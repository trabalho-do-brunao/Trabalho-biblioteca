"""Processamento da fila de avisos pendentes para envio pelo WhatsApp."""

from __future__ import annotations

from collections.abc import Iterable

from app.repositories.mensagens import (
    buscar_mensagens_pendentes,
    marcar_mensagem_enviada,
    marcar_mensagem_falha,
)
from app.services.whatsapp import ProvedorWhatsApp, obter_provedor_whatsapp


def processar_mensagens_pendentes(
    provedor: ProvedorWhatsApp | None = None,
    limite: int = 100,
    mensagem_ids: Iterable[int] | None = None,
) -> list[dict[str, object]]:
    """Envia mensagens pendentes sem deixar uma falha interromper as demais."""
    cliente = provedor or obter_provedor_whatsapp()
    mensagens = buscar_mensagens_pendentes(
        limite=limite,
        mensagem_ids=mensagem_ids,
    )
    resultados: list[dict[str, object]] = []

    for item in mensagens:
        mensagem_id = int(item["id"])

        try:
            envio = cliente.enviar(
                telefone=str(item["usuario_telefone"]),
                mensagem=str(item["mensagem"]),
            )
            atualizado = marcar_mensagem_enviada(
                mensagem_id,
                envio.identificador_externo,
            )
            resultados.append(
                {
                    "mensagem_id": mensagem_id,
                    "status": "enviado",
                    "provedor": envio.provedor,
                    "identificador_externo": atualizado["identificador_externo"],
                }
            )
        except Exception as erro:
            try:
                marcar_mensagem_falha(mensagem_id)
            except Exception as erro_persistencia:
                resultados.append(
                    {
                        "mensagem_id": mensagem_id,
                        "status": "erro_persistencia",
                        "erro": str(erro_persistencia),
                        "erro_original": str(erro),
                    }
                )
                continue

            resultados.append(
                {
                    "mensagem_id": mensagem_id,
                    "status": "falha",
                    "erro": str(erro),
                }
            )

    return resultados
