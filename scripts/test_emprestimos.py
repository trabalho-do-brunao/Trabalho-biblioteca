"""Teste manual da consulta de empréstimos ativos."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.emprestimos import buscar_emprestimos_ativos


def main() -> int:
    print("=== Empréstimos ativos ===\n")

    try:
        emprestimos = buscar_emprestimos_ativos()
    except (RuntimeError, ConnectionError, psycopg2.Error) as erro:
        print(f"[ERRO] Não foi possível consultar os empréstimos: {erro}")
        return 1

    if not emprestimos:
        print("Nenhum empréstimo ativo encontrado.")
        return 0

    for emprestimo in emprestimos:
        data_emprestimo = emprestimo["data_emprestimo"].strftime("%d/%m/%Y")
        data_prevista = emprestimo["data_prevista_devolucao"].strftime("%d/%m/%Y")

        print(f"ID: {emprestimo['id']}")
        print(f"Usuário: {emprestimo['usuario_nome']}")
        print(f"Telefone: {emprestimo['usuario_telefone']}")
        print(f"Livro: {emprestimo['livro_titulo']}")
        print(f"Data do empréstimo: {data_emprestimo}")
        print(f"Devolução prevista: {data_prevista}")
        print(f"Status: {emprestimo['status']}")
        print("-" * 45)

    print(f"Total: {len(emprestimos)} empréstimo(s) ativo(s)")
    print("\n=== Consulta concluída com sucesso ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
