"""Fluxo principal e agendamento diário do BiblioAvisa."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from app.automation.enviar_mensagens import processar_mensagens_pendentes
from app.automation.verificar_prazos import verificar_prazos
from app.services.email_service import enviar_relatorio_email
from app.services.relatorio import gerar_relatorio_pdf
from app.services.whatsapp import ProvedorSimulado, ProvedorWhatsApp


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
LOGGER = logging.getLogger("biblioavisa")


@dataclass(frozen=True)
class ConfiguracaoAgendamento:
    ativo: bool
    hora: int
    minuto: int
    timezone: str
    enviar_email: bool
    dias_relatorio: int


def _env_bool(nome: str, padrao: str = "false") -> bool:
    return str(os.getenv(nome, padrao)).strip().lower() in {
        "1",
        "true",
        "yes",
        "sim",
        "on",
    }


def _carregar_env() -> None:
    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. Execute setup.bat antes de iniciar a automação."
        )
    load_dotenv(ENV_PATH, override=True)


def _normalizar_data(valor: date | str | None) -> date:
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError as erro:
            raise ValueError("A data deve estar no formato AAAA-MM-DD.") from erro
    raise ValueError("A data de referência é inválida.")


def carregar_configuracao_agendamento() -> ConfiguracaoAgendamento:
    """Carrega e valida as opções da automação diária definidas no `.env`."""
    _carregar_env()

    hora_texto = (os.getenv("AUTOMACAO_HORA") or "08:00").strip()
    try:
        partes = hora_texto.split(":")
        if len(partes) != 2:
            raise ValueError
        hora = int(partes[0])
        minuto = int(partes[1])
    except ValueError as erro:
        raise ValueError("AUTOMACAO_HORA deve usar o formato HH:MM, por exemplo 08:00.") from erro

    if not 0 <= hora <= 23 or not 0 <= minuto <= 59:
        raise ValueError("AUTOMACAO_HORA possui horário inválido.")

    timezone_nome = (os.getenv("AUTOMACAO_TIMEZONE") or "America/Sao_Paulo").strip()
    try:
        ZoneInfo(timezone_nome)
    except ZoneInfoNotFoundError as erro:
        raise ValueError(f"AUTOMACAO_TIMEZONE inválido: {timezone_nome}.") from erro

    dias_texto = (os.getenv("AUTOMACAO_RELATORIO_DIAS") or "0").strip()
    try:
        dias_relatorio = int(dias_texto)
    except ValueError as erro:
        raise ValueError("AUTOMACAO_RELATORIO_DIAS deve ser um número inteiro.") from erro

    if dias_relatorio < 0 or dias_relatorio > 365:
        raise ValueError("AUTOMACAO_RELATORIO_DIAS deve estar entre 0 e 365.")

    return ConfiguracaoAgendamento(
        ativo=_env_bool("AUTOMACAO_ENABLED", "false"),
        hora=hora,
        minuto=minuto,
        timezone=timezone_nome,
        enviar_email=_env_bool("AUTOMACAO_ENVIAR_EMAIL", "true"),
        dias_relatorio=dias_relatorio,
    )


def _registrar_falha(resultado: dict[str, object], etapa: str, erro: Exception) -> None:
    etapas = resultado["etapas"]
    assert isinstance(etapas, dict)
    etapas[etapa] = {
        "status": "falha",
        "erro": f"{type(erro).__name__}: {erro}",
    }
    resultado["sucesso"] = False
    LOGGER.exception("Etapa %s falhou, mas o fluxo continuará.", etapa)


def executar_rotina(
    data_referencia: date | str | None = None,
    *,
    provedor_whatsapp: ProvedorWhatsApp | None = None,
    emprestimo_ids: list[int] | None = None,
    enviar_email: bool | None = None,
) -> dict[str, object]:
    """Executa uma passagem completa da automação sem interromper por falha isolada.

    Em produção, ``emprestimo_ids`` deve permanecer como ``None`` para processar os
    empréstimos elegíveis. O filtro existe para testes controlados.
    """
    _carregar_env()
    referencia = _normalizar_data(data_referencia)
    configuracao = carregar_configuracao_agendamento()
    email_ativo = configuracao.enviar_email if enviar_email is None else enviar_email

    inicio = datetime.now()
    resultado: dict[str, object] = {
        "inicio": inicio,
        "fim": None,
        "data_referencia": referencia,
        "sucesso": True,
        "etapas": {},
    }
    etapas = resultado["etapas"]
    assert isinstance(etapas, dict)

    LOGGER.info("Iniciando rotina diária do BiblioAvisa para %s.", referencia.isoformat())

    mensagens_criadas: list[dict[str, object]] = []

    try:
        prazos = verificar_prazos(referencia, emprestimo_ids)
        mensagens_obj = prazos.get("mensagens", [])
        mensagens_criadas = list(mensagens_obj) if isinstance(mensagens_obj, list) else []
        etapas["prazos"] = {
            "status": "ok",
            "processados": prazos.get("processados", 0),
            "mensagens_criadas": len(mensagens_criadas),
            "atualizados_para_atrasado": prazos.get("atualizados_para_atrasado", 0),
            "classificacoes": prazos.get("classificacoes", {}),
            "classificacoes_risco": prazos.get("classificacoes_risco", {}),
        }
        LOGGER.info(
            "Verificação de prazos concluída: %s empréstimo(s), %s mensagem(ns) criada(s).",
            prazos.get("processados", 0),
            len(mensagens_criadas),
        )
    except Exception as erro:
        _registrar_falha(resultado, "prazos", erro)

    try:
        mensagem_ids: list[int] | None
        if emprestimo_ids is None:
            # Execução normal também recupera mensagens pendentes de uma execução
            # anterior que tenha sido interrompida antes do envio.
            mensagem_ids = None
        else:
            mensagem_ids = [
                int(item["id"])
                for item in mensagens_criadas
                if item.get("id") is not None
            ]

        envios = processar_mensagens_pendentes(
            provedor=provedor_whatsapp,
            mensagem_ids=mensagem_ids,
        )
        enviados = sum(1 for item in envios if item.get("status") == "enviado")
        falhas = sum(1 for item in envios if item.get("status") != "enviado")
        etapas["whatsapp"] = {
            "status": "ok" if falhas == 0 else "parcial",
            "processados": len(envios),
            "enviados": enviados,
            "falhas": falhas,
        }
        if falhas:
            resultado["sucesso"] = False
            LOGGER.warning(
                "Envio de WhatsApp terminou com %s falha(s); as demais etapas continuarão.",
                falhas,
            )
        else:
            LOGGER.info("Fila de WhatsApp processada: %s envio(s).", enviados)
    except Exception as erro:
        _registrar_falha(resultado, "whatsapp", erro)

    caminho_pdf: Path | None = None
    try:
        data_inicio_relatorio = referencia - timedelta(days=configuracao.dias_relatorio)
        caminho_pdf = gerar_relatorio_pdf(data_inicio_relatorio, referencia)
        etapas["relatorio"] = {
            "status": "ok",
            "arquivo": str(caminho_pdf),
            "data_inicio": data_inicio_relatorio,
            "data_fim": referencia,
        }
        LOGGER.info("Relatório PDF gerado em %s.", caminho_pdf)
    except Exception as erro:
        _registrar_falha(resultado, "relatorio", erro)

    if not email_ativo:
        etapas["email"] = {"status": "desativado"}
        LOGGER.info("Envio automático de e-mail está desativado.")
    elif caminho_pdf is None:
        etapas["email"] = {
            "status": "ignorado",
            "motivo": "relatorio_indisponivel",
        }
        resultado["sucesso"] = False
        LOGGER.warning("E-mail não enviado porque o relatório não foi gerado.")
    else:
        try:
            assunto = (
                "BiblioAvisa - Relatório "
                f"{(referencia - timedelta(days=configuracao.dias_relatorio)).strftime('%d/%m/%Y')} "
                f"a {referencia.strftime('%d/%m/%Y')}"
            )
            envio_email = enviar_relatorio_email(caminho_pdf, assunto=assunto)
            etapas["email"] = {
                "status": "ok",
                "arquivo": str(envio_email.arquivo),
                "destinatario": envio_email.destinatario,
            }
            LOGGER.info("Relatório enviado por e-mail com sucesso.")
        except Exception as erro:
            _registrar_falha(resultado, "email", erro)

    fim = datetime.now()
    resultado["fim"] = fim
    LOGGER.info(
        "Rotina diária finalizada em %.2f segundo(s). Sucesso geral: %s.",
        (fim - inicio).total_seconds(),
        resultado["sucesso"],
    )
    return resultado


def _job_rotina_diaria() -> None:
    try:
        executar_rotina()
    except Exception:
        # Proteção final: uma exceção inesperada não remove o job do agendador.
        LOGGER.exception("Falha inesperada fora das etapas controladas da rotina diária.")


def criar_agendador(
    configuracao: ConfiguracaoAgendamento | None = None,
) -> BlockingScheduler:
    """Cria o APScheduler com um único job diário, sem iniciá-lo."""
    config = configuracao or carregar_configuracao_agendamento()
    fuso = ZoneInfo(config.timezone)
    scheduler = BlockingScheduler(timezone=fuso)
    scheduler.add_job(
        _job_rotina_diaria,
        trigger=CronTrigger(
            hour=config.hora,
            minute=config.minuto,
            timezone=fuso,
        ),
        id="biblioavisa_rotina_diaria",
        name="BiblioAvisa - rotina diária",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    return scheduler


def iniciar_agendador() -> int:
    config = carregar_configuracao_agendamento()
    if not config.ativo:
        print("[AUTOMAÇÃO] Agendamento diário DESATIVADO no .env (AUTOMACAO_ENABLED=false).")
        return 0

    scheduler = criar_agendador(config)
    print(
        "[AUTOMAÇÃO] Agendamento diário ATIVADO: "
        f"{config.hora:02d}:{config.minuto:02d} ({config.timezone})."
    )
    print("[AUTOMAÇÃO] O agendador não dispara uma execução imediata ao iniciar.")

    try:
        scheduler.start()
        return 0
    except (KeyboardInterrupt, SystemExit):
        return 0


def _configurar_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    _configurar_logging()
    parser = argparse.ArgumentParser(
        description="Executa ou agenda o fluxo principal do BiblioAvisa."
    )
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument(
        "--executar-agora",
        action="store_true",
        help="Executa uma passagem completa imediatamente.",
    )
    modo.add_argument(
        "--agendar",
        action="store_true",
        help="Mantém o processo aberto e executa diariamente no horário do .env.",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="Data de referência AAAA-MM-DD para execução manual.",
    )
    parser.add_argument(
        "--simular-whatsapp",
        action="store_true",
        help="Não usa Baileys; processa a fila com provedor simulado.",
    )
    parser.add_argument(
        "--sem-email",
        action="store_true",
        help="Gera o PDF, mas não envia o relatório por e-mail nesta execução.",
    )
    args = parser.parse_args()

    try:
        if args.agendar:
            return iniciar_agendador()

        provedor = ProvedorSimulado() if args.simular_whatsapp else None
        resultado = executar_rotina(
            args.data,
            provedor_whatsapp=provedor,
            enviar_email=False if args.sem_email else None,
        )
        return 0 if resultado["sucesso"] else 1
    except (RuntimeError, ValueError) as erro:
        LOGGER.error("%s", erro)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
