"""Rotas HTTP para consulta e cadastro do acervo de livros."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.repositories.livros import (
    LivroDuplicadoError,
    buscar_livro_por_isbn,
    buscar_livros,
    cadastrar_livro,
    listar_livros,
)
from app.services.google_books import GoogleBooksError, buscar_livro_por_isbn as buscar_google_books


router = APIRouter(prefix="/api/livros", tags=["livros"])


class LivroEntrada(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    subtitulo: str | None = Field(default=None, max_length=200)
    autor: str | None = Field(default=None, max_length=255)
    isbn: str = Field(min_length=10, max_length=25)
    google_books_id: str | None = Field(default=None, max_length=100)
    editora: str | None = Field(default=None, max_length=150)
    data_publicacao: str | None = Field(default=None, max_length=20)
    descricao: str | None = None
    numero_paginas: int | None = Field(default=None, ge=1)
    url_capa: str | None = None
    quantidade_total: int = Field(default=1, ge=1, le=9999)


def _erro_operacao(erro: Exception) -> HTTPException:
    if isinstance(erro, LivroDuplicadoError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
    if isinstance(erro, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))
    if isinstance(erro, GoogleBooksError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar a Google Books agora. Tente novamente em instantes.",
        )
    if isinstance(erro, ConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o banco de dados. Tente novamente em instantes.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Não foi possível concluir a operação com o acervo.",
    )


@router.get("")
def listar(busca: str = Query(default="", max_length=200)) -> dict[str, object]:
    """Lista o acervo ou pesquisa por ID, título, autor, ISBN e editora."""
    try:
        livros = buscar_livros(busca) if busca.strip() else listar_livros()
        return {"livros": livros, "total": len(livros)}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.get("/consulta-isbn/{isbn}")
def consultar_isbn(isbn: str) -> dict[str, object]:
    """Consulta primeiro o acervo e depois a Google Books para preparar o cadastro."""
    try:
        existente = buscar_livro_por_isbn(isbn)
        if existente:
            return {
                "encontrado": True,
                "ja_cadastrado": True,
                "fonte": "acervo",
                "livro": existente,
            }

        livro = buscar_google_books(isbn)
        if livro is None:
            raise HTTPException(status_code=404, detail="Nenhum livro foi encontrado para este ISBN.")

        return {
            "encontrado": True,
            "ja_cadastrado": False,
            "fonte": "google_books",
            "livro": livro,
        }
    except HTTPException:
        raise
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.post("", status_code=status.HTTP_201_CREATED)
def cadastrar(dados: LivroEntrada) -> dict[str, object]:
    """Confirma o cadastro de um livro previamente revisado na interface."""
    try:
        payload = dados.model_dump(exclude={"quantidade_total"})
        livro = cadastrar_livro(payload, quantidade_total=dados.quantidade_total)
        return {"livro": livro, "mensagem": "Livro cadastrado no acervo com sucesso."}
    except Exception as erro:
        raise _erro_operacao(erro) from erro
