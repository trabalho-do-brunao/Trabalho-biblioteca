"""Consultas consolidadas para os indicadores do dashboard."""

from __future__ import annotations

from datetime import date

from psycopg2.extras import RealDictCursor

from app.db import conectar


def obter_dashboard(dias_proximos: int = 2, limite: int = 10) -> dict[str, object]:
    """Retorna indicadores e empréstimos que exigem atenção.

    A situação é derivada das datas atuais para que o dashboard continue correto
    mesmo antes da rotina diária persistir o status ``atrasado`` no empréstimo.
    """
    try:
        dias = int(dias_proximos)
        max_itens = int(limite)
    except (TypeError, ValueError) as erro:
        raise ValueError("Os parâmetros do dashboard devem ser números inteiros.") from erro

    if dias < 0 or dias > 30:
        raise ValueError("dias_proximos deve estar entre 0 e 30.")
    if max_itens <= 0 or max_itens > 100:
        raise ValueError("limite deve estar entre 1 e 100.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*)
                       FROM usuarios
                      WHERE ativo = TRUE) AS usuarios_ativos,
                    (SELECT COUNT(*)
                       FROM livros) AS titulos_cadastrados,
                    (SELECT COALESCE(SUM(quantidade_disponivel), 0)
                       FROM livros) AS exemplares_disponiveis,
                    (SELECT COUNT(*)
                       FROM emprestimos
                      WHERE data_devolucao IS NULL
                        AND status IN ('ativo', 'atrasado')) AS emprestimos_abertos,
                    (SELECT COUNT(*)
                       FROM emprestimos
                      WHERE data_devolucao IS NULL
                        AND status IN ('ativo', 'atrasado')
                        AND data_prevista_devolucao < CURRENT_DATE) AS emprestimos_atrasados,
                    (SELECT COUNT(*)
                       FROM emprestimos
                      WHERE data_devolucao IS NULL
                        AND status IN ('ativo', 'atrasado')
                        AND data_prevista_devolucao BETWEEN CURRENT_DATE AND CURRENT_DATE + %s) AS proximos_vencimento;
                """,
                (dias,),
            )
            resumo = dict(cursor.fetchone())

            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    u.nome AS usuario_nome,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    l.isbn AS livro_isbn,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    CASE
                        WHEN e.data_prevista_devolucao < CURRENT_DATE THEN 'atrasado'
                        WHEN e.data_prevista_devolucao = CURRENT_DATE THEN 'vence_hoje'
                        ELSE 'proximo'
                    END AS situacao,
                    CASE
                        WHEN e.data_prevista_devolucao < CURRENT_DATE
                            THEN CURRENT_DATE - e.data_prevista_devolucao
                        ELSE e.data_prevista_devolucao - CURRENT_DATE
                    END AS dias
                FROM emprestimos e
                INNER JOIN usuarios u ON u.id = e.usuario_id
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.data_devolucao IS NULL
                  AND e.status IN ('ativo', 'atrasado')
                  AND e.data_prevista_devolucao <= CURRENT_DATE + %s
                ORDER BY
                    CASE WHEN e.data_prevista_devolucao < CURRENT_DATE THEN 0 ELSE 1 END,
                    e.data_prevista_devolucao,
                    e.id
                LIMIT %s;
                """,
                (dias, max_itens),
            )
            atencao = [dict(linha) for linha in cursor.fetchall()]

        return {
            "resumo": resumo,
            "atencao": atencao,
            "dias_proximos": dias,
            "data_referencia": date.today().isoformat(),
        }
    finally:
        conexao.close()
