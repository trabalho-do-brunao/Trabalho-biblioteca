"""Processamento das respostas recebidas pelo WhatsApp para renovação."""

from __future__ import annotations

import os
import re
from datetime import date

from app.automation.enviar_mensagens import processar_mensagens_pendentes
from app.repositories.mensagens_renovacao import (
    buscar_mensagem_por_identificador_externo,
    criar_mensagem_resposta,
    registrar_mensagem_recebida,
)
from app.repositories.renovacoes import (
    buscar_emprestimo_por_mensagem_externa,
    listar_emprestimos_nao_devolvidos_usuario,
    solicitar_renovacao,
)
from app.repositories.usuarios import buscar_usuario_por_telefone
from app.services.whatsapp import ProvedorWhatsApp, obter_provedor_whatsapp


def _eh_comando_renovar(texto: str) -> bool:
    normalizado = re.sub(r"[^A-Z0-9À-Ú ]+", " ", str(texto or "").upper())
    normalizado = " ".join(normalizado.split())
    return normalizado in {"RENOVAR", "RENOVAR EMPRESTIMO", "RENOVAR EMPRÉSTIMO"}


def _dias_renovacao() -> int:
    bruto = (os.getenv("RENOVACAO_DIAS") or "7").strip()
    try:
        dias = int(bruto)
    except ValueError as erro:
        raise ValueError("RENOVACAO_DIAS deve ser um número inteiro.") from erro

    if dias <= 0 or dias > 90:
        raise ValueError("RENOVACAO_DIAS deve estar entre 1 e 90.")
    return dias


def _enviar_resposta_registrada(
    usuario_id: int,
    texto: str,
    tipo: str,
    emprestimo_id: int | None,
    provedor: ProvedorWhatsApp,
) -> dict[str, object]:
    mensagem = criar_mensagem_resposta(
        usuario_id=usuario_id,
        mensagem=texto,
        tipo=tipo,
        emprestimo_id=emprestimo_id,
    )
    resultados = processar_mensagens_pendentes(
        provedor=provedor,
        mensagem_ids=[int(mensagem["id"])],
    )
    envio = resultados[0] if resultados else {"status": "nao_processado"}
    return {
        "mensagem_saida_id": mensagem["id"],
        "envio": envio,
    }


def processar_resposta_whatsapp(
    telefone: str,
    texto: str,
    identificador_externo: str,
    mensagem_citada_id: str | None = None,
    provedor: ProvedorWhatsApp | None = None,
    data_referencia: date | None = None,
) -> dict[str, object]:
    """Interpreta uma mensagem recebida e executa a renovação quando aplicável."""
    cliente = provedor or obter_provedor_whatsapp()
    conteudo = str(texto or "").strip()
    externo = str(identificador_externo or "").strip()
    citado = str(mensagem_citada_id or "").strip() or None

    if not conteudo:
        raise ValueError("A mensagem recebida não pode ficar vazia.")
    if not externo:
        raise ValueError("A mensagem recebida precisa de um identificador externo.")

    ja_registrada = buscar_mensagem_por_identificador_externo(externo)
    if ja_registrada:
        return {
            "status": "duplicada",
            "mensagem_recebida_id": ja_registrada["id"],
            "processada": False,
        }

    try:
        usuario = buscar_usuario_por_telefone(telefone)
    except ValueError:
        usuario = None

    if not usuario or not usuario.get("ativo"):
        resposta = (
            "Não encontrei um usuário ativo cadastrado com este número. "
            "Procure a biblioteca para atualizar seu cadastro."
        )
        try:
            envio = cliente.enviar(telefone, resposta)
            status_envio = "enviado"
            identificador_resposta = envio.identificador_externo
        except Exception as erro:
            status_envio = "falha"
            identificador_resposta = None
            return {
                "status": "usuario_nao_encontrado",
                "processada": True,
                "resposta": resposta,
                "envio_status": status_envio,
                "erro_envio": str(erro),
            }

        return {
            "status": "usuario_nao_encontrado",
            "processada": True,
            "resposta": resposta,
            "envio_status": status_envio,
            "identificador_resposta": identificador_resposta,
        }

    usuario_id = int(usuario["id"])
    comando_renovar = _eh_comando_renovar(conteudo)

    if not comando_renovar:
        recebida, nova = registrar_mensagem_recebida(
            usuario_id=usuario_id,
            mensagem=conteudo,
            identificador_externo=externo,
            tipo="outro",
        )
        if not nova:
            return {
                "status": "duplicada",
                "mensagem_recebida_id": recebida["id"],
                "processada": False,
            }

        resposta = (
            "Comando não reconhecido. Para solicitar uma renovação, "
            "responda RENOVAR ao aviso do empréstimo."
        )
        saida = _enviar_resposta_registrada(
            usuario_id,
            resposta,
            "outro",
            None,
            cliente,
        )
        return {
            "status": "comando_invalido",
            "processada": True,
            "mensagem_recebida_id": recebida["id"],
            "resposta": resposta,
            **saida,
        }

    emprestimo: dict[str, object] | None = None
    motivo_sem_emprestimo: str | None = None

    if citado:
        emprestimo = buscar_emprestimo_por_mensagem_externa(usuario_id, citado)
        if not emprestimo:
            motivo_sem_emprestimo = (
                "Não consegui identificar o empréstimo deste aviso. "
                "Responda RENOVAR diretamente a uma mensagem de vencimento enviada pelo BiblioAvisa."
            )
    else:
        candidatos = listar_emprestimos_nao_devolvidos_usuario(usuario_id)
        if len(candidatos) == 1:
            emprestimo = candidatos[0]
        elif not candidatos:
            motivo_sem_emprestimo = "Você não possui empréstimos em aberto para renovar."
        else:
            motivo_sem_emprestimo = (
                "Você possui mais de um empréstimo em aberto. "
                "Responda RENOVAR diretamente ao aviso do livro que deseja renovar."
            )

    recebida, nova = registrar_mensagem_recebida(
        usuario_id=usuario_id,
        mensagem=conteudo,
        identificador_externo=externo,
        emprestimo_id=int(emprestimo["id"]) if emprestimo else None,
        tipo="solicitacao_renovacao",
    )
    if not nova:
        return {
            "status": "duplicada",
            "mensagem_recebida_id": recebida["id"],
            "processada": False,
        }

    if not emprestimo:
        resposta = motivo_sem_emprestimo or "Não foi possível identificar o empréstimo para renovação."
        saida = _enviar_resposta_registrada(
            usuario_id,
            resposta,
            "recusa_renovacao",
            None,
            cliente,
        )
        return {
            "status": "recusada",
            "processada": True,
            "mensagem_recebida_id": recebida["id"],
            "renovacao_id": None,
            "resposta": resposta,
            **saida,
        }

    renovacao = solicitar_renovacao(
        emprestimo_id=int(emprestimo["id"]),
        dias=_dias_renovacao(),
        data_referencia=data_referencia,
        origem="whatsapp",
    )

    if renovacao["status"] == "aprovada":
        nova_data = renovacao["nova_data"]
        resposta = (
            f"Renovação aprovada para '{renovacao['livro_titulo']}'. "
            f"Novo prazo de devolução: {nova_data.strftime('%d/%m/%Y')}."
        )
        tipo_resposta = "confirmacao_renovacao"
    else:
        resposta = (
            f"Não foi possível renovar '{renovacao['livro_titulo']}'. "
            f"{renovacao['motivo_recusa']}"
        )
        tipo_resposta = "recusa_renovacao"

    saida = _enviar_resposta_registrada(
        usuario_id,
        resposta,
        tipo_resposta,
        int(emprestimo["id"]),
        cliente,
    )

    return {
        "status": renovacao["status"],
        "processada": True,
        "mensagem_recebida_id": recebida["id"],
        "renovacao_id": renovacao["renovacao_id"],
        "emprestimo_id": renovacao["emprestimo_id"],
        "data_anterior": renovacao["data_anterior"],
        "nova_data": renovacao["nova_data"],
        "motivo_recusa": renovacao["motivo_recusa"],
        "resposta": resposta,
        **saida,
    }
