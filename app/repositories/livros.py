"""Consultas e operações de persistência relacionadas ao acervo de livros."""

from __future__ import annotations

from typing import Mapping

import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extras import RealDictCursor

from app.db import conectar
from app.services.google_books import normalizar_isbn


class LivroDuplicadoError(ValueError):
    """Indica tentativa de cadastrar um ISBN que já existe no acervo."""


CAMPOS_LIVRO = """
    id,
    titulo,
    subtitulo,
    autor,
    isbn,
    google_books_id,
    editora,
    data_publicacao,
    descricao,
    numero_paginas,
    url_capa,
    quantidade_total,
    quantidade_disponivel,
    criado_em
"""


def _texto_limitado(valor: object, limite: int) -> str | None:
    if valor is None:
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    return texto[:limite]


def listar_livros(limite: int = 500) -> list[dict[str, object]]:
    """Lista o acervo real ordenado por título."""
    limite_seguro = max(1, min(int(limite), 1000))
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT {CAMPOS_LIVRO}
                FROM livros
                ORDER BY titulo, id
                LIMIT %s;
                """,
                (limite_seguro,),
            )
            return [dict(item) for item in cursor.fetchall()]
    finally:
        conexao.close()


def buscar_livros(termo: str, limite: int = 200) -> list[dict[str, object]]:
    """Pesquisa por ID, título, autor, ISBN ou editora sem duplicar regras no frontend."""
    busca = str(termo or "").strip()
    if not busca:
        return listar_livros(limite=limite)

    limite_seguro = max(1, min(int(limite), 500))
    padrao = f"%{busca}%"
    id_busca = int(busca) if busca.isdigit() else None
    isbn_busca = "".join(caractere for caractere in busca.upper() if caractere.isdigit() or caractere == "X")

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT {CAMPOS_LIVRO}
                FROM livros
                WHERE (%s::INTEGER IS NOT NULL AND id = %s)
                   OR titulo ILIKE %s
                   OR COALESCE(autor, '') ILIKE %s
                   OR COALESCE(editora, '') ILIKE %s
                   OR isbn ILIKE %s
                   OR (%s <> '' AND isbn ILIKE %s)
                ORDER BY titulo, id
                LIMIT %s;
                """,
                (
                    id_busca,
                    id_busca,
                    padrao,
                    padrao,
                    padrao,
                    padrao,
                    isbn_busca,
                    f"%{isbn_busca}%",
                    limite_seguro,
                ),
            )
            return [dict(item) for item in cursor.fetchall()]
    finally:
        conexao.close()


def buscar_livro_por_isbn(isbn: str) -> dict[str, object] | None:
    """Retorna um livro cadastrado pelo ISBN ou ``None`` se ele não existir."""
    isbn_normalizado = normalizar_isbn(isbn)
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT {CAMPOS_LIVRO}
                FROM livros
                WHERE isbn = %s;
                """,
                (isbn_normalizado,),
            )
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
    finally:
        conexao.close()


def cadastrar_livro(
    dados: Mapping[str, object],
    quantidade_total: int = 1,
) -> dict[str, object]:
    """Cadastra um livro no PostgreSQL a partir dos dados revisados pelo usuário."""
    try:
        quantidade = int(quantidade_total)
    except (TypeError, ValueError) as erro:
        raise ValueError("A quantidade total deve ser um número inteiro.") from erro

    if quantidade <= 0:
        raise ValueError("A quantidade total deve ser maior que zero.")

    titulo = _texto_limitado(dados.get("titulo"), 200)
    if not titulo:
        raise ValueError("O livro precisa ter um título antes de ser salvo.")

    isbn_bruto = dados.get("isbn")
    if not isbn_bruto:
        raise ValueError("O livro precisa ter um ISBN antes de ser salvo.")

    isbn = normalizar_isbn(str(isbn_bruto))

    parametros = {
        "titulo": titulo,
        "subtitulo": _texto_limitado(dados.get("subtitulo"), 200),
        "autor": _texto_limitado(dados.get("autor"), 255),
        "isbn": isbn,
        "google_books_id": _texto_limitado(dados.get("google_books_id"), 100),
        "editora": _texto_limitado(dados.get("editora"), 150),
        "data_publicacao": _texto_limitado(dados.get("data_publicacao"), 20),
        "descricao": str(dados["descricao"]).strip() if dados.get("descricao") else None,
        "numero_paginas": dados.get("numero_paginas"),
        "url_capa": str(dados["url_capa"]).strip() if dados.get("url_capa") else None,
        "quantidade_total": quantidade,
    }

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO livros (
                    titulo,
                    subtitulo,
                    autor,
                    isbn,
                    google_books_id,
                    editora,
                    data_publicacao,
                    descricao,
                    numero_paginas,
                    url_capa,
                    quantidade_total,
                    quantidade_disponivel
                )
                VALUES (
                    %(titulo)s,
                    %(subtitulo)s,
                    %(autor)s,
                    %(isbn)s,
                    %(google_books_id)s,
                    %(editora)s,
                    %(data_publicacao)s,
                    %(descricao)s,
                    %(numero_paginas)s,
                    %(url_capa)s,
                    %(quantidade_total)s,
                    %(quantidade_total)s
                )
                RETURNING
                    id,
                    titulo,
                    subtitulo,
                    autor,
                    isbn,
                    google_books_id,
                    editora,
                    data_publicacao,
                    descricao,
                    numero_paginas,
                    url_capa,
                    quantidade_total,
                    quantidade_disponivel,
                    criado_em;
                """,
                parametros,
            )
            resultado = dict(cursor.fetchone())

        conexao.commit()
        return resultado
    except UniqueViolation as erro:
        conexao.rollback()
        raise LivroDuplicadoError(
            f"Já existe um livro cadastrado com o ISBN {isbn}."
        ) from erro
    except psycopg2.Error:
        conexao.rollback()
        raise
    finally:
        conexao.close()
