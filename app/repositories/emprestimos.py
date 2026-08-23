"""Consultas relacionadas aos empréstimos da biblioteca."""

from __future__ import annotations

from psycopg2.extras import RealDictCursor

from app.db import conectar


def buscar_emprestimos_ativos() -> list[dict[str, object]]:
    """Retorna os empréstimos ativos com dados do usuário e do livro."""
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
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN usuarios u
                    ON u.id = e.usuario_id
                INNER JOIN livros l
                    ON l.id = e.livro_id
                WHERE e.status = 'ativo'
                ORDER BY e.data_prevista_devolucao, e.id;
                """
            )

            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()
