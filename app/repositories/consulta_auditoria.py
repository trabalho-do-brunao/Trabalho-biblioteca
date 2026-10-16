"""Consulta paginada e somente leitura dos eventos de auditoria."""
from __future__ import annotations

from psycopg2.extras import RealDictCursor
from app.db import conectar


def listar_eventos(
    *, limite: int = 50, deslocamento: int = 0,
    acao: str | None = None, entidade: str | None = None,
    entidade_id: int | None = None,
) -> dict[str, object]:
    """Filtra por campos exatos; sem dados pessoais ou conteúdo de mensagens."""
    if not isinstance(limite, int) or isinstance(limite, bool) or not 1 <= limite <= 100:
        raise ValueError("Limite deve estar entre 1 e 100.")
    if not isinstance(deslocamento, int) or isinstance(deslocamento, bool) or deslocamento < 0:
        raise ValueError("Deslocamento inválido.")
    if entidade_id is not None and (not isinstance(entidade_id, int) or isinstance(entidade_id, bool) or entidade_id <= 0):
        raise ValueError("Identificador inválido.")

    condicoes = []
    parametros: list[object] = []
    if acao is not None:
        condicoes.append("acao = %s")
        parametros.append(acao)
    if entidade is not None:
        condicoes.append("entidade = %s")
        parametros.append(entidade)
    if entidade_id is not None:
        condicoes.append("entidade_id = %s")
        parametros.append(entidade_id)
    filtro = " WHERE " + " AND ".join(condicoes) if condicoes else ""

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM auditoria_eventos" + filtro, tuple(parametros))
            total = int(cursor.fetchone()["total"])
            cursor.execute(
                """SELECT id, acao, entidade, entidade_id, ator_id, criado_em
                   FROM auditoria_eventos""" + filtro +
                " ORDER BY criado_em DESC, id DESC LIMIT %s OFFSET %s",
                tuple([*parametros, limite, deslocamento]),
            )
            eventos = [dict(registro) for registro in cursor.fetchall()]
        return {"eventos": eventos, "total": total, "limite": limite, "deslocamento": deslocamento}
    finally:
        conexao.close()
