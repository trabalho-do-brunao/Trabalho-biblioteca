"""Teste seguro da geração de relatórios e montagem do e-mail sem acesso SMTP real."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.email_service import ConfiguracaoEmail, montar_email_relatorio
from app.services.relatorio import gerar_relatorio_pdf


def main() -> int:
    hoje = date.today()

    with TemporaryDirectory(prefix="biblioavisa_relatorio_") as pasta:
        caminho = Path(pasta) / "relatorio_teste.pdf"
        gerado = gerar_relatorio_pdf(hoje, hoje, caminho)

        assert gerado == caminho.resolve()
        assert gerado.exists(), "O PDF não foi criado."
        assert gerado.stat().st_size > 0, "O PDF foi criado vazio."
        assert gerado.read_bytes().startswith(b"%PDF"), "O arquivo gerado não é um PDF válido."
        print("[OK] PDF gerado pelo serviço de relatório")

        config = ConfiguracaoEmail(
            host="smtp.exemplo.local",
            porta=587,
            usuario="remetente@exemplo.local",
            senha="senha-ficticia-nao-utilizada",
            destinatario="responsavel@exemplo.local",
        )
        mensagem = montar_email_relatorio(gerado, config)

        assert mensagem["To"] == config.destinatario
        assert mensagem["From"] == config.usuario
        anexos = list(mensagem.iter_attachments())
        assert len(anexos) == 1, "O relatório deveria conter exatamente um anexo."
        assert anexos[0].get_content_type() == "application/pdf"
        assert anexos[0].get_filename() == gerado.name
        assert config.senha not in mensagem.as_string(), "A senha SMTP não pode aparecer na mensagem."
        print("[OK] E-mail com PDF montado sem rede e sem expor senha SMTP")

        try:
            gerar_relatorio_pdf(date(2026, 2, 2), date(2026, 2, 1), Path(pasta) / "invalido.pdf")
        except ValueError:
            print("[OK] Período inválido foi rejeitado")
        else:
            raise AssertionError("Período inválido deveria gerar ValueError.")

    print("\n=== Teste de relatórios web passou ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
