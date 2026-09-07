"""Teste controlado das operações usadas pela tela de livros."""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.livros import (
    LivroDuplicadoError,
    buscar_livro_por_isbn,
    buscar_livros,
    cadastrar_livro,
    listar_livros,
)


def ok(mensagem: str) -> None:
    print(f"[OK] {mensagem}")


def limpar(livro_id: int | None) -> None:
    if not livro_id:
        return
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM livros WHERE id = %s;", (livro_id,))
        conexao.commit()
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste da gestão de livros ===\n")
    livro_id = None
    sufixo = int(time.time()) % 10_000_000
    isbn = f"978000{sufixo:07d}"

    dados = {
        "titulo": f"Livro Teste Frontend {sufixo}",
        "subtitulo": "Registro temporário",
        "autor": "Equipe BiblioAvisa",
        "isbn": isbn,
        "google_books_id": None,
        "editora": "Editora Teste",
        "data_publicacao": "2026",
        "descricao": "Criado automaticamente pelo teste controlado do acervo.",
        "numero_paginas": 120,
        "url_capa": None,
    }

    try:
        livro = cadastrar_livro(dados, quantidade_total=3)
        livro_id = int(livro["id"])
        assert livro["quantidade_total"] == 3
        assert livro["quantidade_disponivel"] == 3
        ok("Livro temporário cadastrado com todos os exemplares disponíveis")

        por_isbn = buscar_livro_por_isbn(isbn)
        assert por_isbn and int(por_isbn["id"]) == livro_id
        ok("Consulta por ISBN encontrou o registro no PostgreSQL")

        encontrados = buscar_livros("Equipe BiblioAvisa")
        assert any(int(item["id"]) == livro_id for item in encontrados)
        ok("Pesquisa por autor encontrou o livro")

        listados = listar_livros()
        assert any(int(item["id"]) == livro_id for item in listados)
        ok("Listagem do acervo retornou o registro real")

        try:
            cadastrar_livro(dados, quantidade_total=1)
        except LivroDuplicadoError:
            ok("ISBN duplicado foi bloqueado pelo backend")
        else:
            raise AssertionError("O cadastro de ISBN duplicado deveria ter sido bloqueado.")

        print("\n=== Teste da gestão de livros passou ===")
        return 0
    finally:
        limpar(livro_id)
        if livro_id:
            ok("Dados temporários removidos do PostgreSQL")


if __name__ == "__main__":
    raise SystemExit(main())
