"""Inicia os serviços locais do BiblioAvisa em um único terminal."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"
WHATSAPP_DIR = PROJECT_ROOT / "whatsapp_service"
WHATSAPP_NODE_MODULES = WHATSAPP_DIR / "node_modules"
SERVER_JS = WHATSAPP_DIR / "server.js"
LOG_FILTER_JS = WHATSAPP_DIR / "silenciar_logs.js"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_NODE_MODULES = FRONTEND_DIR / "node_modules"
FRONTEND_PACKAGE_JSON = FRONTEND_DIR / "package.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.webhooks.whatsapp import criar_servidor


def _carregar_env_local() -> dict[str, str]:
    """Carrega somente o .env local e o torna a fonte oficial desta execução."""
    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. Execute setup.bat ou copie .env.example para .env."
        )

    valores_brutos = dotenv_values(ENV_PATH)
    valores = {
        str(chave): str(valor)
        for chave, valor in valores_brutos.items()
        if chave and valor is not None
    }

    for chave, valor in valores.items():
        os.environ[chave] = valor

    os.environ["WHATSAPP_INBOUND_ENABLED"] = valores.get(
        "WHATSAPP_INBOUND_ENABLED", "false"
    )
    os.environ["AUTOMACAO_ENABLED"] = valores.get("AUTOMACAO_ENABLED", "false")
    os.environ.pop("WHATSAPP_INBOUND_ALLOWED_PHONE", None)

    return valores


def _avisar_env_desatualizado(valores: dict[str, str]) -> None:
    """Avisa quando o .env local não possui chaves presentes no modelo atual."""
    if not ENV_EXAMPLE_PATH.exists():
        return

    exemplo = dotenv_values(ENV_EXAMPLE_PATH)
    chaves_modelo = {str(chave) for chave in exemplo if chave}
    faltando = sorted(chaves_modelo.difference(valores))

    if not faltando:
        return

    print(
        "[AVISO] Seu .env local está desatualizado em relação ao .env.example. "
        "Nenhum segredo será sobrescrito automaticamente."
    )
    print("[AVISO] Chaves ausentes: " + ", ".join(faltando))
    print(
        "[AVISO] Copie apenas as chaves que faltam do .env.example para o .env "
        "e preencha somente os valores locais necessários.\n"
    )


def _env_ativo(nome: str, padrao: str = "false") -> bool:
    return str(os.getenv(nome, padrao)).strip().lower() in {"1", "true", "yes", "sim", "on"}


def _porta_configurada(nome: str, padrao: int) -> int:
    texto = str(os.getenv(nome, str(padrao))).strip()
    try:
        porta = int(texto)
    except ValueError as erro:
        raise RuntimeError(f"{nome} deve conter uma porta numérica válida.") from erro

    if porta < 1 or porta > 65535:
        raise RuntimeError(f"{nome} deve estar entre 1 e 65535.")
    return porta


def _porta_em_uso(host: str, porta: int) -> bool:
    """Verifica se já existe um processo aceitando conexões na porta informada."""
    host_teste = str(host or "").strip()
    if host_teste in {"", "0.0.0.0", "::"}:
        host_teste = "127.0.0.1"

    try:
        with socket.create_connection((host_teste, porta), timeout=0.25):
            return True
    except (ConnectionRefusedError, TimeoutError, socket.timeout):
        return False
    except OSError:
        # Se o host configurado não puder ser usado para uma conexão de teste,
        # a criação real do serviço ainda produzirá o erro correspondente.
        return False


def _verificar_portas_livres(servicos: list[tuple[str, str, int, str]]) -> None:
    ocupadas: list[str] = []

    for nome, host, porta, dica in servicos:
        if _porta_em_uso(host, porta):
            ocupadas.append(
                f"[ERRO] Porta {porta} ocupada ({nome}, {host}:{porta}). {dica}"
            )

    if not ocupadas:
        return

    raise RuntimeError(
        "Não foi possível iniciar o BiblioAvisa porque existem portas em uso:\n"
        + "\n".join(ocupadas)
        + "\nFeche as instâncias antigas e execute run.bat novamente."
    )


def _localizar_node() -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError(
            "Node.js não foi encontrado no PATH. Instale/configure o Node.js antes de iniciar o Baileys."
        )

    if not SERVER_JS.exists() or not LOG_FILTER_JS.exists():
        raise RuntimeError("Arquivos do serviço Baileys não foram encontrados em whatsapp_service/.")

    if not WHATSAPP_NODE_MODULES.exists():
        raise RuntimeError(
            "Dependências do WhatsApp ainda não foram instaladas. "
            "Execute novamente setup.bat para preparar o ambiente."
        )

    return node


def _localizar_frontend() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise RuntimeError("npm não foi encontrado no PATH. Execute setup.bat após instalar o Node.js.")

    if not FRONTEND_PACKAGE_JSON.exists():
        raise RuntimeError("frontend/package.json não foi encontrado.")

    if not FRONTEND_NODE_MODULES.exists():
        raise RuntimeError(
            "Dependências do frontend ainda não foram instaladas. Execute novamente setup.bat."
        )

    return npm


def _ler_saida(processo: subprocess.Popen[str], prefixo: str) -> None:
    assert processo.stdout is not None
    for linha in processo.stdout:
        texto = linha.rstrip()
        if texto:
            print(f"[{prefixo}] {texto}", flush=True)


def _encerrar_processo(processo: subprocess.Popen[str] | None) -> None:
    if processo is None or processo.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    try:
        processo.terminate()
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait(timeout=2)


def _iniciar_processo(
    comando: list[str],
    *,
    cwd: Path,
    prefixo: str,
) -> tuple[subprocess.Popen[str], threading.Thread]:
    processo = subprocess.Popen(
        comando,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=os.environ.copy(),
    )
    thread = threading.Thread(
        target=_ler_saida,
        args=(processo, prefixo),
        name=f"biblioavisa-{prefixo.lower()}-log",
        daemon=True,
    )
    thread.start()
    return processo, thread


def _processo_encerrou(processo: subprocess.Popen[str] | None, nome: str) -> int | None:
    if processo is None:
        return None

    codigo = processo.poll()
    if codigo is None:
        return None

    print(f"[ERRO] {nome} encerrou inesperadamente com código {codigo}.")
    return codigo or 1


def main() -> int:
    try:
        valores_env = _carregar_env_local()
        _avisar_env_desatualizado(valores_env)
        inbound_ativo = _env_ativo("WHATSAPP_INBOUND_ENABLED")
        automacao_ativa = _env_ativo("AUTOMACAO_ENABLED")
        node = _localizar_node()
        npm = _localizar_frontend()

        api_host = "127.0.0.1"
        api_porta = 8000
        frontend_host = "127.0.0.1"
        frontend_porta = 5173
        webhook_host = (os.getenv("WHATSAPP_WEBHOOK_HOST") or "127.0.0.1").strip()
        webhook_porta = _porta_configurada("WHATSAPP_WEBHOOK_PORT", 3002)
        baileys_host = (os.getenv("BAILEYS_SERVICE_HOST") or "127.0.0.1").strip()
        baileys_porta = _porta_configurada("BAILEYS_SERVICE_PORT", 3001)

        _verificar_portas_livres(
            [
                (
                    "API FastAPI",
                    api_host,
                    api_porta,
                    "Normalmente isso indica outra API/BiblioAvisa ainda aberta.",
                ),
                (
                    "Frontend React/Vite",
                    frontend_host,
                    frontend_porta,
                    "Feche outro Vite ou terminal antigo do frontend.",
                ),
                (
                    "Webhook WhatsApp",
                    webhook_host,
                    webhook_porta,
                    "Feche outro webhook ou ajuste WHATSAPP_WEBHOOK_PORT no .env.",
                ),
                (
                    "Baileys/WhatsApp",
                    baileys_host,
                    baileys_porta,
                    "Feche outro Baileys ou ajuste BAILEYS_SERVICE_PORT no .env.",
                ),
            ]
        )

        servidor = criar_servidor()
    except (RuntimeError, OSError, ValueError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    host, porta = servidor.server_address
    automacao_hora = (os.getenv("AUTOMACAO_HORA") or "08:00").strip()
    automacao_timezone = (os.getenv("AUTOMACAO_TIMEZONE") or "America/Sao_Paulo").strip()

    thread_webhook = threading.Thread(
        target=servidor.serve_forever,
        name="biblioavisa-webhook",
        daemon=True,
    )
    thread_webhook.start()

    print("=== BiblioAvisa - Serviços locais ===")
    print(f"[FRONTEND] [INFO] http://{frontend_host}:{frontend_porta}/")
    print(f"[API] [INFO] http://{api_host}:{api_porta}/api/health")
    print(f"[WEBHOOK] [OK] http://{host}:{porta}/webhook/whatsapp")
    print(f"[BAILEYS] [INFO] Iniciando serviço WhatsApp em http://{baileys_host}:{baileys_porta}")
    print(
        "[SEGURANÇA] Recebimento automático: "
        + ("ATIVADO" if inbound_ativo else "DESATIVADO")
    )
    if inbound_ativo:
        print("[SEGURANÇA] Autorização de respostas: usuários ativos do PostgreSQL")

    if automacao_ativa:
        print(
            f"[AUTOMAÇÃO] [INFO] Rotina diária ATIVADA para {automacao_hora} "
            f"({automacao_timezone})"
        )
    else:
        print("[AUTOMAÇÃO] [INFO] Rotina diária DESATIVADA")

    print("[INFO] Pressione Ctrl + C para encerrar todos os serviços.\n")

    processo_api: subprocess.Popen[str] | None = None
    processo_frontend: subprocess.Popen[str] | None = None
    processo_baileys: subprocess.Popen[str] | None = None
    processo_automacao: subprocess.Popen[str] | None = None

    try:
        processo_api, _ = _iniciar_processo(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.api:app",
                "--host",
                api_host,
                "--port",
                str(api_porta),
            ],
            cwd=PROJECT_ROOT,
            prefixo="API",
        )

        time.sleep(0.4)

        processo_frontend, _ = _iniciar_processo(
            [npm, "run", "dev", "--", "--host", frontend_host, "--port", str(frontend_porta)],
            cwd=FRONTEND_DIR,
            prefixo="FRONTEND",
        )

        processo_baileys, _ = _iniciar_processo(
            [node, "--import", "./silenciar_logs.js", "server.js"],
            cwd=WHATSAPP_DIR,
            prefixo="BAILEYS",
        )

        if automacao_ativa:
            processo_automacao, _ = _iniciar_processo(
                [sys.executable, "-m", "app.main", "--agendar"],
                cwd=PROJECT_ROOT,
                prefixo="AUTOMAÇÃO",
            )

        while True:
            for processo, nome in (
                (processo_api, "API FastAPI"),
                (processo_frontend, "Frontend React/Vite"),
                (processo_baileys, "Serviço Baileys"),
                (processo_automacao, "Automação diária"),
            ):
                codigo = _processo_encerrou(processo, nome)
                if codigo is not None:
                    return codigo

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
        _encerrar_processo(processo_automacao)
        _encerrar_processo(processo_baileys)
        _encerrar_processo(processo_frontend)
        _encerrar_processo(processo_api)
        print("[OK] Serviços encerrados.")


if __name__ == "__main__":
    raise SystemExit(main())
