"""Teste manual das operações de usuários.

O script cria um usuário temporário, valida as consultas e remove o registro
no final para não acumular dados de teste no banco.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.usuarios import (
    UsuarioDuplicadoError,
    buscar_usuario_por_id,
    buscar_usuario_por_telefone,
    buscar_usuarios_por_nome,
    cadastrar_usuario,
    listar_usuarios,
    normalizar_telefone,
)


def excluir_usuario_teste(usuario_id: int) -> None:
    """Remove somente o usuário temporário criado por este teste."""
    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
        conexao.commit()
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste de cadastro e consulta de usuários ===\n")

    usuario_criado: dict[str, object] | None = None

    try:
        usuarios_iniciais = listar_usuarios()
        print(f"[OK] Usuários ativos encontrados inicialmente: {len(usuarios_iniciais)}")

        exemplo_formatado = "(42) 99999-0001"
        exemplo_normalizado = normalizar_telefone(exemplo_formatado)
        print(
            f"[OK] Normalização de telefone: {exemplo_formatado} -> {exemplo_normalizado}"
        )

        # Mantém o número na faixa móvel para também validar a variação canônica
        # brasileira que o WhatsApp pode apresentar com ou sem o nono dígito.
        telefone_teste = "55429" + f"{secrets.randbelow(100_000_000):08d}"

        usuario_criado = cadastrar_usuario(
            nome="Usuário Teste Automático",
            telefone=telefone_teste,
            email="teste.automatico@example.com",
        )
        usuario_id = int(usuario_criado["id"])
        print(f"[OK] Usuário temporário cadastrado com ID {usuario_id}.")

        por_id = buscar_usuario_por_id(usuario_id)
        if not por_id or por_id["telefone"] != telefone_teste:
            raise RuntimeError("A busca por ID não retornou o usuário esperado.")
        print("[OK] Busca por ID funcionando.")

        por_telefone = buscar_usuario_por_telefone(telefone_teste)
        if not por_telefone or por_telefone["id"] != usuario_id:
            raise RuntimeError("A busca por telefone não retornou o usuário esperado.")
        print("[OK] Busca por telefone funcionando.")

        telefone_canonico_sem_nono = telefone_teste[:4] + telefone_teste[5:]
        por_variacao = buscar_usuario_por_telefone(telefone_canonico_sem_nono)
        if not por_variacao or por_variacao["id"] != usuario_id:
            raise RuntimeError(
                "A busca não reconheceu a variação canônica brasileira sem o nono dígito."
            )
        print("[OK] Variação canônica de telefone do WhatsApp reconhecida.")

        por_nome = buscar_usuarios_por_nome("Teste Automático")
        if not any(int(usuario["id"]) == usuario_id for usuario in por_nome):
            raise RuntimeError("A busca por nome não retornou o usuário esperado.")
        print("[OK] Busca parcial por nome funcionando.")

        try:
            cadastrar_usuario(
                nome="Usuário Duplicado",
                telefone=telefone_teste,
                email="duplicado@example.com",
            )
        except UsuarioDuplicadoError:
            print("[OK] Telefone duplicado foi bloqueado corretamente.")
        else:
            raise RuntimeError("O sistema permitiu cadastrar um telefone duplicado.")

        print("\n=== Todos os testes de usuários passaram ===")
        return 0

    except (ValueError, RuntimeError, ConnectionError) as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    finally:
        if usuario_criado is not None:
            try:
                excluir_usuario_teste(int(usuario_criado["id"]))
                print("[OK] Usuário temporário removido; banco restaurado.")
            except Exception as erro:
                print(
                    "[ATENÇÃO] O teste terminou, mas não foi possível remover "
                    f"o usuário temporário: {erro}"
                )


if __name__ == "__main__":
    raise SystemExit(main())
