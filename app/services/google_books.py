"""Integração com a Google Books API para consulta de livros por ISBN."""

from __future__ import annotations

import re
from typing import Any

import requests


GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksError(RuntimeError):
    """Erro ao consultar ou interpretar uma resposta da Google Books API."""


def normalizar_isbn(isbn: str) -> str:
    """Remove formatação do ISBN e valida se ele possui 10 ou 13 caracteres."""
    if not isinstance(isbn, str):
        raise ValueError("O ISBN deve ser informado como texto.")

    normalizado = re.sub(r"[^0-9Xx]", "", isbn).upper()

    if len(normalizado) not in (10, 13):
        raise ValueError("ISBN inválido. Informe um ISBN com 10 ou 13 caracteres.")

    if "X" in normalizado[:-1]:
        raise ValueError("ISBN inválido: X só pode aparecer no último caractere do ISBN-10.")

    if len(normalizado) == 13 and "X" in normalizado:
        raise ValueError("ISBN-13 deve conter somente números.")

    return normalizado


def _identificadores(volume_info: dict[str, Any]) -> set[str]:
    encontrados: set[str] = set()

    for identificador in volume_info.get("industryIdentifiers") or []:
        valor = identificador.get("identifier")
        if valor:
            encontrados.add(re.sub(r"[^0-9Xx]", "", str(valor)).upper())

    return encontrados


def _selecionar_volume(itens: list[dict[str, Any]], isbn: str) -> dict[str, Any]:
    """Prefere um resultado cujo identificador corresponda exatamente ao ISBN buscado."""
    for item in itens:
        volume_info = item.get("volumeInfo") or {}
        if isbn in _identificadores(volume_info):
            return item

    return itens[0]


def buscar_livro_por_isbn(isbn: str, timeout: float = 10.0) -> dict[str, object] | None:
    """Consulta a Google Books API e retorna os dados disponíveis para um ISBN.

    Retorna ``None`` quando nenhum volume é encontrado. Campos que não existem na
    resposta da API são retornados como ``None`` para que o cadastro não dependa
    da presença de todas as informações.
    """
    isbn_normalizado = normalizar_isbn(isbn)

    try:
        resposta = requests.get(
            GOOGLE_BOOKS_URL,
            params={
                "q": f"isbn:{isbn_normalizado}",
                "maxResults": 5,
                "printType": "books",
            },
            timeout=timeout,
        )
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise GoogleBooksError(
            "Não foi possível consultar a Google Books API. Verifique sua conexão "
            "com a internet e tente novamente."
        ) from erro

    try:
        dados = resposta.json()
    except ValueError as erro:
        raise GoogleBooksError("A Google Books API retornou uma resposta inválida.") from erro

    itens = dados.get("items") or []
    if not itens:
        return None

    item = _selecionar_volume(itens, isbn_normalizado)
    volume_info = item.get("volumeInfo") or {}

    autores = volume_info.get("authors") or []
    autor = ", ".join(str(nome) for nome in autores) if autores else None

    imagens = volume_info.get("imageLinks") or {}
    url_capa = imagens.get("thumbnail") or imagens.get("smallThumbnail")
    if url_capa:
        url_capa = str(url_capa).replace("http://", "https://", 1)

    numero_paginas = volume_info.get("pageCount")
    if not isinstance(numero_paginas, int) or numero_paginas <= 0:
        numero_paginas = None

    return {
        "google_books_id": item.get("id"),
        "titulo": volume_info.get("title"),
        "subtitulo": volume_info.get("subtitle"),
        "autor": autor,
        "isbn": isbn_normalizado,
        "editora": volume_info.get("publisher"),
        "data_publicacao": volume_info.get("publishedDate"),
        "descricao": volume_info.get("description"),
        "numero_paginas": numero_paginas,
        "url_capa": url_capa,
    }
