"""Classificação segura de falhas do provedor WhatsApp, sem reenvio automático."""
from __future__ import annotations
from requests.exceptions import ConnectionError as HttpConnectionError, Timeout as HttpTimeout
from app.services.whatsapp import WhatsAppError

CATEGORIAS = {
    "telefone_invalido": ("Telefone inválido", False),
    "mensagem_invalida": ("Mensagem inválida", False),
    "timeout": ("Tempo limite excedido", True),
    "servico_indisponivel": ("Serviço WhatsApp indisponível", True),
    "provedor_rejeitou": ("Provedor recusou o envio", False),
    "falha_desconhecida": ("Falha não classificada", False),
}

def classificar_falha(erro: Exception) -> dict[str, object]:
    """Não revela detalhes da exceção e nunca autoriza reenvio automático."""
    texto = str(erro).casefold() if isinstance(erro, WhatsAppError) else ""
    if "telefone inválido" in texto:
        codigo = "telefone_invalido"
    elif "mensagem não pode ficar vazia" in texto:
        codigo = "mensagem_invalida"
    elif isinstance(erro, HttpTimeout) or "excedeu o tempo" in texto:
        codigo = "timeout"
    elif isinstance(erro, HttpConnectionError) or "não foi possível conectar" in texto:
        codigo = "servico_indisponivel"
    elif isinstance(erro, WhatsAppError) and "envio pelo whatsapp falhou" in texto:
        codigo = "provedor_rejeitou"
    else:
        codigo = "falha_desconhecida"
    rotulo, transitoria = CATEGORIAS[codigo]
    return {
        "codigo": codigo,
        "rotulo": rotulo,
        "potencialmente_transitoria": transitoria,
        "reenvio_automatico_permitido": False,
    }
