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
    """Interpreta somente mensagens relacionadas ao fluxo de renovação.

    Conversas comuns e números não cadastrados são ignorados silenciosamente.
    Uma mensagem inválida só recebe orientação quando foi enviada como resposta a
    um aviso do próprio BiblioAvisa.
    """
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

    # Segurança: o BiblioAvisa não responde contatos desconhecidos da conta vinculada.
    if not usuario or not usuario.get("ativo"):
        return {
            "status": "ignorada_usuario_nao_cadastrado",
            "processada": False,
        }

    usuario_id = int(usuario["id"])
    comando_renovar = _eh_comando_renovar(conteudo)

    # Conversa comum não deve virar conversa automática do bot.
    # Só orientamos comando inválido se o usuário respondeu a um aviso do BiblioAvisa.
    if not comando_renovar:
        emprestimo_contexto = (
            buscar_emprestimo_por_mensagem_externa(usuario_id, citado)
            if citado
            else None
        )
        if not emprestimo_contexto:
            return {
                "status": "ignorada_fora_do_fluxo",
                "processada": False,
            }

        cliente = provedor or obter_provedor_whatsapp()
        recebida, nova = registrar_mensagem_recebida(
            usuario_id=usuario_id,
            mensagem=conteudo,
            identificador_externo=externo,
            emprestimo_id=int(emprestimo_contexto["id"]),
            tipo="outro",
        )
        if not nova:
            return {
                "status": "duplicada",
                "mensagem_recebida_id": recebida["id"],
                "processada": False,
            }

        resposta = (
            "Comando não reconhecido. Para solicitar a renovação deste empréstimo, "
            "responda RENOVAR a este aviso."
        )
        saida = _enviar_resposta_registrada(
            usuario_id,
            resposta,
            "outro",
            int(emprestimo_contexto["id"]),
            cliente,
        )
        return {
            "status": "comando_invalido",
            "processada": True,
            "mensagem_recebida_id": recebida["id"],
            "resposta": resposta,
            **saida,
        }

    cliente = provedor or obter_provedor_whatsapp()
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
