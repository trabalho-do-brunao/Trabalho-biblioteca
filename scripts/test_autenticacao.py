"""Teste seguro da autenticação administrativa sem credenciais reais."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.services.autenticacao import (
    autenticar_administrador,
    buscar_administrador_por_token,
    criar_administrador,
    criar_sessao,
    encerrar_sessao,
)


def main() -> int:
    identificador = uuid.uuid4().hex[:12]
    email = f"auth-ci-{identificador}@example.test"
    senha = "SenhaTeste!123"
    administrador_id = None
    token = None

    try:
        administrador = criar_administrador("Administrador de Teste", email, senha)
        administrador_id = int(administrador["id"])
        print("[OK] Administrador temporário criado")

        conexao = conectar()
        try:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT senha_hash FROM administradores WHERE id = %s;",
                    (administrador_id,),
                )
                senha_hash = cursor.fetchone()[0]
        finally:
            conexao.close()

        assert senha_hash != senha, "A senha não pode ser armazenada em texto puro."
        assert senha not in senha_hash, "A senha não pode fazer parte do hash armazenado."
        assert senha_hash.startswith("pbkdf2_sha256$"), "Formato de hash inesperado."
        print("[OK] Senha armazenada somente como hash PBKDF2")

        assert autenticar_administrador(email, "senha-incorreta") is None
        autenticado = autenticar_administrador(email, senha)
        assert autenticado is not None
        assert autenticado["email"] == email
        print("[OK] Credencial incorreta é rejeitada e credencial correta é aceita")

        sessao = criar_sessao(autenticado)
        token = sessao.token
        assert token

        conexao = conectar()
        try:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT token_hash FROM sessoes_admin WHERE administrador_id = %s;",
                    (administrador_id,),
                )
                token_hash = cursor.fetchone()[0]
        finally:
            conexao.close()

        assert token_hash != token, "O token puro não pode ser persistido."
        assert token not in token_hash, "O token puro não pode fazer parte do valor persistido."
        assert len(token_hash) == 64
        print("[OK] Sessão persiste somente o hash SHA-256 do token")

        sessao_valida = buscar_administrador_por_token(token)
        assert sessao_valida is not None
        assert int(sessao_valida["id"]) == administrador_id
        print("[OK] Sessão válida identifica o administrador")

        encerrar_sessao(token)
        token = None
        assert buscar_administrador_por_token(sessao.token) is None
        print("[OK] Logout invalida a sessão")

        print("\n=== Teste de autenticação passou ===")
        return 0
    finally:
        if token:
            try:
                encerrar_sessao(token)
            except Exception:
                pass

        if administrador_id is not None:
            conexao = conectar()
            try:
                with conexao.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM sessoes_admin WHERE administrador_id = %s;",
                        (administrador_id,),
                    )
                    cursor.execute(
                        "DELETE FROM administradores WHERE id = %s;",
                        (administrador_id,),
                    )
                conexao.commit()
            finally:
                conexao.close()


if __name__ == "__main__":
    raise SystemExit(main())
