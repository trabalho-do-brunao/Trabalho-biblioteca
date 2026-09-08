"""Teste seguro da autenticação e do cadastro administrativo sem credenciais reais."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.routes.auth import exigir_administrador
from app.services.autenticacao import (
    COOKIE_SESSAO,
    autenticar_administrador,
    buscar_administrador_por_token,
    criar_administrador,
    criar_sessao,
    encerrar_sessao,
)


class PedidoFake:
    def __init__(self, cookies: dict[str, str]):
        self.cookies = cookies


def gerar_cpf_teste() -> str:
    base = f"{int(uuid.uuid4().hex[:10], 16) % 1_000_000_000:09d}"
    if len(set(base)) == 1:
        base = "529982247"

    def digito(parcial: str, peso_inicial: int) -> int:
        soma = sum(int(numero) * (peso_inicial - indice) for indice, numero in enumerate(parcial))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    primeiro = digito(base, 10)
    segundo = digito(base + str(primeiro), 11)
    return base + str(primeiro) + str(segundo)


def main() -> int:
    identificador = uuid.uuid4().hex[:12]
    email = f"auth-ci-{identificador}@example.test"
    senha = "SenhaTeste!123"
    cpf = gerar_cpf_teste()
    whatsapp = f"41{int(uuid.uuid4().hex[:8], 16) % 1_000_000_000:09d}"
    administrador_id = None
    token = None

    try:
        administrador = criar_administrador(
            "Administrador",
            email,
            senha,
            sobrenome="de Teste",
            cpf=cpf,
            data_nascimento="01/01/2000",
            whatsapp=whatsapp,
        )
        administrador_id = int(administrador["id"])
        print("[OK] Administrador temporário criado com os campos da tela de cadastro")

        conexao = conectar()
        try:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT senha_hash, sobrenome, cpf, data_nascimento, whatsapp
                    FROM administradores
                    WHERE id = %s;
                    """,
                    (administrador_id,),
                )
                senha_hash, sobrenome, cpf_salvo, nascimento, whatsapp_salvo = cursor.fetchone()
        finally:
            conexao.close()

        assert sobrenome == "de Teste"
        assert cpf_salvo == cpf
        assert nascimento.isoformat() == "2000-01-01"
        assert whatsapp_salvo == "55" + whatsapp
        print("[OK] CPF, nascimento e WhatsApp foram normalizados e persistidos")

        assert senha_hash != senha, "A senha não pode ser armazenada em texto puro."
        assert senha not in senha_hash, "A senha não pode fazer parte do hash armazenado."
        assert senha_hash.startswith("pbkdf2_sha256$"), "Formato de hash inesperado."
        print("[OK] Senha armazenada somente como hash PBKDF2")

        assert autenticar_administrador(email, "senha-incorreta") is None
        autenticado = autenticar_administrador(email, senha)
        assert autenticado is not None
        assert autenticado["email"] == email
        assert autenticado["sobrenome"] == "de Teste"
        print("[OK] Credencial incorreta é rejeitada e credencial correta é aceita")

        try:
            exigir_administrador(PedidoFake({}))
        except HTTPException as erro:
            assert erro.status_code == 401
        else:
            raise AssertionError("Uma rota protegida deveria rejeitar requisição sem sessão.")
        print("[OK] Requisição sem sessão é bloqueada com HTTP 401")

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

        admin_rota = exigir_administrador(PedidoFake({COOKIE_SESSAO: token}))
        assert int(admin_rota["id"]) == administrador_id
        print("[OK] Sessão válida libera a proteção administrativa")

        encerrar_sessao(token)
        token = None
        assert buscar_administrador_por_token(sessao.token) is None
        print("[OK] Logout invalida a sessão")

        print("\n=== Teste de autenticação e cadastro passou ===")
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
