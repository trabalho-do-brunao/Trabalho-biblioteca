"""Contrato de estados operacionais para mensagens WhatsApp.

O status legado continua sendo persistido em mensagens.status. Este módulo
traduz o estado conhecido em uma explicação segura para a interface, sem
confundir aceitação pelo provedor com entrega ao destinatário.
"""
from __future__ import annotations

STATUS_OPERACIONAIS = {
    "pendente": ("Aguardando envio", "Mensagem registrada, ainda não enviada ao provedor."),
    "enviado": ("Enviado ao provedor", "O provedor aceitou o envio; entrega e leitura não estão confirmadas."),
    "recebido": ("Recebida pelo sistema", "Mensagem de entrada registrada no BiblioAvisa."),
    "falha": ("Falha no envio", "O envio falhou; consulte os logs para investigar a causa."),
}

def descrever_status(status: str) -> dict[str, object]:
    """Normaliza somente os quatro estados persistidos no banco atual."""
    chave = str(status or "").strip().lower()
    if chave not in STATUS_OPERACIONAIS:
        return {"codigo": "desconhecido", "rotulo": "Estado desconhecido",
                "descricao": "Estado não reconhecido.", "entrega_confirmada": False}
    rotulo, descricao = STATUS_OPERACIONAIS[chave]
    return {"codigo": chave, "rotulo": rotulo, "descricao": descricao,
            "entrega_confirmada": False}

def enriquecer_mensagem(mensagem: dict[str, object]) -> dict[str, object]:
    return {**mensagem, "status_operacional": descrever_status(str(mensagem.get("status") or ""))}
