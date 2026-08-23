"""Envia uma única mensagem real para validar a integração local com Baileys.

Este script não grava o número no repositório nem processa a fila automática.
Use somente com um número que você controla ou que autorizou o teste.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.whatsapp import BaileysHttpProvider, WhatsAppError


def normalizar_telefone(valor: str) -> str:
    numero = "".join(caractere for caractere in valor if caractere.isdigit())
    if len(numero) < 10 or len(numero) > 15:
        raise ValueError("Informe o telefone com DDI e DDD, usando de 10 a 15 dígitos.")
    return numero


def main() -> int:
    print("=== Teste real controlado do WhatsApp ===\n")
    print("Este teste enviará exatamente UMA mensagem pelo Baileys.")
    print("Use somente um número seu ou que tenha autorizado o teste.\n")

    try:
        telefone = normalizar_telefone(input("Número com DDI e DDD (ex.: 5542...): ").strip())
    except ValueError as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    mensagem = "Teste do BiblioAvisa: integração com WhatsApp funcionando."

    print("\nMensagem que será enviada:")
    print(mensagem)
    print(f"Destino: {telefone}")

    confirmacao = input("\nDigite SIM para enviar uma única mensagem: ").strip().upper()
    if confirmacao != "SIM":
        print("\n[INFO] Envio cancelado. Nenhuma mensagem foi enviada.")
        return 0

    try:
        resultado = BaileysHttpProvider().enviar(telefone, mensagem)
    except WhatsAppError as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    print("\n[OK] Mensagem aceita pelo serviço Baileys.")
    print(f"[OK] Provedor: {resultado.provedor}")
    print(f"[OK] Message ID: {resultado.identificador_externo or '(não retornado)'}")
    print("\nConfirme no aparelho de destino se a mensagem chegou.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
