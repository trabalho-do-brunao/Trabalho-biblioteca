"""Regras de autenticação administrativa do BiblioAvisa."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.repositories.autenticacao import (
    buscar_administrador_por_email,
    buscar_administrador_por_sessao,
    criar_administrador as criar_administrador_repo,
    criar_sessao as criar_sessao_repo,
    encerrar_sessao as encerrar_sessao_repo,
)


COOKIE_SESSAO = "biblioavisa_session"
ALGORITMO_SENHA = "pbkdf2_sha256"
ITERACOES_PBKDF2 = 600_000
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class SessaoCriada:
    token: str
    expira_em: datetime
    administrador: dict[str, object]


def normalizar_email(email: str) -> str:
    valor = str(email or "").strip().lower()
    if len(valor) > 150 or not EMAIL_RE.fullmatch(valor):
        raise ValueError("Informe um e-mail válido.")
    return valor


def validar_nome(nome: str) -> str:
    valor = " ".join(str(nome or "").split())
    if len(valor) < 2:
        raise ValueError("O nome do administrador deve ter pelo menos 2 caracteres.")
    if len(valor) > 150:
        raise ValueError("O nome do administrador deve ter no máximo 150 caracteres.")
    return valor


def validar_senha_nova(senha: str) -> str:
    valor = str(senha or "")
    if len(valor) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if len(valor) > 128:
        raise ValueError("A senha deve ter no máximo 128 caracteres.")
    return valor


def gerar_hash_senha(senha: str) -> str:
    senha_validada = validar_senha_nova(senha)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        senha_validada.encode("utf-8"),
        salt,
        ITERACOES_PBKDF2,
    )
    return (
        f"{ALGORITMO_SENHA}${ITERACOES_PBKDF2}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    try:
        algoritmo, iteracoes_texto, salt_hex, digest_hex = hash_armazenado.split("$", 3)
        if algoritmo != ALGORITMO_SENHA:
            return False

        iteracoes = int(iteracoes_texto)
        if iteracoes < 100_000 or iteracoes > 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(digest_hex)
        calculado = hashlib.pbkdf2_hmac(
            "sha256",
            str(senha or "").encode("utf-8"),
            salt,
            iteracoes,
        )
        return hmac.compare_digest(calculado, esperado)
    except (ValueError, TypeError):
        return False


def criar_administrador(nome: str, email: str, senha: str) -> dict[str, object]:
    nome_validado = validar_nome(nome)
    email_validado = normalizar_email(email)
    hash_senha = gerar_hash_senha(senha)
    return criar_administrador_repo(nome_validado, email_validado, hash_senha)


def autenticar_administrador(email: str, senha: str) -> dict[str, object] | None:
    try:
        email_normalizado = normalizar_email(email)
    except ValueError:
        return None

    administrador = buscar_administrador_por_email(email_normalizado)
    if not administrador or not administrador.get("ativo"):
        return None

    if not verificar_senha(senha, str(administrador.get("senha_hash") or "")):
        return None

    return {
        "id": administrador["id"],
        "nome": administrador["nome"],
        "email": administrador["email"],
    }


def _horas_sessao() -> int:
    texto = (os.getenv("AUTH_SESSION_HOURS") or "8").strip()
    try:
        horas = int(texto)
    except ValueError:
        horas = 8
    return min(max(horas, 1), 168)


def criar_sessao(administrador: dict[str, object]) -> SessaoCriada:
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expira_em = datetime.now(timezone.utc) + timedelta(hours=_horas_sessao())
    criar_sessao_repo(int(administrador["id"]), token_hash, expira_em)
    return SessaoCriada(
        token=token,
        expira_em=expira_em,
        administrador={
            "id": administrador["id"],
            "nome": administrador["nome"],
            "email": administrador["email"],
        },
    )


def buscar_administrador_por_token(token: str | None) -> dict[str, object] | None:
    valor = str(token or "").strip()
    if not valor:
        return None
    token_hash = hashlib.sha256(valor.encode("utf-8")).hexdigest()
    administrador = buscar_administrador_por_sessao(token_hash)
    if not administrador:
        return None
    return {
        "id": administrador["id"],
        "nome": administrador["nome"],
        "email": administrador["email"],
        "expira_em": administrador["expira_em"],
    }


def encerrar_sessao(token: str | None) -> None:
    valor = str(token or "").strip()
    if not valor:
        return
    token_hash = hashlib.sha256(valor.encode("utf-8")).hexdigest()
    encerrar_sessao_repo(token_hash)


def cookie_seguro() -> bool:
    return (os.getenv("APP_ENV") or "development").strip().lower() == "production"


def duracao_cookie_segundos() -> int:
    return _horas_sessao() * 60 * 60
