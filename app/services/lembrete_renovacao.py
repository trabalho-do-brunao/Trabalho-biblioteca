"""Envio manual de convite de renovação sem alterar a automação de prazos."""

from __future__ import annotations

from datetime import date

from psycopg2.extras import RealDictCursor

from app.automation.enviar_mensagens import processar_mensagens_pendentes
from app.db import conectar
from app.repositories.mensagens_renovacao import criar_mensagem_resposta
from app.services.whatsapp import ProvedorWhatsApp


class LembreteRenovacaoError(ValueError):
    """Erro de regra de negócio relacionado ao lembrete manual de renovação."""


class EmprestimoLembreteNaoEncontradoError(LembreteRenovacaoError):
    """O empréstimo informado não existe."""


class EmprestimoNaoElegivelLembreteError(LembreteRenovacaoError):
    """O empréstimo não pode receber convite de renovação."""


class EnvioLembreteRenovacaoError(RuntimeError):
    """A mensagem foi registrada, mas o provedor não conseguiu enviá-la."""


def _buscar_emprestimo(emprestimo_id: int) -> dict[str, object]:
    try:
        identificador = int(emprestimo_id)
    except (TypeError, ValueError) as erro:
        raise LembreteRenovacaoError("emprestimo_id deve ser um número inteiro.") from erro

    if identificador <= 0:
        raise LembreteRenovacaoError("emprestimo_id deve ser maior que zero.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    u.nome AS usuario_nome,
                    u.telefone AS usuario_telefone,
                    u.ativo AS usuario_ativo,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN usuarios u ON u.id = e.usuario_id
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.id = %s
                LIMIT 1;
                """,
                (identificador,),
            )
            linha = cursor.fetchone()
    finally:
        conexao.close()

    if not linha:
        raise EmprestimoLembreteNaoEncontradoError("Empréstimo não encontrado.")

    return dict(linha)


def _validar_elegibilidade(emprestimo: dict[str, object]) -> None:
    prazo = emprestimo.get("data_prevista_devolucao")

    if emprestimo.get("data_devolucao") is not None or emprestimo.get("status") == "devolvido":
        raise EmprestimoNaoElegivelLembreteError(
            "Este empréstimo já foi devolvido e não pode receber convite de renovação."
        )

    if not emprestimo.get("usuario_ativo"):
        raise EmprestimoNaoElegivelLembreteError(
            "O usuário está inativo e não pode receber convite de renovação."
        )

    if not isinstance(prazo, date):
        raise LembreteRenovacaoError("O empréstimo possui uma data prevista inválida.")

    if emprestimo.get("status") == "atrasado" or prazo < date.today():
        raise EmprestimoNaoElegivelLembreteError(
            "Empréstimos atrasados não podem ser renovados pelo WhatsApp."
        )


def _montar_texto(emprestimo: dict[str, object]) -> str:
    prazo = emprestimo["data_prevista_devolucao"]
    assert isinstance(prazo, date)

    return (
        f"Olá, {emprestimo['usuario_nome']}! O empréstimo do livro "
        f"\"{emprestimo['livro_titulo']}\" tem devolução prevista para "
        f"{prazo.strftime('%d/%m/%Y')}. Se quiser solicitar a renovação, "
        "responda RENOVAR a esta mensagem."
    )


def enviar_lembrete_renovacao_manual(
    emprestimo_id: int,
    provedor: ProvedorWhatsApp | None = None,
) -> dict[str, object]:
    """Registra e envia um convite manual de renovação.

    A mensagem usa ``tipo='outro'`` para permanecer independente dos avisos
    automáticos de prazo. Esta função não altera ``emprestimos`` nem cria uma
    linha em ``renovacoes``; uma renovação só ocorre se o usuário responder
    RENOVAR e o fluxo normal do webhook aprovar a solicitação.
    """
    emprestimo = _buscar_emprestimo(emprestimo_id)
    _validar_elegibilidade(emprestimo)

    mensagem = criar_mensagem_resposta(
        usuario_id=int(emprestimo["usuario_id"]),
        mensagem=_montar_texto(emprestimo),
        tipo="outro",
        emprestimo_id=int(emprestimo["id"]),
    )

    resultados = processar_mensagens_pendentes(
        provedor=provedor,
        mensagem_ids=[int(mensagem["id"])],
    )
    envio = resultados[0] if resultados else {"status": "nao_processado"}

    if envio.get("status") != "enviado":
        raise EnvioLembreteRenovacaoError(
            "Não foi possível enviar o lembrete pelo WhatsApp. A tentativa foi registrada no histórico."
        )

    return {
        "emprestimo_id": int(emprestimo["id"]),
        "usuario_id": int(emprestimo["usuario_id"]),
        "mensagem_id": int(mensagem["id"]),
        "status": "enviado",
        "provedor": envio.get("provedor"),
        "identificador_externo": envio.get("identificador_externo"),
        "mensagem": "Lembrete de renovação enviado pelo WhatsApp.",
    }
