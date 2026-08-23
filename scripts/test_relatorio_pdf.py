"""Teste de geração do relatório PDF usando dados reais do PostgreSQL, sem escrita."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.relatorios import buscar_dados_relatorio
from app.services.relatorio import gerar_relatorio_pdf


def main() -> int:
    print("=== Teste do relatório PDF ===\n")
    hoje = date.today()
    inicio = hoje - timedelta(days=30)
    caminho = PROJECT_ROOT / "reports" / "teste_relatorio_biblioavisa.pdf"

    try:
        dados = buscar_dados_relatorio(inicio, hoje)
        print(f"[OK] Mensagens consultadas no período: {len(dados['mensagens'])}")
        print(f"[OK] Empréstimos atrasados consultados: {len(dados['emprestimos_atrasados'])}")
        print(f"[OK] Empréstimos próximos do vencimento: {len(dados['emprestimos_proximos'])}")

        arquivo = gerar_relatorio_pdf(inicio, hoje, caminho)
        if not arquivo.exists():
            raise AssertionError("O arquivo PDF não foi criado.")

        conteudo = arquivo.read_bytes()
        if len(conteudo) < 1000:
            raise AssertionError("O arquivo PDF gerado ficou pequeno demais para ser válido.")
        if not conteudo.startswith(b"%PDF-"):
            raise AssertionError("O arquivo gerado não possui cabeçalho PDF válido.")
        if b"%%EOF" not in conteudo[-2048:]:
            raise AssertionError("O arquivo gerado não possui marcador final de PDF.")

        print(f"[OK] PDF criado: {arquivo}")
        print(f"[OK] Tamanho: {len(conteudo)} bytes")
        print("[OK] Cabeçalho e final do arquivo PDF são válidos")
        print("[OK] O teste utilizou apenas consultas de leitura no PostgreSQL")
        print("\n=== Teste do relatório PDF passou ===")
        print("Abra o arquivo gerado para a conferência visual final.")
        return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
