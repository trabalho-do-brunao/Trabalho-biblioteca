"""Rotas HTTP para gestão dos usuários da biblioteca."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.repositories.usuarios import (
    UsuarioDuplicadoError,
    atualizar_usuario,
    buscar_usuarios,
    cadastrar_usuario,
    definir_usuario_ativo,
    listar_usuarios,
)


router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


class UsuarioEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    telefone: str = Field(min_length=8, max_length=30)
    email: str | None = Field(default=None, max_length=150)


class UsuarioStatusEntrada(BaseModel):
    ativo: bool


def _erro_operacao(erro: Exception) -> HTTPException:
    if isinstance(erro, UsuarioDuplicadoError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
    if isinstance(erro, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))
    if isinstance(erro, ConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o banco de dados. Tente novamente em instantes.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Não foi possível concluir a operação com o usuário.",
    )


@router.get("")
def listar(
    busca: str = Query(default="", max_length=150),
    incluir_inativos: bool = Query(default=True),
) -> dict[str, object]:
    """Lista usuários ou pesquisa por ID, nome, telefone e e-mail."""
    try:
        usuarios = (
            buscar_usuarios(busca, incluir_inativos=incluir_inativos)
            if busca.strip()
            else listar_usuarios(apenas_ativos=not incluir_inativos)
        )
        return {"usuarios": usuarios, "total": len(usuarios)}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.post("", status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioEntrada) -> dict[str, object]:
    """Cadastra um usuário usando as regras já existentes no backend."""
    try:
        usuario = cadastrar_usuario(dados.nome, dados.telefone, dados.email)
        return {"usuario": usuario, "mensagem": "Usuário cadastrado com sucesso."}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.patch("/{usuario_id}")
def atualizar(usuario_id: int, dados: UsuarioEntrada) -> dict[str, object]:
    """Edita nome, telefone e e-mail sem alterar o histórico do usuário."""
    try:
        usuario = atualizar_usuario(usuario_id, dados.nome, dados.telefone, dados.email)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return {"usuario": usuario, "mensagem": "Usuário atualizado com sucesso."}
    except HTTPException:
        raise
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.patch("/{usuario_id}/status")
def alterar_status(usuario_id: int, dados: UsuarioStatusEntrada) -> dict[str, object]:
    """Ativa ou inativa um usuário, preservando seus registros históricos."""
    try:
        usuario = definir_usuario_ativo(usuario_id, dados.ativo)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        situacao = "ativado" if dados.ativo else "inativado"
        return {"usuario": usuario, "mensagem": f"Usuário {situacao} com sucesso."}
    except HTTPException:
        raise
    except Exception as erro:
        raise _erro_operacao(erro) from erro
