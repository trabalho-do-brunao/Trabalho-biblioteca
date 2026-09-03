"""Endpoint seguro para demonstrar o fluxo React -> Python -> PostgreSQL -> React."""

from __future__ import annotations

import os
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.db import testar_conexao

router = APIRouter(prefix="/api/demo", tags=["demonstracao"])


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def cpf_valido(valor: str) -> bool:
    cpf = somente_digitos(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calcular(base: str, peso_inicial: int) -> int:
        soma = sum(int(numero) * (peso_inicial - indice) for indice, numero in enumerate(base))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    primeiro = calcular(cpf[:9], 10)
    segundo = calcular(cpf[:10], 11)
    return primeiro == int(cpf[9]) and segundo == int(cpf[10])


class DemonstracaoEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    cpf: str = Field(min_length=11, max_length=14)
    telefone: str = Field(min_length=10, max_length=25)
    data: str = Field(min_length=10, max_length=10)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.strip().split())
        if len(valor) < 2:
            raise ValueError("Informe um nome válido.")
        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        valor = valor.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valor):
            raise ValueError("Informe um e-mail válido.")
        return valor

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        if not cpf_valido(valor):
            raise ValueError("Informe um CPF válido.")
        return somente_digitos(valor)

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        digitos = somente_digitos(valor)
        if not 10 <= len(digitos) <= 15:
            raise ValueError("Informe um telefone válido.")
        return digitos

    @field_validator("data")
    @classmethod
    def validar_data(cls, valor: str) -> str:
        try:
            data = datetime.strptime(valor, "%d/%m/%Y").date()
        except ValueError as erro:
            raise ValueError("Informe uma data válida no formato DD/MM/AAAA.") from erro
        return data.isoformat()


@router.post("/integracao")
def demonstrar_integracao(dados: DemonstracaoEntrada) -> dict[str, object]:
    """Valida/processa os dados e consulta o PostgreSQL sem alterar registros."""
    try:
        diagnostico = testar_conexao()
    except (ConnectionError, RuntimeError) as erro:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o PostgreSQL. Verifique se o banco está iniciado e configurado.",
        ) from erro

    return {
        "status": "ok",
        "mensagem": "Dados validados no Python, processados e banco consultado com sucesso.",
        "fluxo": ["React", "FastAPI/Python", "PostgreSQL", "React"],
        "processamento": {
            "nome_normalizado": dados.nome,
            "email_normalizado": dados.email,
            "cpf_digitos": dados.cpf,
            "telefone_digitos": dados.telefone,
            "data_iso": dados.data,
        },
        "banco": {
            "status": "conectado",
            "registros": diagnostico["registros"],
        },
    }


@router.get("/erro/{tipo}")
def demonstrar_erro(tipo: str) -> dict[str, str]:
    """Gera falhas previsíveis para demonstrar o tratamento visual no frontend."""
    ambiente = (os.getenv("APP_ENV") or "development").strip().lower()
    if ambiente not in {"development", "dev", "test"}:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")

    if tipo == "acesso":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado de forma controlada. A interface tratou o erro sem expor detalhes internos.",
        )

    if tipo == "servico":
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível. A interface pode orientar o usuário a tentar novamente.",
        )

    raise HTTPException(status_code=400, detail="Tipo de demonstração de erro inválido.")
