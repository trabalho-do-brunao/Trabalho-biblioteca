"""Persistência de eventos de auditoria de operações administrativas.

A criação da tabela é uma migração separada; não registra dados pessoais
ou conteúdo de mensagens nos detalhes.
"""
from __future__ import annotations
from app.db import conectar

ACOES_PERMITIDAS = frozenset({
    "usuario.criado", "usuario.atualizado", "usuario.status_alterado",
    "livro.criado", "livro.atualizado", "emprestimo.criado",
    "emprestimo.devolvido", "renovacao.aprovada", "renovacao.recusada",
    "configuracao.alterada",
})

def registrar_evento(
    *, acao: str, entidade: str, entidade_id: int,
    ator_id: int | None = None,
) -> int:
    """Grava evento simples em transação própria.

    Usar somente após a operação principal ter sido confirmada.
    Para auditoria transacional completa, integrar com a mesma conexão.
    """
    if acao not in ACOES_PERMITIDAS:
        raise ValueError("Ação de auditoria não permitida.")
    if not entidade or len(entidade) > 60:
        raise ValueError("Entidade inválida.")
    if int(entidade_id) <= 0:
        raise ValueError("Identificador da entidade inválido.")
    if ator_id is not None and int(ator_id) <= 0:
        raise ValueError("Identificador do ator inválido.")
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """INSERT INTO auditoria_eventos (acao, entidade, entidade_id, ator_id)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (acao, entidade, int(entidade_id), int(ator_id) if ator_id else None),
            )
            identificador = cursor.fetchone()[0]
        conexao.commit()
        return int(identificador)
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def registrar_evento_na_transacao(
    cursor,
    *,
    acao: str,
    entidade: str,
    entidade_id: int,
    ator_id: int | None = None,
) -> int:
    """Insere evento usando o cursor da operação principal.

    O chamador controla commit e rollback. Não usar sem a migração
    auditoria_eventos aplicada ao banco de destino.
    """
    if acao not in ACOES_PERMITIDAS:
        raise ValueError("Ação de auditoria não permitida.")
    if not isinstance(entidade, str) or not entidade.strip() or len(entidade) > 60:
        raise ValueError("Entidade inválida.")
    if not isinstance(entidade_id, int) or isinstance(entidade_id, bool) or entidade_id <= 0:
        raise ValueError("Identificador da entidade inválido.")
    if ator_id is not None and (
        not isinstance(ator_id, int) or isinstance(ator_id, bool) or ator_id <= 0
    ):
        raise ValueError("Identificador do ator inválido.")
    cursor.execute(
        """INSERT INTO auditoria_eventos (acao, entidade, entidade_id, ator_id)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (acao, entidade.strip(), entidade_id, ator_id),
    )
    return int(cursor.fetchone()[0])
