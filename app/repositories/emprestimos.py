"""Operações de empréstimos, devoluções e consultas da biblioteca."""

from __future__ import annotations

from datetime import date

import psycopg2
from psycopg2.extras import RealDictCursor

from app.db import conectar


class EmprestimoError(ValueError):
    """Erro de regra de negócio relacionado a empréstimos."""


class UsuarioNaoEncontradoError(EmprestimoError):
    """O usuário informado não existe ou não pode realizar empréstimos."""


class LivroNaoEncontradoError(EmprestimoError):
    """O livro informado não existe no acervo."""


class LivroIndisponivelError(EmprestimoError):
    """Não há exemplar disponível para realizar o empréstimo."""


class EmprestimoNaoEncontradoError(EmprestimoError):
    """O empréstimo informado não existe."""


class EmprestimoJaDevolvidoError(EmprestimoError):
    """O empréstimo já foi finalizado por devolução."""


def _validar_id(valor: object, campo: str) -> int:
    try:
        identificador = int(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError(f"{campo} deve ser um número inteiro.") from erro

    if identificador <= 0:
        raise ValueError(f"{campo} deve ser maior que zero.")

    return identificador


def _normalizar_data(valor: date | str | None, campo: str, padrao: date | None = None) -> date:
    if valor is None:
        if padrao is not None:
            return padrao
        raise ValueError(f"{campo} é obrigatória.")

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError as erro:
            raise ValueError(f"{campo} deve estar no formato AAAA-MM-DD.") from erro

    raise ValueError(f"{campo} deve ser uma data ou texto no formato AAAA-MM-DD.")


def registrar_emprestimo(
    usuario_id: int,
    livro_id: int,
    data_prevista_devolucao: date | str,
    data_emprestimo: date | str | None = None,
) -> dict[str, object]:
    """Registra um empréstimo e reduz o estoque disponível na mesma transação.

    O registro do livro é bloqueado com ``FOR UPDATE`` durante a operação. Isso
    impede que duas transações diferentes emprestem simultaneamente o mesmo
    último exemplar disponível.
    """
    usuario = _validar_id(usuario_id, "usuario_id")
    livro = _validar_id(livro_id, "livro_id")
    data_inicio = _normalizar_data(data_emprestimo, "data_emprestimo", date.today())
    data_prevista = _normalizar_data(data_prevista_devolucao, "data_prevista_devolucao")

    if data_prevista < data_inicio:
        raise ValueError("A data prevista de devolução não pode ser anterior ao empréstimo.")

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, ativo
                FROM usuarios
                WHERE id = %s;
                """,
                (usuario,),
            )
            usuario_db = cursor.fetchone()

            if not usuario_db:
                raise UsuarioNaoEncontradoError("Usuário não encontrado.")

            if not usuario_db["ativo"]:
                raise UsuarioNaoEncontradoError(
                    f"O usuário {usuario_db['nome']} está inativo e não pode realizar empréstimos."
                )

            cursor.execute(
                """
                SELECT id, titulo, quantidade_total, quantidade_disponivel
                FROM livros
                WHERE id = %s
                FOR UPDATE;
                """,
                (livro,),
            )
            livro_db = cursor.fetchone()

            if not livro_db:
                raise LivroNaoEncontradoError("Livro não encontrado no acervo.")

            if livro_db["quantidade_disponivel"] <= 0:
                raise LivroIndisponivelError(
                    f"Não há exemplar disponível de '{livro_db['titulo']}'."
                )

            cursor.execute(
                """
                UPDATE livros
                SET quantidade_disponivel = quantidade_disponivel - 1
                WHERE id = %s
                  AND quantidade_disponivel > 0
                RETURNING quantidade_disponivel;
                """,
                (livro,),
            )
            estoque = cursor.fetchone()

            if not estoque:
                raise LivroIndisponivelError(
                    f"Não há exemplar disponível de '{livro_db['titulo']}'."
                )

            cursor.execute(
                """
                INSERT INTO emprestimos (
                    usuario_id,
                    livro_id,
                    data_emprestimo,
                    data_prevista_devolucao,
                    status
                )
                VALUES (%s, %s, %s, %s, 'ativo')
                RETURNING
                    id,
                    usuario_id,
                    livro_id,
                    data_emprestimo,
                    data_prevista_devolucao,
                    data_devolucao,
                    status,
                    criado_em,
                    atualizado_em;
                """,
                (usuario, livro, data_inicio, data_prevista),
            )
            resultado = dict(cursor.fetchone())
            resultado["usuario_nome"] = usuario_db["nome"]
            resultado["livro_titulo"] = livro_db["titulo"]
            resultado["quantidade_disponivel"] = estoque["quantidade_disponivel"]

        conexao.commit()
        return resultado
    except (EmprestimoError, ValueError):
        conexao.rollback()
        raise
    except psycopg2.Error:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def registrar_devolucao(
    emprestimo_id: int,
    data_devolucao: date | str | None = None,
) -> dict[str, object]:
    """Finaliza um empréstimo e devolve um exemplar ao estoque atomicamente."""
    emprestimo = _validar_id(emprestimo_id, "emprestimo_id")
    data_fim = _normalizar_data(data_devolucao, "data_devolucao", date.today())
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    e.id,
                    e.usuario_id,
                    e.livro_id,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status,
                    l.titulo AS livro_titulo
                FROM emprestimos e
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.id = %s
                FOR UPDATE OF e;
                """,
                (emprestimo,),
            )
            emprestimo_db = cursor.fetchone()

            if not emprestimo_db:
                raise EmprestimoNaoEncontradoError("Empréstimo não encontrado.")

            if emprestimo_db["status"] == "devolvido" or emprestimo_db["data_devolucao"] is not None:
                raise EmprestimoJaDevolvidoError("Este empréstimo já foi devolvido.")

            if data_fim < emprestimo_db["data_emprestimo"]:
                raise ValueError("A data de devolução não pode ser anterior ao empréstimo.")

            cursor.execute(
                """
                SELECT id, quantidade_total, quantidade_disponivel
                FROM livros
                WHERE id = %s
                FOR UPDATE;
                """,
                (emprestimo_db["livro_id"],),
            )
            livro_db = cursor.fetchone()

            if not livro_db:
                raise LivroNaoEncontradoError("O livro deste empréstimo não existe no acervo.")

            if livro_db["quantidade_disponivel"] >= livro_db["quantidade_total"]:
                raise EmprestimoError(
                    "O estoque do livro está inconsistente: todos os exemplares já constam como disponíveis."
                )

            cursor.execute(
                """
                UPDATE emprestimos
                SET
                    data_devolucao = %s,
                    status = 'devolvido',
                    atualizado_em = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    usuario_id,
                    livro_id,
                    data_emprestimo,
                    data_prevista_devolucao,
                    data_devolucao,
                    status,
                    criado_em,
                    atualizado_em;
                """,
                (data_fim, emprestimo),
            )
            resultado = dict(cursor.fetchone())

            cursor.execute(
                """
                UPDATE livros
                SET quantidade_disponivel = quantidade_disponivel + 1
                WHERE id = %s
                  AND quantidade_disponivel < quantidade_total
                RETURNING quantidade_disponivel;
                """,
                (emprestimo_db["livro_id"],),
            )
            estoque = cursor.fetchone()

            if not estoque:
                raise EmprestimoError("Não foi possível devolver o exemplar ao estoque.")

            resultado["livro_titulo"] = emprestimo_db["livro_titulo"]
            resultado["quantidade_disponivel"] = estoque["quantidade_disponivel"]

        conexao.commit()
        return resultado
    except (EmprestimoError, ValueError):
        conexao.rollback()
        raise
    except psycopg2.Error:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def buscar_emprestimos_ativos(usuario_id: int | None = None) -> list[dict[str, object]]:
    """Retorna empréstimos ainda não devolvidos, opcionalmente de um usuário."""
    parametros: tuple[object, ...] = ()
    filtro_usuario = ""

    if usuario_id is not None:
        usuario = _validar_id(usuario_id, "usuario_id")
        filtro_usuario = "AND e.usuario_id = %s"
        parametros = (usuario,)

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT
                    e.id,
                    e.usuario_id,
                    u.nome AS usuario_nome,
                    u.telefone AS usuario_telefone,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    l.isbn AS livro_isbn,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN usuarios u ON u.id = e.usuario_id
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.status IN ('ativo', 'atrasado')
                {filtro_usuario}
                ORDER BY e.data_prevista_devolucao, e.id;
                """,
                parametros,
            )
            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()


def buscar_historico_emprestimos(usuario_id: int | None = None) -> list[dict[str, object]]:
    """Retorna o histórico de empréstimos, opcionalmente filtrado por usuário."""
    parametros: tuple[object, ...] = ()
    filtro_usuario = ""

    if usuario_id is not None:
        usuario = _validar_id(usuario_id, "usuario_id")
        filtro_usuario = "WHERE e.usuario_id = %s"
        parametros = (usuario,)

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT
                    e.id,
                    e.usuario_id,
                    u.nome AS usuario_nome,
                    u.telefone AS usuario_telefone,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    l.isbn AS livro_isbn,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.data_devolucao,
                    e.status,
                    e.criado_em,
                    e.atualizado_em
                FROM emprestimos e
                INNER JOIN usuarios u ON u.id = e.usuario_id
                INNER JOIN livros l ON l.id = e.livro_id
                {filtro_usuario}
                ORDER BY e.data_emprestimo DESC, e.id DESC;
                """,
                parametros,
            )
            return [dict(linha) for linha in cursor.fetchall()]
    finally:
        conexao.close()
