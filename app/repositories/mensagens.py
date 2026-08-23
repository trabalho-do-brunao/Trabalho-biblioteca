"""Consultas e atualizações relacionadas às mensagens do BiblioAvisa."""

from __future__ import annotations

from collections.abc import Iterable

from psycopg2.extras import RealDictCursor

from app.db import conectar


class MensagemNaoEncontradaError(ValueError):
    """Indica que a mensagem não existe ou não está mais pendente."""


def _normalizar_ids(ids: Iterable[int] | None) -> list[int] | None:
    if ids is None:
        return None

    resultado: list[int] = []
    for valor in ids:
        try:
            identificador = int(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError("Os IDs das mensagens devem ser números inteiros.") from erro
        if identificador <= 0:
            raise ValueError("Os IDs das mensagens devem ser maiores que zero.")
        resultado.append(identificador)

    return resultado


def buscar_mensagens_pendentes(
    limite: int = 100,
    mensagem_ids: Iterable[int] | None = None,
) -> list[dict[str, object]]:
    """Retorna avisos pendentes junto ao telefone do usuário destinatário."""
    try:
        limite_normalizado = int(limite)
    except (TypeError, ValueError) as erro:
        raise ValueError("O limite deve ser um número inteiro.") from erro

    if limite_normalizado <= 0:
        raise ValueError("O limite deve ser maior que zero.")

    ids = _normalizar_ids(mensagem_ids)
    filtro_ids = ""
    parametros: list[object] = []

    if ids is not None:
        if not ids:
            return []
        filtro_ids = "AND m.id = ANY(%s)"
        parametros.append(ids)

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
                    u.telefone AS usuario_telefone,
                    m.emprestimo_id,
                    m.tipo,
                    m.mensagem,
                    m.status,
                    m.data_referencia,
                    m.data_mensagem
                FROM mensagens m
                INNER JOIN usuarios u ON u.id = m.usuario_id
                WHERE m.direcao = 'enviada'
                  AND m.status = 'pendente'
                  {filtro_ids}
                ORDER BY m.data_mensagem, m.id
                LIMIT %s;
                """,
                tuple(parametros),
            )
            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()


def marcar_mensagem_enviada(
    mensagem_id: int,
    identificador_externo: str | None = None,
) -> dict[str, object]:
    """Marca uma mensagem pendente como enviada e guarda o ID do provedor."""
    identificador = int(mensagem_id)
    externo = identificador_externo.strip() if identificador_externo else None

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE mensagens
                SET
                    status = 'enviado',
                    identificador_externo = %s,
                    data_mensagem = NOW()
                WHERE id = %s
                  AND status = 'pendente'
                RETURNING id, status, identificador_externo, data_mensagem;
                """,
                (externo, identificador),
            )
            resultado = cursor.fetchone()

            if not resultado:
                raise MensagemNaoEncontradaError(
                    f"A mensagem {identificador} não existe ou não está pendente."
                )

        conexao.commit()
        return dict(resultado)
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def marcar_mensagem_falha(mensagem_id: int) -> dict[str, object]:
    """Marca uma tentativa de envio pendente como falha."""
    identificador = int(mensagem_id)

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE mensagens
                SET
                    status = 'falha',
                    identificador_externo = NULL,
                    data_mensagem = NOW()
                WHERE id = %s
                  AND status = 'pendente'
                RETURNING id, status, data_mensagem;
                """,
                (identificador,),
            )
            resultado = cursor.fetchone()

            if not resultado:
                raise MensagemNaoEncontradaError(
                    f"A mensagem {identificador} não existe ou não está pendente."
                )

        conexao.commit()
        return dict(resultado)
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
