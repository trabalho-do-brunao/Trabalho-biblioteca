"""Teste do histórico operacional do WhatsApp sem acessar serviços externos."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.whatsapp import listar_historico_whatsapp, obter_resumo_whatsapp


def _criar_dados() -> tuple[int, int, int]:
    sufixo = uuid4().hex[:10]
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    f"Usuário WhatsApp {sufixo}",
                    f"5598{sufixo[:9]}",
                    f"whatsapp-{sufixo}@teste.local",
                ),
            )
            usuario_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO livros (titulo, autor, isbn, quantidade_total, quantidade_disponivel)
                VALUES (%s, %s, %s, 1, 0)
                RETURNING id;
                """,
                (f"Livro WhatsApp {sufixo}", "Teste Automatizado", f"WPP-{sufixo}"),
            )
            livro_id = cursor.fetchone()[0]

            prazo = date.today() + timedelta(days=7)
            cursor.execute(
                """
                INSERT INTO emprestimos (
                    usuario_id, livro_id, data_emprestimo, data_prevista_devolucao, status
                )
                VALUES (%s, %s, %s, %s, 'ativo')
                RETURNING id;
                """,
                (usuario_id, livro_id, date.today(), prazo),
            )
            emprestimo_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO mensagens (
                    usuario_id, emprestimo_id, direcao, tipo, mensagem, status, data_referencia
                )
                VALUES
                    (%s, %s, 'enviada', 'aviso_2_dias', %s, 'enviado', CURRENT_DATE),
                    (%s, %s, 'recebida', 'solicitacao_renovacao', %s, 'recebido', CURRENT_DATE),
                    (%s, %s, 'enviada', 'confirmacao_renovacao', %s, 'falha', CURRENT_DATE);
                """,
                (
                    usuario_id,
                    emprestimo_id,
                    f"Aviso temporário {sufixo}",
                    usuario_id,
                    emprestimo_id,
                    f"RENOVAR {sufixo}",
                    usuario_id,
                    emprestimo_id,
                    f"Confirmação temporária {sufixo}",
                ),
            )

            cursor.execute(
                """
                INSERT INTO renovacoes (
                    emprestimo_id, data_anterior, nova_data, status, origem
                )
                VALUES (%s, %s, %s, 'aprovada', 'whatsapp');
                """,
                (emprestimo_id, prazo, prazo + timedelta(days=7)),
            )

        conexao.commit()
        return usuario_id, livro_id, emprestimo_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _limpar(usuario_id: int | None, livro_id: int | None, emprestimo_id: int | None) -> None:
    if usuario_id is None:
        return

    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            if emprestimo_id is not None:
                cursor.execute("DELETE FROM mensagens WHERE emprestimo_id = %s;", (emprestimo_id,))
                cursor.execute("DELETE FROM renovacoes WHERE emprestimo_id = %s;", (emprestimo_id,))
                cursor.execute("DELETE FROM emprestimos WHERE id = %s;", (emprestimo_id,))
            if livro_id is not None:
                cursor.execute("DELETE FROM livros WHERE id = %s;", (livro_id,))
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste do histórico do WhatsApp ===\n")
    usuario_id = livro_id = emprestimo_id = None

    try:
        usuario_id, livro_id, emprestimo_id = _criar_dados()

        mensagens = listar_historico_whatsapp(busca=str(emprestimo_id))
        relacionadas = [m for m in mensagens if int(m["emprestimo_id"] or 0) == emprestimo_id]
        assert len(relacionadas) == 3
        print("[OK] Histórico retornou as três mensagens temporárias")

        assert all("identificador_externo" not in mensagem for mensagem in relacionadas)
        print("[OK] API de consulta não expõe identificador externo")

        recebidas = listar_historico_whatsapp(direcao="recebida", busca=str(emprestimo_id))
        assert len(recebidas) == 1 and recebidas[0]["status"] == "recebido"
        print("[OK] Filtro por direção funciona")

        falhas = listar_historico_whatsapp(status="falha", busca=str(emprestimo_id))
        assert len(falhas) == 1
        print("[OK] Filtro por falha funciona")

        periodo = listar_historico_whatsapp(
            data_inicio=date.today(),
            data_fim=date.today(),
            busca=str(emprestimo_id),
        )
        assert len(periodo) == 3
        print("[OK] Filtro por período funciona")

        renovacao = next(m for m in relacionadas if m["tipo"] == "solicitacao_renovacao")
        assert renovacao["renovacao_status"] == "aprovada"
        assert renovacao["renovacao_nova_data"] is not None
        print("[OK] Resultado da renovação aparece junto ao histórico")

        resumo = obter_resumo_whatsapp()
        assert resumo["total"] >= 3
        assert resumo["enviadas"] >= 2
        assert resumo["recebidas"] >= 1
        assert resumo["falhas"] >= 1
        print("[OK] Indicadores gerais do WhatsApp foram calculados")

        print("\n=== Teste do histórico do WhatsApp passou ===")
        return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            _limpar(usuario_id, livro_id, emprestimo_id)
            if usuario_id is not None:
                print("[OK] Dados temporários removidos do PostgreSQL")
        except Exception as erro_limpeza:
            print(f"[AVISO] Falha ao limpar dados temporários: {erro_limpeza}")


if __name__ == "__main__":
    raise SystemExit(main())
