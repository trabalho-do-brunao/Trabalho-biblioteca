"""Inicia os serviços locais do BiblioAvisa em um único terminal."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
WHATSAPP_DIR = PROJECT_ROOT / "whatsapp_service"
NODE_MODULES = WHATSAPP_DIR / "node_modules"
SERVER_JS = WHATSAPP_DIR / "server.js"
LOG_FILTER_JS = WHATSAPP_DIR / "silenciar_logs.js"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.webhooks.whatsapp import criar_servidor


def _env_ativo(nome: str, padrao: str = "false") -> bool:
    return str(os.getenv(nome, padrao)).strip().lower() in {"1", "true", "yes", "sim"}


def _validar_configuracao() -> tuple[bool, str]:
    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. Execute setup.bat ou copie .env.example para .env."
        )

    load_dotenv(ENV_PATH)

    inbound_ativo = _env_ativo("WHATSAPP_INBOUND_ENABLED")
    telefone_permitido = "".join(
        caractere
        for caractere in str(os.getenv("WHATSAPP_INBOUND_ALLOWED_PHONE", ""))
        if caractere.isdigit()
    )

    if inbound_ativo:
        if not telefone_permitido:
            raise RuntimeError(
                "WHATSAPP_INBOUND_ENABLED=true exige WHATSAPP_INBOUND_ALLOWED_PHONE "
                "configurado no .env. Isso evita que o bot processe contatos não autorizados."
            )
        if not 10 <= len(telefone_permitido) <= 15:
            raise RuntimeError(
                "WHATSAPP_INBOUND_ALLOWED_PHONE inválido. Informe somente dígitos com DDI e DDD."
            )

    return inbound_ativo, telefone_permitido


def _localizar_node() -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError(
            "Node.js não foi encontrado no PATH. Instale/configure o Node.js antes de iniciar o Baileys."
        )

    if not SERVER_JS.exists() or not LOG_FILTER_JS.exists():
        raise RuntimeError("Arquivos do serviço Baileys não foram encontrados em whatsapp_service/.")

    if not NODE_MODULES.exists():
        raise RuntimeError(
            "Dependências do WhatsApp ainda não foram instaladas. "
            "Execute uma vez: cd whatsapp_service; npm install"
        )

    return node


def _ler_saida(processo: subprocess.Popen[str]) -> None:
    assert processo.stdout is not None
    for linha in processo.stdout:
        texto = linha.rstrip()
        if texto:
            print(f"[BAILEYS] {texto}", flush=True)


def _encerrar_processo(processo: subprocess.Popen[str] | None) -> None:
    if processo is None or processo.poll() is not None:
        return

    try:
        processo.terminate()
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait(timeout=2)


def main() -> int:
    try:
        inbound_ativo, telefone_permitido = _validar_configuracao()
        node = _localizar_node()
        servidor = criar_servidor()
    except (RuntimeError, OSError, ValueError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    host, porta = servidor.server_address
    baileys_host = (os.getenv("BAILEYS_SERVICE_HOST") or "127.0.0.1").strip()
    baileys_porta = (os.getenv("BAILEYS_SERVICE_PORT") or "3001").strip()

    thread_webhook = threading.Thread(
        target=servidor.serve_forever,
        name="biblioavisa-webhook",
        daemon=True,
    )
    thread_webhook.start()

    print("=== BiblioAvisa - Serviços locais ===")
    print(f"[WEBHOOK] [OK] http://{host}:{porta}/webhook/whatsapp")
    print(f"[BAILEYS] [INFO] Iniciando serviço WhatsApp em http://{baileys_host}:{baileys_porta}")
    print(
        "[SEGURANÇA] Recebimento automático: "
        + ("ATIVADO" if inbound_ativo else "DESATIVADO")
    )
    if inbound_ativo:
        print("[SEGURANÇA] Filtro de telefone: ATIVO")
    elif telefone_permitido:
        print("[SEGURANÇA] Telefone autorizado configurado, mas recebimento está desativado.")
    print("[INFO] Pressione Ctrl + C para encerrar todos os serviços.\n")

    processo_baileys: subprocess.Popen[str] | None = None

    try:
        processo_baileys = subprocess.Popen(
            [node, "--import", "./silenciar_logs.js", "server.js"],
            cwd=WHATSAPP_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        thread_saida = threading.Thread(
            target=_ler_saida,
            args=(processo_baileys,),
            name="biblioavisa-baileys-log",
            daemon=True,
        )
        thread_saida.start()

        while True:
            codigo = processo_baileys.poll()
            if codigo is not None:
                if codigo == 0:
                    print("[INFO] Serviço Baileys foi encerrado.")
                    return 0
                print(f"[ERRO] Serviço Baileys encerrou inesperadamente com código {codigo}.")
                return codigo or 1

            if not thread_webhook.is_alive():
                print("[ERRO] Webhook foi encerrado inesperadamente.")
                return 1

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[INFO] Encerrando BiblioAvisa...")
        return 0
    finally:
        servidor.shutdown()
        servidor.server_close()
        _encerrar_processo(processo_baileys)
        print("[OK] Serviços encerrados.")


if __name__ == "__main__":
    raise SystemExit(main())
