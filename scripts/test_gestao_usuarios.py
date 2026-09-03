"""Teste controlado das operações usadas pela tela de usuários."""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.usuarios import (
    atualizar_usuario,
    buscar_usuarios,
    cadastrar_usuario,
    definir_usuario_ativo,
    normalizar_telefone,
)


def ok(mensagem: str) -> None:
    print(f"[OK] {mensagem}")


def limpar(usuario_id: int | None) -> None:
    if not usuario_id:
        return
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
        conexao.commit()
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste da gestão de usuários ===\n")
    usuario_id = None
    sufixo = int(time.time()) % 10_000_000
    telefone_internacional = f"+1555{sufixo:07d}"
    telefone_br = f"419{sufixo % 100_000_000:08d}"

    try:
        assert normalizar_telefone(telefone_internacional) == telefone_internacional[1:]
        ok("Telefone com + preserva o código internacional sem receber 55")

        usuario = cadastrar_usuario(
            "Teste Frontend Usuarios",
            telefone_internacional,
            "TESTE.FRONTEND@EXAMPLE.COM",
        )
        usuario_id = int(usuario["id"])
        assert usuario["email"] == "teste.frontend@example.com"
        ok("Usuário temporário cadastrado e e-mail normalizado")

        encontrados = buscar_usuarios("Teste Frontend Usuarios", incluir_inativos=True)
        assert any(int(item["id"]) == usuario_id for item in encontrados)
        ok("Pesquisa por nome encontrou o registro real do PostgreSQL")

        atualizado = atualizar_usuario(
            usuario_id,
            "Teste Frontend Editado",
            telefone_br,
            "editado@example.com",
        )
        assert atualizado and atualizado["nome"] == "Teste Frontend Editado"
        assert str(atualizado["telefone"]).startswith("55")
        ok("Edição atualizou nome, telefone e e-mail")

        inativo = definir_usuario_ativo(usuario_id, False)
        assert inativo and inativo["ativo"] is False
        ok("Usuário foi inativado sem ser excluído")

        ativo = definir_usuario_ativo(usuario_id, True)
        assert ativo and ativo["ativo"] is True
        ok("Usuário foi reativado")

        print("\n=== Teste da gestão de usuários passou ===")
        return 0
    finally:
        limpar(usuario_id)
        if usuario_id:
            ok("Dados temporários removidos do PostgreSQL")


if __name__ == "__main__":
    raise SystemExit(main())
