"""Consultas de acompanhamento das mensagens e renovações do WhatsApp."""

from __future__ import annotations

from datetime import date

from psycopg2.extras import RealDictCursor

from app.db import conectar


def listar_historico_whatsapp(
    *,
    status: str | None = None,
    tipo: str | None = None,
    direcao: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    busca: str = "",
    limite: int = 250,
) -> list[dict[str, object]]:
    """Lista mensagens operacionais sem expor IDs externos ou dados de sessão."""
    try:
        limite_normalizado = int(limite)
    except (TypeError, ValueError) as erro:
        raise ValueError("O limite deve ser um número inteiro.") from erro

    if limite_normalizado <= 0 or limite_normalizado > 500:
        raise ValueError("O limite deve estar entre 1 e 500.")

    filtros: list[str] = []
    parametros: list[object] = []

    if status:
        filtros.append("m.status = %s")
        parametros.append(status)
    if tipo:
        filtros.append("m.tipo = %s")
        parametros.append(tipo)
    if direcao:
        filtros.append("m.direcao = %s")
        parametros.append(direcao)
    if data_inicio:
        filtros.append("m.data_mensagem::date >= %s")
        parametros.append(data_inicio)
    if data_fim:
        filtros.append("m.data_mensagem::date <= %s")
        parametros.append(data_fim)

    termo = str(busca or "").strip()
    if termo:
        filtros.append(
            "(" 
            "u.nome ILIKE %s OR "
            "m.mensagem ILIKE %s OR "
            "COALESCE(l.titulo, '') ILIKE %s OR "
            "CAST(m.id AS TEXT) = %s OR "
            "CAST(COALESCE(m.emprestimo_id, 0) AS TEXT) = %s"
            ")"
        )
        like = f"%{termo}%"
        parametros.extend([like, like, like, termo, termo])

    clausula_where = "WHERE " + " AND ".join(filtros) if filtros else ""
    parametros.append(limite_normalizado)

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT
                    m.id,
                    m.usuario_id,
                    u.nome AS usuario_nome,
                    m.emprestimo_id,
                    l.titulo AS livro_titulo,
                    m.direcao,
                    m.tipo,
                    m.mensagem,
                    m.status,
                    m.data_referencia,
                    m.data_mensagem,
                    r.id AS renovacao_id,
                    r.status AS renovacao_status,
                    r.data_anterior AS renovacao_data_anterior,
                    r.nova_data AS renovacao_nova_data,
                    r.motivo_recusa AS renovacao_motivo_recusa,
                    r.data_solicitacao AS renovacao_data_solicitacao
                FROM mensagens m
                INNER JOIN usuarios u ON u.id = m.usuario_id
                LEFT JOIN emprestimos e ON e.id = m.emprestimo_id
                LEFT JOIN livros l ON l.id = e.livro_id
                LEFT JOIN LATERAL (
                    SELECT
                        ren.id,
                        ren.status,
                        ren.data_anterior,
                        ren.nova_data,
                        ren.motivo_recusa,
                        ren.data_solicitacao
                    FROM renovacoes ren
                    WHERE ren.emprestimo_id = m.emprestimo_id
                    ORDER BY ren.data_solicitacao DESC, ren.id DESC
                    LIMIT 1
                ) r ON TRUE
                {clausula_where}
                ORDER BY m.data_mensagem DESC, m.id DESC
                LIMIT %s;
                """,
                tuple(parametros),
            )
            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()


def obter_resumo_whatsapp() -> dict[str, int]:
    """Retorna indicadores simples do histórico de mensagens."""
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*)::int AS total,
                    COUNT(*) FILTER (WHERE direcao = 'enviada')::int AS enviadas,
                    COUNT(*) FILTER (WHERE direcao = 'recebida')::int AS recebidas,
                    COUNT(*) FILTER (WHERE status = 'pendente')::int AS pendentes,
                    COUNT(*) FILTER (WHERE status = 'falha')::int AS falhas
                FROM mensagens;
                """
            )
            return dict(cursor.fetchone())
    finally:
        conexao.close()
