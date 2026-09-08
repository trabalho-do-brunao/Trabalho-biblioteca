"""Rotas HTTP da autenticação administrativa."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.services.autenticacao import (
    COOKIE_SESSAO,
    autenticar_administrador,
    buscar_administrador_por_token,
    cookie_seguro,
    criar_sessao,
    duracao_cookie_segundos,
    encerrar_sessao,
)


router = APIRouter(prefix="/api/auth", tags=["autenticacao"])


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    senha: str = Field(min_length=1, max_length=128)


def _admin_publico(administrador: dict[str, object]) -> dict[str, object]:
    return {
        "id": administrador["id"],
        "nome": administrador["nome"],
        "email": administrador["email"],
    }


def exigir_administrador(request: Request) -> dict[str, object]:
    token = request.cookies.get(COOKIE_SESSAO)
    administrador = buscar_administrador_por_token(token)
    if not administrador:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Faça login para acessar esta área.",
        )
    return administrador


@router.post("/login")
def login(dados: LoginPayload, response: Response) -> dict[str, object]:
    administrador = autenticar_administrador(dados.email, dados.senha)
    if not administrador:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    sessao = criar_sessao(administrador)
    response.set_cookie(
        key=COOKIE_SESSAO,
        value=sessao.token,
        max_age=duracao_cookie_segundos(),
        httponly=True,
        secure=cookie_seguro(),
        samesite="lax",
        path="/",
    )

    return {
        "authenticated": True,
        "admin": _admin_publico(sessao.administrador),
        "expires_at": sessao.expira_em.isoformat(),
    }


@router.get("/session")
def consultar_sessao(request: Request) -> dict[str, object]:
    administrador = buscar_administrador_por_token(request.cookies.get(COOKIE_SESSAO))
    if not administrador:
        return {"authenticated": False, "admin": None, "expires_at": None}

    return {
        "authenticated": True,
        "admin": _admin_publico(administrador),
        "expires_at": administrador["expira_em"].isoformat(),
    }


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    encerrar_sessao(request.cookies.get(COOKIE_SESSAO))
    response.delete_cookie(
        key=COOKIE_SESSAO,
        path="/",
        httponly=True,
        secure=cookie_seguro(),
        samesite="lax",
    )
    return {"ok": True}
