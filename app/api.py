"""API HTTP do BiblioAvisa para consumo pelo frontend React."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


load_dotenv(override=False)
logger = logging.getLogger("biblioavisa.api")

app = FastAPI(
    title="BiblioAvisa API",
    version="0.1.0",
    description="Camada HTTP do BiblioAvisa. As regras de negócio permanecem nos serviços Python.",
)

origens_padrao = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
origens_env = [
    origem.strip()
    for origem in (os.getenv("FRONTEND_ORIGINS") or "").split(",")
    if origem.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_env or origens_padrao,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Retorna validações de entrada sem expor detalhes internos do servidor."""
    campos = []
    for erro in exc.errors():
        local = [str(item) for item in erro.get("loc", []) if item not in {"body", "query", "path"}]
        campos.append(
            {
                "field": ".".join(local) or "dados",
                "message": erro.get("msg", "Valor inválido."),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Revise os dados enviados e tente novamente.",
            "errors": campos,
        },
    )


@app.exception_handler(Exception)
async def tratar_erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Evita que stack traces e detalhes internos sejam enviados ao frontend."""
    logger.exception("Erro inesperado na API em %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "O servidor encontrou um problema interno. Tente novamente em instantes."},
    )


@app.get("/api/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Confirma que a API Python está disponível para o frontend."""
    return {
        "status": "ok",
        "service": "BiblioAvisa API",
        "environment": (os.getenv("APP_ENV") or "development").strip(),
    }
