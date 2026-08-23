"""Regras de persistência para renovação de empréstimos."""

from __future__ import annotations

from datetime import date, timedelta

from psycopg2.extras import RealDictCursor

from app.db import conectar


class EmprestimoRenovacaoNaoEncontradoError(ValueError):
    """Indica que o empréstimo informado não existe."""


def _validar_id(valor: int, nome: str) -> int:
    try:
        identificador = int(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError(f"{nome} deve ser um número inteiro.") from erro

    if identificador <= 0:
        raise ValueError(f"{nome} deve ser maior que zero.")
    return identificador


def listar_emprestimos_nao_devolvidos_usuario(usuario_id: int) -> list[dict[str, object]]:
    """Lista empréstimos ainda não devolvidos, inclusive os atrasados."""
    identificador = _validar_id(usuario_id, "usuario_id")
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.usuario_id = %s
                  AND e.data_devolucao IS NULL
                  AND e.status IN ('ativo', 'atrasado')
                ORDER BY e.data_prevista_devolucao, e.id;
                """,
                (identificador,),
            )
            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()


def buscar_emprestimo_por_mensagem_externa(
    usuario_id: int,
    identificador_externo: str,
) -> dict[str, object] | None:
    """Descobre o empréstimo associado ao aviso respondido pelo usuário."""
    identificador_usuario = _validar_id(usuario_id, "usuario_id")
    externo = str(identificador_externo or "").strip()
    if not externo:
        return None

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status
                FROM mensagens m
                INNER JOIN emprestimos e ON e.id = m.emprestimo_id
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE m.usuario_id = %s
                  AND m.identificador_externo = %s
                  AND m.direcao = 'enviada'
                  AND m.emprestimo_id IS NOT NULL
                LIMIT 1;
                """,
                (identificador_usuario, externo),
            )
            linha = cursor.fetchone()
            return dict(linha) if linha else None
    finally:
        conexao.close()


def solicitar_renovacao(
    emprestimo_id: int,
    dias: int = 7,
    data_referencia: date | None = None,
    origem: str = "whatsapp",
) -> dict[str, object]:
    """Aprova ou recusa uma renovação e registra o resultado no histórico."""
    identificador = _validar_id(emprestimo_id, "emprestimo_id")

    try:
        quantidade_dias = int(dias)
    except (TypeError, ValueError) as erro:
        raise ValueError("A quantidade de dias da renovação deve ser inteira.") from erro

    if quantidade_dias <= 0 or quantidade_dias > 90:
        raise ValueError("A renovação deve acrescentar entre 1 e 90 dias.")

    referencia = data_referencia or date.today()
    if not isinstance(referencia, date):
        raise ValueError("data_referencia deve ser uma data válida.")

    origem_normalizada = str(origem or "").strip().lower()
    if origem_normalizada not in {"whatsapp", "sistema", "manual"}:
        raise ValueError("Origem de renovação inválida.")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.id = %s
                FOR UPDATE OF e;
                """,
                (identificador,),
            )
            emprestimo = cursor.fetchone()

            if not emprestimo:
                raise EmprestimoRenovacaoNaoEncontradoError(
                    f"O empréstimo {identificador} não foi encontrado."
                )

            data_anterior = emprestimo["data_prevista_devolucao"]
            motivo_recusa: str | None = None

            if emprestimo["data_devolucao"] is not None or emprestimo["status"] == "devolvido":
                motivo_recusa = "Este empréstimo já foi devolvido e não pode ser renovado."
            elif emprestimo["status"] == "atrasado" or data_anterior < referencia:
                motivo_recusa = "Este empréstimo está atrasado e não pode ser renovado pelo WhatsApp."
            elif emprestimo["status"] != "ativo":
                motivo_recusa = "Este empréstimo não está disponível para renovação."

            if motivo_recusa:
                cursor.execute(
                    """
                    INSERT INTO renovacoes (
                        emprestimo_id,
                        data_anterior,
                        nova_data,
                        status,
                        origem,
                        motivo_recusa
                    )
                    VALUES (%s, %s, NULL, 'recusada', %s, %s)
                    RETURNING id, data_solicitacao, criado_em;
                    """,
                    (identificador, data_anterior, origem_normalizada, motivo_recusa),
                )
                renovacao = cursor.fetchone()
                conexao.commit()
                return {
                    "renovacao_id": renovacao["id"],
                    "emprestimo_id": identificador,
                    "usuario_id": emprestimo["usuario_id"],
                    "livro_id": emprestimo["livro_id"],
                    "livro_titulo": emprestimo["livro_titulo"],
                    "status": "recusada",
                    "data_anterior": data_anterior,
                    "nova_data": None,
                    "motivo_recusa": motivo_recusa,
                }

            nova_data = data_anterior + timedelta(days=quantidade_dias)

            cursor.execute(
                """
                UPDATE emprestimos
                SET
                    data_prevista_devolucao = %s,
                    atualizado_em = NOW()
                WHERE id = %s;
                """,
                (nova_data, identificador),
            )

            -- Reminders that have not been sent yet refer to the old due date.
            cursor.execute(
                """
                DELETE FROM mensagens
                WHERE emprestimo_id = %s
                  AND direcao = 'enviada'
                  AND status = 'pendente'
                  AND tipo IN ('aviso_2_dias', 'aviso_vencimento', 'aviso_atraso');
                """,
                (identificador,),
            )

            cursor.execute(
                """
                INSERT INTO renovacoes (
                    emprestimo_id,
                    data_anterior,
                    nova_data,
                    status,
                    origem,
                    motivo_recusa
                )
                VALUES (%s, %s, %s, 'aprovada', %s, NULL)
                RETURNING id, data_solicitacao, criado_em;
                """,
                (identificador, data_anterior, nova_data, origem_normalizada),
            )
            renovacao = cursor.fetchone()

        conexao.commit()
        return {
            "renovacao_id": renovacao["id"],
            "emprestimo_id": identificador,
            "usuario_id": emprestimo["usuario_id"],
            "livro_id": emprestimo["livro_id"],
            "livro_titulo": emprestimo["livro_titulo"],
            "status": "aprovada",
            "data_anterior": data_anterior,
            "nova_data": nova_data,
            "motivo_recusa": None,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
