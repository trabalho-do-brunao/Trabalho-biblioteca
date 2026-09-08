"""Rotas HTTP da autenticação administrativa."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.services.autenticacao import (
    COOKIE_SESSAO,
    autenticar_administrador,
    buscar_administrador_por_token,
    cadastro_publico_disponivel,
    cookie_seguro,
    criar_administrador,
    criar_sessao,
    duracao_cookie_segundos,
    encerrar_sessao,
)


router = APIRouter(prefix="/api/auth", tags=["autenticacao"])


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    senha: str = Field(min_length=1, max_length=128)


class CadastroPayload(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    sobrenome: str = Field(min_length=2, max_length=100)
    cpf: str = Field(min_length=11, max_length=14)
    data_nascimento: str = Field(min_length=8, max_length=10)
    whatsapp: str = Field(min_length=10, max_length=25)
    email: str = Field(min_length=3, max_length=150)
    senha: str = Field(min_length=8, max_length=128)


def _admin_publico(administrador: dict[str, object]) -> dict[str, object]:
    return {
        "id": administrador["id"],
        "nome": administrador["nome"],
        "sobrenome": administrador.get("sobrenome"),
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


@router.get("/registration-status")
def consultar_status_cadastro(request: Request) -> dict[str, object]:
    administrador = buscar_administrador_por_token(request.cookies.get(COOKIE_SESSAO))
    publico = cadastro_publico_disponivel()
    return {
        "public_registration_available": publico,
        "authenticated": administrador is not None,
        "can_register": publico or administrador is not None,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def cadastrar_administrador(dados: CadastroPayload, request: Request) -> dict[str, object]:
    administrador_atual = buscar_administrador_por_token(request.cookies.get(COOKIE_SESSAO))
    publico = cadastro_publico_disponivel()

    if not publico and not administrador_atual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O cadastro de novas contas é restrito a administradores autenticados.",
        )

    try:
        administrador = criar_administrador(
            dados.nome,
            dados.email,
            dados.senha,
            sobrenome=dados.sobrenome,
            cpf=dados.cpf,
            data_nascimento=dados.data_nascimento,
            whatsapp=dados.whatsapp,
        )
    except ValueError as erro:
        mensagem = str(erro)
        codigo = status.HTTP_409_CONFLICT if mensagem.startswith("Já existe") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=codigo, detail=mensagem) from erro

    return {
        "ok": True,
        "message": "Conta administrativa criada com sucesso.",
        "admin": _admin_publico(administrador),
        "first_admin": publico,
    }


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
