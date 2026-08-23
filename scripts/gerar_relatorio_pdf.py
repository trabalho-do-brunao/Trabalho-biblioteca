"""Gera o relatório PDF do BiblioAvisa para um período informado."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.relatorio import gerar_relatorio_pdf


def _data_iso(valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as erro:
        raise argparse.ArgumentTypeError("Use a data no formato AAAA-MM-DD.") from erro


def main() -> int:
    hoje = date.today()
    parser = argparse.ArgumentParser(description="Gera relatório PDF do BiblioAvisa.")
    parser.add_argument(
        "--inicio",
        type=_data_iso,
        default=hoje - timedelta(days=30),
        help="Data inicial AAAA-MM-DD. Padrão: 30 dias atrás.",
    )
    parser.add_argument(
        "--fim",
        type=_data_iso,
        default=hoje,
        help="Data final AAAA-MM-DD. Padrão: hoje.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=None,
        help="Caminho opcional do PDF. Se omitido, usa reports/.",
    )
    args = parser.parse_args()

    try:
        caminho = gerar_relatorio_pdf(args.inicio, args.fim, args.saida)
    except Exception as erro:
        print(f"[ERRO] {type(erro).__name__}: {erro}")
        return 1

    print("=== Relatório BiblioAvisa gerado ===")
    print(f"Período : {args.inicio.strftime('%d/%m/%Y')} a {args.fim.strftime('%d/%m/%Y')}")
    print(f"Arquivo : {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
