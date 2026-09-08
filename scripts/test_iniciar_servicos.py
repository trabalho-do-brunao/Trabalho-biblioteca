"""Teste isolado da verificação de portas do inicializador local."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.iniciar_servicos import _porta_em_uso, _verificar_portas_livres


def abrir_servidor_teste() -> tuple[socket.socket, int]:
    """Abre uma porta efêmera exclusiva para uma única verificação."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(5)
    return servidor, int(servidor.getsockname()[1])


def main() -> int:
    # Usa um socket exclusivo para testar _porta_em_uso. No Windows, reutilizar
    # o mesmo listener em várias conexões sem accept() pode saturar a fila.
    servidor_deteccao, porta_deteccao = abrir_servidor_teste()
    try:
        assert _porta_em_uso(
            "127.0.0.1", porta_deteccao
        ), "A porta em escuta deveria ser detectada como ocupada."
        print("[OK] Porta em uso é detectada")
    finally:
        servidor_deteccao.close()

    # Uma nova porta é usada para validar a mensagem de bloqueio, evitando que
    # a conexão do teste anterior interfira no resultado em Windows/Linux.
    servidor_bloqueio, porta_bloqueio = abrir_servidor_teste()
    try:
        try:
            _verificar_portas_livres(
                [
                    (
                        "Serviço de teste",
                        "127.0.0.1",
                        porta_bloqueio,
                        "Feche o processo de teste.",
                    )
                ]
            )
        except RuntimeError as erro:
            mensagem = str(erro)
            assert str(porta_bloqueio) in mensagem
            assert "Serviço de teste" in mensagem
        else:
            raise AssertionError("A verificação deveria bloquear uma porta ocupada.")

        print("[OK] Mensagem identifica porta e serviço em conflito")
    finally:
        servidor_bloqueio.close()

    assert not _porta_em_uso(
        "127.0.0.1", porta_bloqueio
    ), "Após fechar o socket, a porta deveria estar livre."
    print("[OK] Porta liberada deixa de ser reportada como ocupada")

    print("\n=== Teste do inicializador passou ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
