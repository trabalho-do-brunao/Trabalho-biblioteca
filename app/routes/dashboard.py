"""Rotas HTTP para a visão consolidada do dashboard."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.dashboard import obter_dashboard


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def consultar_dashboard(
    dias_proximos: int = Query(default=2, ge=0, le=30),
    limite: int = Query(default=10, ge=1, le=100),
) -> dict[str, object]:
    """Retorna indicadores e empréstimos que exigem atenção."""
    try:
        return obter_dashboard(dias_proximos=dias_proximos, limite=limite)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        ) from erro
    except ConnectionError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o banco de dados. Tente novamente em instantes.",
        ) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível carregar os dados do dashboard.",
        ) from erro
