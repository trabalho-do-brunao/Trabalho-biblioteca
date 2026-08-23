"""Teste manual da consulta de livros na Google Books API."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.google_books import GoogleBooksError, buscar_livro_por_isbn


def main() -> int:
    print("=== Teste Google Books por ISBN ===\n")

    isbn = input("Informe um ISBN para consultar: ").strip()

    try:
        livro = buscar_livro_por_isbn(isbn)
    except (ValueError, GoogleBooksError) as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    if livro is None:
        print("\n[INFO] Nenhum livro foi encontrado para esse ISBN.")
        return 0

    print("\n[OK] Livro encontrado:\n")
    print(f"Título:            {livro.get('titulo') or '-'}")
    print(f"Subtítulo:         {livro.get('subtitulo') or '-'}")
    print(f"Autor(es):         {livro.get('autor') or '-'}")
    print(f"ISBN:              {livro.get('isbn') or '-'}")
    print(f"Editora:           {livro.get('editora') or '-'}")
    print(f"Publicação:        {livro.get('data_publicacao') or '-'}")
    print(f"Páginas:           {livro.get('numero_paginas') or '-'}")
    print(f"Google Books ID:   {livro.get('google_books_id') or '-'}")
    print(f"Capa:              {livro.get('url_capa') or '-'}")

    descricao = livro.get("descricao")
    if descricao:
        texto = str(descricao).replace("\n", " ").strip()
        if len(texto) > 300:
            texto = texto[:297] + "..."
        print(f"Descrição:         {texto}")
    else:
        print("Descrição:         -")

    print("\n=== Consulta concluída com sucesso ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
