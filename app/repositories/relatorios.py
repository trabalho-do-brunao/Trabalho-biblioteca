"""Consultas somente-leitura usadas pelos relatórios do BiblioAvisa."""

from __future__ import annotations

from datetime import date, timedelta

from psycopg2.extras import RealDictCursor

from app.db import conectar


DIAS_PROXIMO_VENCIMENTO = 7


def _validar_periodo(data_inicio: date, data_fim: date) -> None:
    if not isinstance(data_inicio, date) or not isinstance(data_fim, date):
        raise ValueError("data_inicio e data_fim devem ser datas válidas.")
    if data_inicio > data_fim:
        raise ValueError("data_inicio não pode ser posterior a data_fim.")


def buscar_dados_relatorio(
    data_inicio: date,
    data_fim: date,
    dias_proximo_vencimento: int = DIAS_PROXIMO_VENCIMENTO,
) -> dict[str, object]:
    """Reúne mensagens e empréstimos para o relatório sem alterar o banco."""
    _validar_periodo(data_inicio, data_fim)
    if dias_proximo_vencimento < 0 or dias_proximo_vencimento > 90:
        raise ValueError("dias_proximo_vencimento deve estar entre 0 e 90.")

    limite_proximos = data_fim + timedelta(days=dias_proximo_vencimento)
    conexao = conectar()

    try:
        # Defesa adicional: esta conexão não pode executar comandos de escrita.
        conexao.set_session(readonly=True, autocommit=True)
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    m.id,
                    m.data_mensagem,
                    m.tipo,
                    m.status,
                    m.mensagem,
                    u.nome AS usuario_nome,
                    l.titulo AS livro_titulo,
                    e.id AS emprestimo_id
                FROM mensagens m
                JOIN usuarios u ON u.id = m.usuario_id
                LEFT JOIN emprestimos e ON e.id = m.emprestimo_id
                LEFT JOIN livros l ON l.id = e.livro_id
                WHERE m.direcao = 'enviada'
                  AND m.data_mensagem::date BETWEEN %s AND %s
                ORDER BY m.data_mensagem, m.id;
                """,
                (data_inicio, data_fim),
            )
            mensagens = [dict(item) for item in cursor.fetchall()]

            cursor.execute(
                """
                SELECT
                    e.id,
                    e.status,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    u.nome AS usuario_nome,
                    l.titulo AS livro_titulo
                FROM emprestimos e
                JOIN usuarios u ON u.id = e.usuario_id
                JOIN livros l ON l.id = e.livro_id
                WHERE e.data_devolucao IS NULL
                  AND e.status IN ('ativo', 'atrasado')
                  AND e.data_prevista_devolucao < %s
                ORDER BY e.data_prevista_devolucao, e.id;
                """,
                (data_fim,),
            )
            atrasados = [dict(item) for item in cursor.fetchall()]

            cursor.execute(
                """
                SELECT
                    e.id,
                    e.status,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    u.nome AS usuario_nome,
                    l.titulo AS livro_titulo
                FROM emprestimos e
                JOIN usuarios u ON u.id = e.usuario_id
                JOIN livros l ON l.id = e.livro_id
                WHERE e.data_devolucao IS NULL
                  AND e.status = 'ativo'
                  AND e.data_prevista_devolucao BETWEEN %s AND %s
                ORDER BY e.data_prevista_devolucao, e.id;
                """,
                (data_fim, limite_proximos),
            )
            proximos = [dict(item) for item in cursor.fetchall()]

        return {
            "periodo_inicio": data_inicio,
            "periodo_fim": data_fim,
            "dias_proximo_vencimento": dias_proximo_vencimento,
            "mensagens": mensagens,
            "emprestimos_atrasados": atrasados,
            "emprestimos_proximos": proximos,
        }
    finally:
        conexao.close()
