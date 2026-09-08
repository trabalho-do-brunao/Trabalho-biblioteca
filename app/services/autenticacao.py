"""Regras de autenticação administrativa do BiblioAvisa."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.repositories.autenticacao import (
    buscar_administrador_por_email,
    buscar_administrador_por_sessao,
    contar_administradores,
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


def validar_sobrenome(sobrenome: str) -> str:
    valor = " ".join(str(sobrenome or "").split())
    if len(valor) < 2:
        raise ValueError("Informe o sobrenome.")
    if len(valor) > 100:
        raise ValueError("O sobrenome deve ter no máximo 100 caracteres.")
    return valor


def validar_senha_nova(senha: str) -> str:
    valor = str(senha or "")
    if len(valor) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if len(valor) > 128:
        raise ValueError("A senha deve ter no máximo 128 caracteres.")
    return valor


def validar_cpf(cpf: str) -> str:
    digitos = re.sub(r"\D", "", str(cpf or ""))
    if len(digitos) != 11 or len(set(digitos)) == 1:
        raise ValueError("Informe um CPF válido.")

    def calcular(base: str, peso_inicial: int) -> int:
        soma = sum(int(numero) * (peso_inicial - indice) for indice, numero in enumerate(base))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    primeiro = calcular(digitos[:9], 10)
    segundo = calcular(digitos[:10], 11)
    if primeiro != int(digitos[9]) or segundo != int(digitos[10]):
        raise ValueError("Informe um CPF válido.")
    return digitos


def validar_data_nascimento(valor: str | date) -> date:
    if isinstance(valor, date):
        resultado = valor
    else:
        texto = str(valor or "").strip()
        resultado = None
        for formato in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                resultado = datetime.strptime(texto, formato).date()
                break
            except ValueError:
                continue
        if resultado is None:
            raise ValueError("Informe uma data de nascimento válida.")

    hoje = date.today()
    if resultado > hoje:
        raise ValueError("A data de nascimento não pode estar no futuro.")
    if resultado.year < 1900:
        raise ValueError("Informe uma data de nascimento válida.")
    return resultado


def normalizar_whatsapp(valor: str) -> str:
    texto = str(valor or "").strip()
    digitos = re.sub(r"\D", "", texto)
    if digitos.startswith("00"):
        digitos = digitos[2:]
    if len(digitos) in {10, 11}:
        digitos = "55" + digitos
    if len(digitos) < 12 or len(digitos) > 15:
        raise ValueError("Informe um WhatsApp válido com DDD.")
    return digitos


def gerar_hash_senha(senha: str) -> str:
    senha_validada = validar_senha_nova(senha)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        senha_validada.encode("utf-8"),
        salt,
        ITERACOES_PBKDF2,
    )
    return f"{ALGORITMO_SENHA}${ITERACOES_PBKDF2}${salt.hex()}${digest.hex()}"


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


def cadastro_publico_disponivel() -> bool:
    """Permite cadastro sem sessão somente enquanto não existir nenhum administrador."""
    return contar_administradores() == 0


def criar_administrador(
    nome: str,
    email: str,
    senha: str,
    *,
    sobrenome: str | None = None,
    cpf: str | None = None,
    data_nascimento: str | date | None = None,
    whatsapp: str | None = None,
) -> dict[str, object]:
    nome_validado = validar_nome(nome)
    email_validado = normalizar_email(email)
    hash_senha = gerar_hash_senha(senha)

    sobrenome_validado = validar_sobrenome(sobrenome) if sobrenome is not None else None
    cpf_validado = validar_cpf(cpf) if cpf is not None else None
    data_validada = validar_data_nascimento(data_nascimento) if data_nascimento is not None else None
    whatsapp_validado = normalizar_whatsapp(whatsapp) if whatsapp is not None else None

    return criar_administrador_repo(
        nome_validado,
        email_validado,
        hash_senha,
        sobrenome=sobrenome_validado,
        cpf=cpf_validado,
        data_nascimento=data_validada,
        whatsapp=whatsapp_validado,
    )


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
        "sobrenome": administrador.get("sobrenome"),
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
            "sobrenome": administrador.get("sobrenome"),
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
        "sobrenome": administrador.get("sobrenome"),
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
