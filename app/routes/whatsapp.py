"""Rotas HTTP para acompanhamento operacional do WhatsApp."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.whatsapp import listar_historico_whatsapp, obter_resumo_whatsapp


router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

StatusMensagem = Literal["pendente", "enviado", "recebido", "falha"]
DirecaoMensagem = Literal["enviada", "recebida"]
TipoMensagem = Literal[
    "aviso_2_dias",
    "aviso_vencimento",
    "aviso_atraso",
    "solicitacao_renovacao",
    "confirmacao_renovacao",
    "recusa_renovacao",
    "consulta",
    "outro",
]


def _erro_operacao(erro: Exception) -> HTTPException:
    if isinstance(erro, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))
    if isinstance(erro, ConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o banco de dados. Tente novamente em instantes.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Não foi possível consultar o histórico do WhatsApp.",
    )


@router.get("/mensagens")
def listar_mensagens(
    status_mensagem: StatusMensagem | None = Query(default=None, alias="status"),
    tipo: TipoMensagem | None = Query(default=None),
    direcao: DirecaoMensagem | None = Query(default=None),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    busca: str = Query(default="", max_length=200),
    limite: int = Query(default=250, ge=1, le=500),
) -> dict[str, object]:
    """Lista mensagens registradas, com filtros operacionais e dados de renovação relacionados."""
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial não pode ser posterior à data final.",
        )

    try:
        mensagens = listar_historico_whatsapp(
            status=status_mensagem,
            tipo=tipo,
            direcao=direcao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            busca=busca,
            limite=limite,
        )
        resumo = obter_resumo_whatsapp()
        return {
            "mensagens": mensagens,
            "total_filtrado": len(mensagens),
            "resumo": resumo,
        }
    except HTTPException:
        raise
    except Exception as erro:
        raise _erro_operacao(erro) from erro
