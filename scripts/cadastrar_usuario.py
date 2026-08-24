"""Cadastro simples e persistente de usuários da biblioteca pelo terminal.

Este script é uma interface provisória para desenvolvimento. Ele reutiliza o
repositório de usuários e não contém regras próprias de cadastro. A futura
interface web poderá chamar a mesma camada de aplicação.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.usuarios import UsuarioDuplicadoError, cadastrar_usuario


def main() -> int:
    print("=== BiblioAvisa - Cadastro de usuário ===\n")
    print("O telefone cadastrado identifica o usuário nas respostas do WhatsApp.")
    print("Informe DDD e número; para números brasileiros o DDI 55 é opcional.\n")

    nome = input("Nome: ").strip()
    telefone = input("Telefone: ").strip()
    email = input("E-mail (opcional): ").strip() or None

    confirmacao = input("\nSalvar este usuário? Digite SIM: ").strip().upper()
    if confirmacao != "SIM":
        print("[INFO] Cadastro cancelado. Nenhum dado foi alterado.")
        return 0

    try:
        usuario = cadastrar_usuario(nome=nome, telefone=telefone, email=email)
    except UsuarioDuplicadoError as erro:
        print(f"[ERRO] {erro}")
        return 1
    except (ValueError, RuntimeError, ConnectionError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    print("\n[OK] Usuário cadastrado com sucesso.")
    print(f"[OK] ID: {usuario['id']}")
    print(f"[OK] Nome: {usuario['nome']}")
    print(f"[OK] Status: {'ativo' if usuario['ativo'] else 'inativo'}")
    print("[OK] O telefone deste usuário já pode ser reconhecido pelo fluxo do WhatsApp.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
