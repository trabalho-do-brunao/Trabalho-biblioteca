"""Histórico de auditoria; proteção administrativa aplicada em app/api.py."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.repositories.consulta_auditoria import listar_eventos

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])


@router.get("/eventos")
def consultar_eventos(
    limite: int = Query(default=50, ge=1, le=100),
    deslocamento: int = Query(default=0, ge=0),
    acao: str | None = Query(default=None, max_length=80),
    entidade: str | None = Query(default=None, max_length=60),
    entidade_id: int | None = Query(default=None, ge=1),
) -> dict[str, object]:
    """Lista eventos sem expor dados pessoais dos usuários afetados."""
    try:
        return listar_eventos(
            limite=limite, deslocamento=deslocamento,
            acao=acao, entidade=entidade, entidade_id=entidade_id,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except ConnectionError as erro:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from erro
    except Exception as erro:
        raise HTTPException(status_code=500, detail="Não foi possível consultar a auditoria.") from erro
