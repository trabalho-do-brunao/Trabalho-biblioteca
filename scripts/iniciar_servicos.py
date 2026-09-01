"""Inicia os serviços locais do BiblioAvisa em um único terminal."""

from __future__ import annotations

import os
import shutil
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
NODE_MODULES = WHATSAPP_DIR / "node_modules"
SERVER_JS = WHATSAPP_DIR / "server.js"
LOG_FILTER_JS = WHATSAPP_DIR / "silenciar_logs.js"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.webhooks.whatsapp import criar_servidor


def _carregar_env_local() -> dict[str, str]:
    """Carrega somente o .env local e o torna a fonte oficial desta execução.

    Variáveis herdadas do PowerShell podem sobreviver por toda a sessão. Para evitar
    que uma configuração antiga habilite comportamentos automáticos sem aparecer no
    arquivo local, opções sensíveis recebem explicitamente o valor do `.env` ou um
    padrão seguro desligado.
    """
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

    # A antiga allowlist por telefone não faz mais parte da configuração.
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
            "Execute novamente setup.bat para preparar o ambiente."
        )

    return node


def _ler_saida(processo: subprocess.Popen[str], prefixo: str) -> None:
    assert processo.stdout is not None
    for linha in processo.stdout:
        texto = linha.rstrip()
        if texto:
            print(f"[{prefixo}] {texto}", flush=True)


def _encerrar_processo(processo: subprocess.Popen[str] | None) -> None:
    if processo is None or processo.poll() is not None:
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


def main() -> int:
    try:
        valores_env = _carregar_env_local()
        _avisar_env_desatualizado(valores_env)
        inbound_ativo = _env_ativo("WHATSAPP_INBOUND_ENABLED")
        automacao_ativa = _env_ativo("AUTOMACAO_ENABLED")
        node = _localizar_node()
        servidor = criar_servidor()
    except (RuntimeError, OSError, ValueError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    host, porta = servidor.server_address
    baileys_host = (os.getenv("BAILEYS_SERVICE_HOST") or "127.0.0.1").strip()
    baileys_porta = (os.getenv("BAILEYS_SERVICE_PORT") or "3001").strip()
    automacao_hora = (os.getenv("AUTOMACAO_HORA") or "08:00").strip()
    automacao_timezone = (os.getenv("AUTOMACAO_TIMEZONE") or "America/Sao_Paulo").strip()

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
        print("[SEGURANÇA] Autorização de respostas: usuários ativos do PostgreSQL")

    if automacao_ativa:
        print(
            f"[AUTOMAÇÃO] [INFO] Rotina diária ATIVADA para {automacao_hora} "
            f"({automacao_timezone})"
        )
    else:
        print("[AUTOMAÇÃO] [INFO] Rotina diária DESATIVADA")

    print("[INFO] Pressione Ctrl + C para encerrar todos os serviços.\n")

    processo_baileys: subprocess.Popen[str] | None = None
    processo_automacao: subprocess.Popen[str] | None = None

    try:
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
            codigo_baileys = processo_baileys.poll()
            if codigo_baileys is not None:
                if codigo_baileys == 0:
                    print("[INFO] Serviço Baileys foi encerrado.")
                    return 0
                print(
                    f"[ERRO] Serviço Baileys encerrou inesperadamente com código {codigo_baileys}."
                )
                return codigo_baileys or 1

            if processo_automacao is not None:
                codigo_automacao = processo_automacao.poll()
                if codigo_automacao is not None:
                    print(
                        "[ERRO] Processo da automação diária foi encerrado "
                        f"inesperadamente com código {codigo_automacao}."
                    )
                    return codigo_automacao or 1

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
        print("[OK] Serviços encerrados.")


if __name__ == "__main__":
    raise SystemExit(main())
