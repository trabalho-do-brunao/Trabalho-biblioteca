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
    que uma configuração antiga do terminal habilite o listener sem aparecer no .env,
    as opções de segurança recebem explicitamente o valor do arquivo ou o padrão seguro.
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

    # O .env local tem precedência sobre valores antigos herdados do terminal.
    for chave, valor in valores.items():
        os.environ[chave] = valor

    # Segurança: ausência destas opções nunca herda um `true` antigo do PowerShell.
    os.environ["WHATSAPP_INBOUND_ENABLED"] = valores.get(
        "WHATSAPP_INBOUND_ENABLED", "false"
    )
    os.environ["WHATSAPP_INBOUND_ALLOWED_PHONE"] = valores.get(
        "WHATSAPP_INBOUND_ALLOWED_PHONE", ""
    )

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
    return str(os.getenv(nome, padrao)).strip().lower() in {"1", "true", "yes", "sim"}


def _validar_configuracao(valores: dict[str, str]) -> tuple[bool, str]:
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
        valores_env = _carregar_env_local()
        _avisar_env_desatualizado(valores_env)
        inbound_ativo, telefone_permitido = _validar_configuracao(valores_env)
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
            env=os.environ.copy(),
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
