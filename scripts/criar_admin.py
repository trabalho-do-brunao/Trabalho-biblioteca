"""Cria uma conta administrativa do BiblioAvisa sem expor a senha no terminal."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.autenticacao import criar_administrador


def main() -> int:
    print("=== Criar administrador do BiblioAvisa ===\n")
    print("A senha será digitada de forma oculta e ficará armazenada apenas como hash.\n")

    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")

    if senha != confirmacao:
        print("\n[ERRO] As senhas não coincidem.", file=sys.stderr)
        return 1

    try:
        administrador = criar_administrador(nome, email, senha)
    except ValueError as erro:
        print(f"\n[ERRO] {erro}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "\n[ERRO] Não foi possível criar a conta. Confirme se o PostgreSQL está ativo "
            "e execute setup.bat para aplicar as migrações.",
            file=sys.stderr,
        )
        return 1

    print("\n[OK] Conta administrativa criada com sucesso.")
    print(f"[OK] ID: {administrador['id']}")
    print(f"[OK] Nome: {administrador['nome']}")
    print(f"[OK] E-mail: {administrador['email']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
