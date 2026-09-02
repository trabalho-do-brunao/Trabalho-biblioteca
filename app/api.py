"""API HTTP mínima do BiblioAvisa para consumo pelo frontend React."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(override=False)

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


@app.get("/api/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Confirma que a API Python está disponível para o frontend."""
    return {
        "status": "ok",
        "service": "BiblioAvisa API",
        "environment": (os.getenv("APP_ENV") or "development").strip(),
    }
