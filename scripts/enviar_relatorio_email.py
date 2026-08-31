"""Gera um relatório PDF e envia uma cópia ao responsável por e-mail."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.email_service import enviar_relatorio_email
from app.services.relatorio import gerar_relatorio_pdf


def _data_iso(valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as erro:
        raise argparse.ArgumentTypeError("Use a data no formato AAAA-MM-DD.") from erro


def main() -> int:
    hoje = date.today()
    parser = argparse.ArgumentParser(
        description="Gera o relatório PDF do BiblioAvisa e envia ao e-mail configurado no .env."
    )
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

    if args.inicio > args.fim:
        print("[ERRO] A data inicial não pode ser posterior à data final.")
        return 1

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    try:
        arquivo = gerar_relatorio_pdf(args.inicio, args.fim, args.saida)
        assunto = (
            "BiblioAvisa - Relatório "
            f"{args.inicio.strftime('%d/%m/%Y')} a {args.fim.strftime('%d/%m/%Y')}"
        )
        resultado = enviar_relatorio_email(arquivo, assunto=assunto)
    except Exception as erro:
        print(f"[ERRO] {type(erro).__name__}: {erro}")
        return 1

    print("=== Relatório BiblioAvisa enviado por e-mail ===")
    print(f"Período : {args.inicio.strftime('%d/%m/%Y')} a {args.fim.strftime('%d/%m/%Y')}")
    print(f"Arquivo : {resultado.arquivo}")
    print("[OK] Envio concluído para o destinatário configurado no .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
