"""Consulta um ISBN no Google Books e permite revisar antes de salvar no PostgreSQL."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.livros import (
    LivroDuplicadoError,
    buscar_livro_por_isbn as buscar_livro_no_banco,
    cadastrar_livro,
)
from app.services.google_books import GoogleBooksError, buscar_livro_por_isbn


def exibir_livro(livro: dict[str, object]) -> None:
    """Mostra os principais campos para revisão antes do cadastro."""
    print("\n--- Dados encontrados ---")
    print(f"Título:          {livro.get('titulo') or '-'}")
    print(f"Subtítulo:       {livro.get('subtitulo') or '-'}")
    print(f"Autor(es):       {livro.get('autor') or '-'}")
    print(f"ISBN:            {livro.get('isbn') or '-'}")
    print(f"Editora:         {livro.get('editora') or '-'}")
    print(f"Publicação:      {livro.get('data_publicacao') or '-'}")
    print(f"Páginas:         {livro.get('numero_paginas') or '-'}")
    print(f"Google Books ID: {livro.get('google_books_id') or '-'}")
    print(f"Capa:            {livro.get('url_capa') or '-'}")

    descricao = livro.get("descricao")
    if descricao:
        texto = str(descricao).replace("\n", " ").strip()
        if len(texto) > 300:
            texto = texto[:297] + "..."
        print(f"Descrição:       {texto}")
    else:
        print("Descrição:       -")


def ler_quantidade() -> int:
    valor = input("Quantidade de exemplares [1]: ").strip()
    if not valor:
        return 1

    try:
        quantidade = int(valor)
    except ValueError as erro:
        raise ValueError("A quantidade precisa ser um número inteiro.") from erro

    if quantidade <= 0:
        raise ValueError("A quantidade precisa ser maior que zero.")

    return quantidade


def main() -> int:
    print("=== Cadastro de livro por ISBN ===\n")
    isbn = input("Informe o ISBN: ").strip()

    try:
        existente = buscar_livro_no_banco(isbn)
        if existente:
            print(
                f"\n[INFO] Este ISBN já está cadastrado: "
                f"{existente['titulo']} (ID {existente['id']})."
            )
            return 0

        livro = buscar_livro_por_isbn(isbn)
    except (ValueError, GoogleBooksError, ConnectionError) as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    if livro is None:
        print("\n[INFO] Nenhum livro foi encontrado no Google Books para esse ISBN.")
        return 0

    if not livro.get("titulo"):
        titulo = input("\nA API não retornou o título. Informe o título manualmente: ").strip()
        if not titulo:
            print("[ERRO] O título é obrigatório para cadastrar o livro.")
            return 1
        livro["titulo"] = titulo

    exibir_livro(livro)

    confirmar = input("\nSalvar este livro no PostgreSQL? [s/N]: ").strip().lower()
    if confirmar not in {"s", "sim"}:
        print("\n[INFO] Cadastro cancelado. Nenhuma alteração foi feita no banco.")
        return 0

    try:
        quantidade = ler_quantidade()
        salvo = cadastrar_livro(livro, quantidade_total=quantidade)
    except (ValueError, LivroDuplicadoError, ConnectionError) as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    print("\n[OK] Livro cadastrado com sucesso.")
    print(f"ID: {salvo['id']}")
    print(f"Título: {salvo['titulo']}")
    print(f"ISBN: {salvo['isbn']}")
    print(f"Exemplares disponíveis: {salvo['quantidade_disponivel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
