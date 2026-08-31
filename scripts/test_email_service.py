"""Testa o serviço de e-mail sem abrir conexão de rede nem enviar mensagens reais."""

from __future__ import annotations

import smtplib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.email_service import (
    ConfiguracaoEmail,
    EmailEnvioError,
    enviar_relatorio_email,
)


def _configuracao_teste() -> ConfiguracaoEmail:
    return ConfiguracaoEmail(
        host="smtp.exemplo.local",
        porta=587,
        usuario="biblioteca@exemplo.test",
        senha="senha-apenas-de-teste",
        destinatario="responsavel@exemplo.test",
    )


def main() -> int:
    print("=== Teste do serviço de e-mail ===\n")

    try:
        with TemporaryDirectory() as diretorio:
            pdf = Path(diretorio) / "relatorio_teste.pdf"
            pdf.write_bytes(b"%PDF-1.4\n% arquivo simulado para teste\n%%EOF\n")
            config = _configuracao_teste()

            with patch("app.services.email_service.smtplib.SMTP") as smtp_mock:
                servidor = smtp_mock.return_value.__enter__.return_value
                resultado = enviar_relatorio_email(
                    pdf,
                    assunto="Relatório de teste",
                    configuracao=config,
                    timeout=5,
                )

                smtp_mock.assert_called_once_with(config.host, config.porta, timeout=5)
                servidor.ehlo.assert_called()
                servidor.starttls.assert_called_once()
                servidor.login.assert_called_once_with(config.usuario, config.senha)
                servidor.send_message.assert_called_once()

                mensagem = servidor.send_message.call_args.args[0]
                if mensagem["Subject"] != "Relatório de teste":
                    raise AssertionError("O assunto do e-mail não foi montado corretamente.")
                if mensagem["To"] != config.destinatario:
                    raise AssertionError("O destinatário do e-mail não foi montado corretamente.")
                if not mensagem.is_multipart():
                    raise AssertionError("O e-mail deveria possuir anexo.")

                anexos = list(mensagem.iter_attachments())
                if len(anexos) != 1:
                    raise AssertionError("Era esperado exatamente um anexo.")
                if anexos[0].get_filename() != pdf.name:
                    raise AssertionError("O nome do PDF anexado está incorreto.")
                if anexos[0].get_content_type() != "application/pdf":
                    raise AssertionError("O anexo deveria ser application/pdf.")
                if resultado.arquivo != pdf.resolve():
                    raise AssertionError("O resultado não retornou o PDF enviado.")

            print("[OK] Mensagem montada com assunto, destinatário e PDF anexado")
            print("[OK] STARTTLS e autenticação SMTP seriam executados")
            print("[OK] Nenhuma conexão de rede foi aberta")

            with patch("app.services.email_service.smtplib.SMTP") as smtp_mock:
                servidor = smtp_mock.return_value.__enter__.return_value
                servidor.login.side_effect = smtplib.SMTPAuthenticationError(
                    535,
                    b"falha simulada",
                )

                try:
                    enviar_relatorio_email(pdf, configuracao=config)
                except EmailEnvioError:
                    pass
                else:
                    raise AssertionError(
                        "Falha de autenticação deveria gerar EmailEnvioError."
                    )

            print("[OK] Falha de autenticação é convertida em erro controlado")
            print("\n=== Teste do serviço de e-mail passou ===")
            return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
