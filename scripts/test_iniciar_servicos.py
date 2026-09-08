"""Teste isolado da verificação de portas do inicializador local."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.iniciar_servicos import _porta_em_uso, _verificar_portas_livres


def main() -> int:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    porta = int(servidor.getsockname()[1])

    try:
        assert _porta_em_uso("127.0.0.1", porta), "A porta em escuta deveria ser detectada como ocupada."
        print("[OK] Porta em uso é detectada")

        try:
            _verificar_portas_livres(
                [
                    (
                        "Serviço de teste",
                        "127.0.0.1",
                        porta,
                        "Feche o processo de teste.",
                    )
                ]
            )
        except RuntimeError as erro:
            mensagem = str(erro)
            assert str(porta) in mensagem
            assert "Serviço de teste" in mensagem
        else:
            raise AssertionError("A verificação deveria bloquear uma porta ocupada.")

        print("[OK] Mensagem identifica porta e serviço em conflito")
    finally:
        servidor.close()

    assert not _porta_em_uso("127.0.0.1", porta), "Após fechar o socket, a porta deveria estar livre."
    print("[OK] Porta liberada deixa de ser reportada como ocupada")

    print("\n=== Teste do inicializador passou ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
