"""Teste controlado dos indicadores e itens de atenção do dashboard."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.dashboard import obter_dashboard
from app.repositories.emprestimos import registrar_emprestimo


def _criar_base() -> tuple[int, int]:
    sufixo = uuid4().hex[:10]
    telefone = f"5588{int(sufixo[:7], 16) % 10_000_000:07d}"
    isbn = f"978{int(sufixo[:10], 16) % 10_000_000_000:010d}"
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                ("Teste Dashboard", telefone, f"dashboard-{sufixo}@teste.local"),
            )
            usuario_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO livros (titulo, autor, isbn, quantidade_total, quantidade_disponivel)
                VALUES (%s, %s, %s, 2, 2)
                RETURNING id;
                """,
                ("Livro Teste Dashboard", "Teste Automatizado", isbn),
            )
            livro_id = cursor.fetchone()[0]
        conexao.commit()
        return usuario_id, livro_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _limpar(usuario_id: int | None, livro_id: int | None) -> None:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            if usuario_id is not None:
                cursor.execute("DELETE FROM emprestimos WHERE usuario_id = %s;", (usuario_id,))
            if livro_id is not None:
                cursor.execute("DELETE FROM livros WHERE id = %s;", (livro_id,))
            if usuario_id is not None:
                cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste do dashboard ===\n")
    usuario_id = None
    livro_id = None
    try:
        usuario_id, livro_id = _criar_base()
        hoje = date.today()

        atrasado = registrar_emprestimo(
            usuario_id,
            livro_id,
            hoje - timedelta(days=2),
            data_emprestimo=hoje - timedelta(days=6),
        )
        proximo = registrar_emprestimo(
            usuario_id,
            livro_id,
            hoje + timedelta(days=1),
            data_emprestimo=hoje - timedelta(days=1),
        )

        dados = obter_dashboard(dias_proximos=2, limite=20)
        resumo = dados["resumo"]
        atencao = dados["atencao"]

        assert int(resumo["emprestimos_abertos"]) >= 2
        assert int(resumo["emprestimos_atrasados"]) >= 1
        assert int(resumo["proximos_vencimento"]) >= 1
        assert int(resumo["usuarios_ativos"]) >= 1

        ids = {int(item["id"]) for item in atencao}
        assert int(atrasado["id"]) in ids
        assert int(proximo["id"]) in ids

        item_atrasado = next(item for item in atencao if int(item["id"]) == int(atrasado["id"]))
        item_proximo = next(item for item in atencao if int(item["id"]) == int(proximo["id"]))
        assert item_atrasado["situacao"] == "atrasado"
        assert int(item_atrasado["dias"]) == 2
        assert item_proximo["situacao"] == "proximo"
        assert int(item_proximo["dias"]) == 1

        print("[OK] Indicadores retornam empréstimos abertos, próximos e atrasados")
        print("[OK] Empréstimo atrasado aparece na área de atenção")
        print("[OK] Empréstimo vencendo amanhã aparece na área de atenção")
        print("[OK] Quantidade de dias foi calculada corretamente")
        print("\n=== Teste do dashboard passou ===")
        return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            _limpar(usuario_id, livro_id)
            if usuario_id is not None or livro_id is not None:
                print("[OK] Dados temporários removidos do PostgreSQL")
        except Exception as erro_limpeza:
            print(f"[AVISO] Falha ao limpar dados temporários: {erro_limpeza}")


if __name__ == "__main__":
    raise SystemExit(main())
