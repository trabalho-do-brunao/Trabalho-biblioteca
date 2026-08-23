"""Interface de envio de WhatsApp desacoplada do provedor concreto."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import requests
from dotenv import load_dotenv

load_dotenv()


class WhatsAppError(RuntimeError):
    """Erro de envio ou comunicação com o provedor de WhatsApp."""


@dataclass(frozen=True)
class ResultadoEnvio:
    provedor: str
    identificador_externo: str | None = None


class ProvedorWhatsApp(Protocol):
    """Contrato mínimo que qualquer integração de WhatsApp deve cumprir."""

    def enviar(self, telefone: str, mensagem: str) -> ResultadoEnvio:
        """Envia uma mensagem e retorna os dados do provedor."""


class BaileysHttpProvider:
    """Chama o pequeno serviço Node.js local responsável pelo Baileys."""

    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        self.base_url = (
            base_url
            or os.getenv("WHATSAPP_SERVICE_URL")
            or "http://127.0.0.1:3001"
        ).rstrip("/")
        self.timeout = timeout

    def enviar(self, telefone: str, mensagem: str) -> ResultadoEnvio:
        numero = "".join(caractere for caractere in str(telefone) if caractere.isdigit())
        texto = str(mensagem).strip()

        if len(numero) < 10 or len(numero) > 15:
            raise WhatsAppError("Telefone inválido para envio pelo WhatsApp.")
        if not texto:
            raise WhatsAppError("A mensagem não pode ficar vazia.")

        try:
            resposta = requests.post(
                f"{self.base_url}/send",
                json={"phone": numero, "message": texto},
                timeout=self.timeout,
            )
        except requests.Timeout as erro:
            raise WhatsAppError("O serviço local do WhatsApp excedeu o tempo de resposta.") from erro
        except requests.ConnectionError as erro:
            raise WhatsAppError(
                "Não foi possível conectar ao serviço local do WhatsApp. "
                "Verifique se o serviço Node.js está em execução."
            ) from erro
        except requests.RequestException as erro:
            raise WhatsAppError(f"Falha ao chamar o serviço local do WhatsApp: {erro}") from erro

        try:
            dados = resposta.json()
        except ValueError:
            dados = {}

        if not resposta.ok or not dados.get("ok"):
            detalhe = dados.get("error") or f"HTTP {resposta.status_code}"
            raise WhatsAppError(f"O envio pelo WhatsApp falhou: {detalhe}")

        return ResultadoEnvio(
            provedor=str(dados.get("provider") or "baileys"),
            identificador_externo=(
                str(dados["message_id"]) if dados.get("message_id") else None
            ),
        )


class ProvedorSimulado:
    """Provedor sem rede usado para validar o fluxo sem enviar mensagens reais."""

    def __init__(self, falhar_se_contem: str | None = None) -> None:
        self.falhar_se_contem = falhar_se_contem
        self.quantidade_envios = 0

    def enviar(self, telefone: str, mensagem: str) -> ResultadoEnvio:
        self.quantidade_envios += 1

        if self.falhar_se_contem and self.falhar_se_contem in mensagem:
            raise WhatsAppError("Falha simulada para teste de continuidade.")

        return ResultadoEnvio(
            provedor="simulado",
            identificador_externo=f"simulado-{self.quantidade_envios}",
        )


def obter_provedor_whatsapp() -> ProvedorWhatsApp:
    """Monta o provedor configurado sem espalhar detalhes dele pela aplicação."""
    provedor = (os.getenv("WHATSAPP_PROVIDER") or "baileys").strip().lower()

    if provedor == "baileys":
        return BaileysHttpProvider()
    if provedor == "simulado":
        return ProvedorSimulado()

    raise WhatsAppError(f"Provedor de WhatsApp não suportado: {provedor}.")
