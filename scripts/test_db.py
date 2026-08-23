"""Teste manual da conexão da aplicação com o PostgreSQL."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import testar_conexao


def main() -> int:
    print("=== Teste de conexão Python -> PostgreSQL ===\n")

    try:
        resultado = testar_conexao()
    except (RuntimeError, ConnectionError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    conexao = resultado["conexao"]
    registros = resultado["registros"]

    versao = str(conexao["versao"]).split(",")[0]

    print("[OK] Conexão realizada com sucesso.")
    print(f"[OK] Banco atual: {conexao['banco']}")
    print(f"[OK] Usuário PostgreSQL: {conexao['usuario']}")
    print(f"[OK] {versao}")

    print("\nRegistros encontrados:")
    print(f"  usuarios:     {registros['usuarios']}")
    print(f"  livros:       {registros['livros']}")
    print(f"  emprestimos:  {registros['emprestimos']}")
    print(f"  renovacoes:   {registros['renovacoes']}")
    print(f"  mensagens:    {registros['mensagens']}")

    print("\n=== Teste concluído com sucesso ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
