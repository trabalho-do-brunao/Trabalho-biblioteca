"""Rotas HTTP para geração e envio dos relatórios do BiblioAvisa."""

from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from app.services.email_service import (
    EmailConfiguracaoError,
    EmailEnvioError,
    enviar_relatorio_email,
)
from app.services.relatorio import gerar_relatorio_pdf


router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


class PeriodoRelatorio(BaseModel):
    data_inicio: date
    data_fim: date


def _validar_periodo(data_inicio: date, data_fim: date) -> None:
    if data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial não pode ser posterior à data final.",
        )


def _caminho_temporario() -> Path:
    descritor, caminho = tempfile.mkstemp(prefix="biblioavisa_relatorio_", suffix=".pdf")
    os.close(descritor)
    return Path(caminho)


def _apagar_silenciosamente(caminho: Path) -> None:
    try:
        caminho.unlink(missing_ok=True)
    except OSError:
        pass


@router.get("/pdf")
def gerar_pdf(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
) -> FileResponse:
    """Gera o PDF do período e o devolve ao navegador sem persistir arquivo temporário."""
    _validar_periodo(data_inicio, data_fim)
    caminho = _caminho_temporario()

    try:
        gerar_relatorio_pdf(data_inicio, data_fim, caminho)
    except ValueError as erro:
        _apagar_silenciosamente(caminho)
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except ConnectionError as erro:
        _apagar_silenciosamente(caminho)
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o banco de dados para gerar o relatório.",
        ) from erro
    except Exception as erro:
        _apagar_silenciosamente(caminho)
        raise HTTPException(status_code=500, detail="Não foi possível gerar o relatório PDF.") from erro

    nome = f"relatorio_biblioavisa_{data_inicio:%Y%m%d}_{data_fim:%Y%m%d}.pdf"
    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=nome,
        background=BackgroundTask(_apagar_silenciosamente, caminho),
    )


@router.post("/email")
def enviar_email(dados: PeriodoRelatorio) -> dict[str, object]:
    """Gera o relatório e solicita seu envio usando somente a configuração SMTP do backend."""
    _validar_periodo(dados.data_inicio, dados.data_fim)
    caminho = _caminho_temporario()

    try:
        gerar_relatorio_pdf(dados.data_inicio, dados.data_fim, caminho)
        enviar_relatorio_email(caminho)
    except EmailConfiguracaoError as erro:
        raise HTTPException(
            status_code=503,
            detail="O envio por e-mail ainda não está configurado neste ambiente.",
        ) from erro
    except EmailEnvioError as erro:
        raise HTTPException(
            status_code=502,
            detail="O servidor de e-mail não conseguiu concluir o envio. Tente novamente.",
        ) from erro
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except ConnectionError as erro:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o banco de dados para gerar o relatório.",
        ) from erro
    except Exception as erro:
        raise HTTPException(status_code=500, detail="Não foi possível enviar o relatório por e-mail.") from erro
    finally:
        _apagar_silenciosamente(caminho)

    return {
        "mensagem": "Relatório gerado e enviado por e-mail com sucesso.",
        "periodo": {
            "data_inicio": dados.data_inicio,
            "data_fim": dados.data_fim,
        },
    }
