"""Envio de relatórios PDF do BiblioAvisa por e-mail via SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
LOGGER = logging.getLogger(__name__)


class EmailServiceError(RuntimeError):
    """Erro base relacionado à configuração ou ao envio de e-mail."""


class EmailConfiguracaoError(EmailServiceError):
    """Indica que a configuração SMTP local está ausente ou inválida."""


class EmailEnvioError(EmailServiceError):
    """Indica que o servidor SMTP recusou ou não concluiu o envio."""


@dataclass(frozen=True)
class ConfiguracaoEmail:
    host: str
    porta: int
    usuario: str
    senha: str
    destinatario: str


@dataclass(frozen=True)
class ResultadoEnvioEmail:
    arquivo: Path
    destinatario: str
    identificador: str


def carregar_configuracao_email() -> ConfiguracaoEmail:
    """Carrega do `.env` somente as variáveis necessárias para o SMTP."""
    if not ENV_PATH.exists():
        raise EmailConfiguracaoError(
            "Arquivo .env não encontrado. Execute setup.bat e configure o e-mail localmente."
        )

    load_dotenv(ENV_PATH)

    host = (os.getenv("SMTP_HOST") or "").strip()
    porta_texto = (os.getenv("SMTP_PORT") or "587").strip()
    usuario = (os.getenv("SMTP_USER") or "").strip()
    senha = os.getenv("SMTP_PASSWORD") or ""
    destinatario = (os.getenv("EMAIL_DESTINATARIO") or "").strip()

    faltando = [
        nome
        for nome, valor in (
            ("SMTP_HOST", host),
            ("SMTP_USER", usuario),
            ("SMTP_PASSWORD", senha),
            ("EMAIL_DESTINATARIO", destinatario),
        )
        if not valor
    ]
    if faltando:
        raise EmailConfiguracaoError(
            "Variáveis de e-mail não configuradas no .env: " + ", ".join(faltando)
        )

    try:
        porta = int(porta_texto)
    except ValueError as erro:
        raise EmailConfiguracaoError("SMTP_PORT deve ser um número inteiro.") from erro

    if porta <= 0 or porta > 65535:
        raise EmailConfiguracaoError("SMTP_PORT deve estar entre 1 e 65535.")

    return ConfiguracaoEmail(
        host=host,
        porta=porta,
        usuario=usuario,
        senha=senha,
        destinatario=destinatario,
    )


def montar_email_relatorio(
    caminho_pdf: str | Path,
    configuracao: ConfiguracaoEmail,
    assunto: str | None = None,
    corpo: str | None = None,
) -> EmailMessage:
    """Monta a mensagem MIME com o relatório PDF anexado, sem realizar rede."""
    arquivo = Path(caminho_pdf).expanduser().resolve()
    if not arquivo.exists() or not arquivo.is_file():
        raise FileNotFoundError(f"Relatório PDF não encontrado: {arquivo}")
    if arquivo.suffix.lower() != ".pdf":
        raise ValueError("O anexo do relatório deve ser um arquivo PDF.")
    if arquivo.stat().st_size == 0:
        raise ValueError("O relatório PDF está vazio.")

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto or "BiblioAvisa - Relatório de notificações e empréstimos"
    mensagem["From"] = configuracao.usuario
    mensagem["To"] = configuracao.destinatario
    mensagem["Message-ID"] = make_msgid(domain=None)
    mensagem.set_content(
        corpo
        or (
            "Olá,\n\n"
            "Segue em anexo o relatório gerado pelo BiblioAvisa.\n\n"
            "Esta é uma mensagem automática do sistema."
        )
    )

    mensagem.add_attachment(
        arquivo.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=arquivo.name,
    )
    return mensagem


def enviar_relatorio_email(
    caminho_pdf: str | Path,
    assunto: str | None = None,
    corpo: str | None = None,
    configuracao: ConfiguracaoEmail | None = None,
    timeout: float = 20.0,
) -> ResultadoEnvioEmail:
    """Envia um relatório PDF usando o servidor SMTP configurado localmente.

    Porta 465 usa TLS implícito (SMTP_SSL). Outras portas usam STARTTLS,
    comportamento compatível com a configuração mais comum na porta 587.
    """
    config = configuracao or carregar_configuracao_email()
    mensagem = montar_email_relatorio(caminho_pdf, config, assunto, corpo)
    contexto_tls = ssl.create_default_context()

    try:
        if config.porta == 465:
            with smtplib.SMTP_SSL(
                config.host,
                config.porta,
                timeout=timeout,
                context=contexto_tls,
            ) as servidor:
                servidor.login(config.usuario, config.senha)
                servidor.send_message(mensagem)
        else:
            with smtplib.SMTP(config.host, config.porta, timeout=timeout) as servidor:
                servidor.ehlo()
                servidor.starttls(context=contexto_tls)
                servidor.ehlo()
                servidor.login(config.usuario, config.senha)
                servidor.send_message(mensagem)
    except smtplib.SMTPAuthenticationError as erro:
        LOGGER.error("Falha de autenticação ao enviar relatório por e-mail.")
        raise EmailEnvioError(
            "Falha na autenticação SMTP. Confira SMTP_USER e SMTP_PASSWORD no .env."
        ) from erro
    except (smtplib.SMTPException, OSError) as erro:
        LOGGER.error(
            "Falha ao enviar relatório por e-mail (%s).",
            type(erro).__name__,
        )
        raise EmailEnvioError(
            "Não foi possível enviar o relatório por e-mail. Confira o servidor SMTP e tente novamente."
        ) from erro

    arquivo = Path(caminho_pdf).expanduser().resolve()
    identificador = str(mensagem["Message-ID"] or "")
    LOGGER.info("Relatório enviado por e-mail com sucesso.")
    return ResultadoEnvioEmail(
        arquivo=arquivo,
        destinatario=config.destinatario,
        identificador=identificador,
    )
