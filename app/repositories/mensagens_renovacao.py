"""Persistência das mensagens recebidas e respostas da renovação."""

from __future__ import annotations

from psycopg2.extras import RealDictCursor

from app.db import conectar


TIPOS_RESPOSTA = {"confirmacao_renovacao", "recusa_renovacao", "outro"}


def buscar_mensagem_por_identificador_externo(
    identificador_externo: str,
) -> dict[str, object] | None:
    """Busca uma mensagem já registrada pelo identificador recebido do provedor."""
    externo = str(identificador_externo or "").strip()
    if not externo:
        return None

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    identificador_externo,
                    data_referencia,
                    data_mensagem
                FROM mensagens
                WHERE identificador_externo = %s
                LIMIT 1;
                """,
                (externo,),
            )
            linha = cursor.fetchone()
            return dict(linha) if linha else None
    finally:
        conexao.close()


def registrar_mensagem_recebida(
    usuario_id: int,
    mensagem: str,
    identificador_externo: str,
    emprestimo_id: int | None = None,
    tipo: str = "solicitacao_renovacao",
) -> tuple[dict[str, object], bool]:
    """Registra uma mensagem recebida e informa se ela era nova.

    O índice único de `identificador_externo` torna o webhook idempotente:
    uma reentrega do mesmo evento não cria uma segunda solicitação.
    """
    texto = str(mensagem or "").strip()
    externo = str(identificador_externo or "").strip()
    tipo_normalizado = str(tipo or "").strip().lower()

    if not texto:
        raise ValueError("A mensagem recebida não pode ficar vazia.")
    if not externo:
        raise ValueError("A mensagem recebida precisa de um identificador externo.")
    if tipo_normalizado not in {"solicitacao_renovacao", "outro", "consulta"}:
        raise ValueError("Tipo inválido para mensagem recebida.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO mensagens (
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    identificador_externo,
                    data_referencia
                )
                VALUES (%s, %s, 'recebida', %s, %s, 'recebido', %s, CURRENT_DATE)
                ON CONFLICT DO NOTHING
                RETURNING
                    id,
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    identificador_externo,
                    data_referencia,
                    data_mensagem;
                """,
                (
                    int(usuario_id),
                    int(emprestimo_id) if emprestimo_id is not None else None,
                    tipo_normalizado,
                    texto,
                    externo,
                ),
            )
            linha = cursor.fetchone()

            if linha:
                conexao.commit()
                return dict(linha), True

            cursor.execute(
                """
                SELECT
                    id,
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    identificador_externo,
                    data_referencia,
                    data_mensagem
                FROM mensagens
                WHERE identificador_externo = %s
                LIMIT 1;
                """,
                (externo,),
            )
            existente = cursor.fetchone()
            conexao.commit()

            if not existente:
                raise RuntimeError("Não foi possível registrar nem localizar a mensagem recebida.")
            return dict(existente), False
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_mensagem_resposta(
    usuario_id: int,
    mensagem: str,
    tipo: str,
    emprestimo_id: int | None = None,
) -> dict[str, object]:
    """Cria uma resposta pendente para envio pela fila da Backlog #8."""
    texto = str(mensagem or "").strip()
    tipo_normalizado = str(tipo or "").strip().lower()

    if not texto:
        raise ValueError("A resposta não pode ficar vazia.")
    if tipo_normalizado not in TIPOS_RESPOSTA:
        raise ValueError("Tipo de resposta de renovação inválido.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO mensagens (
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    data_referencia
                )
                VALUES (%s, %s, 'enviada', %s, %s, 'pendente', CURRENT_DATE)
                RETURNING
                    id,
                    usuario_id,
                    emprestimo_id,
                    direcao,
                    tipo,
                    mensagem,
                    status,
                    data_referencia,
                    data_mensagem;
                """,
                (
                    int(usuario_id),
                    int(emprestimo_id) if emprestimo_id is not None else None,
                    tipo_normalizado,
                    texto,
                ),
            )
            linha = cursor.fetchone()
        conexao.commit()
        return dict(linha)
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
