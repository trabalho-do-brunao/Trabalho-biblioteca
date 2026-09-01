"""Teste integrado e seguro do fluxo principal do BiblioAvisa."""

from __future__ import annotations

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.main import ConfiguracaoAgendamento, criar_agendador, executar_rotina
from app.services.whatsapp import ProvedorSimulado


def criar_cenario(data_referencia: date) -> dict[str, int]:
    sufixo = str(uuid.uuid4().int)[-9:]
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    f"Teste Fluxo {sufixo}",
                    f"5598{sufixo}",
                    f"fluxo{sufixo}@teste.local",
                ),
            )
            usuario_id = int(cursor.fetchone()["id"])

            cursor.execute(
                """
                INSERT INTO livros (
                    titulo,
                    autor,
                    quantidade_total,
                    quantidade_disponivel
                )
                VALUES (%s, %s, 1, 0)
                RETURNING id;
                """,
                (f"Livro Teste Fluxo {sufixo}", "Autor de Teste"),
            )
            livro_id = int(cursor.fetchone()["id"])

            cursor.execute(
                """
                INSERT INTO emprestimos (
                    usuario_id,
                    livro_id,
                    data_emprestimo,
                    data_prevista_devolucao,
                    status
                )
                VALUES (%s, %s, %s, %s, 'ativo')
                RETURNING id;
                """,
                (
                    usuario_id,
                    livro_id,
                    data_referencia - timedelta(days=10),
                    data_referencia + timedelta(days=2),
                ),
            )
            emprestimo_id = int(cursor.fetchone()["id"])

        conexao.commit()
        return {
            "usuario_id": usuario_id,
            "livro_id": livro_id,
            "emprestimo_id": emprestimo_id,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def limpar_cenario(cenario: dict[str, int] | None) -> None:
    if not cenario:
        return
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "DELETE FROM mensagens WHERE emprestimo_id = %s;",
                (cenario["emprestimo_id"],),
            )
            cursor.execute(
                "DELETE FROM emprestimos WHERE id = %s;",
                (cenario["emprestimo_id"],),
            )
            cursor.execute("DELETE FROM livros WHERE id = %s;", (cenario["livro_id"],))
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (cenario["usuario_id"],))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def conferir_status_mensagem(emprestimo_id: int, esperado: str) -> None:
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT tipo, status
                FROM mensagens
                WHERE emprestimo_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (emprestimo_id,),
            )
            mensagem = cursor.fetchone()
            assert mensagem is not None
            assert mensagem["tipo"] == "aviso_2_dias"
            assert mensagem["status"] == esperado
    finally:
        conexao.close()


def remover_pdf(resultado: dict[str, object]) -> None:
    etapas = resultado.get("etapas")
    if not isinstance(etapas, dict):
        return
    relatorio = etapas.get("relatorio")
    if not isinstance(relatorio, dict):
        return
    arquivo = relatorio.get("arquivo")
    if not arquivo:
        return
    caminho = Path(str(arquivo))
    if caminho.exists():
        caminho.unlink()


def testar_agendador() -> None:
    config = ConfiguracaoAgendamento(
        ativo=True,
        hora=7,
        minuto=35,
        timezone="UTC",
        enviar_email=False,
        dias_relatorio=0,
    )
    scheduler = criar_agendador(config)
    job = scheduler.get_job("biblioavisa_rotina_diaria")
    assert job is not None
    gatilho = str(job.trigger)
    assert "hour='7'" in gatilho
    assert "minute='35'" in gatilho
    print("[OK] APScheduler criou o job diário no horário configurado")


def main() -> int:
    print("=== Teste do fluxo principal e agendamento ===\n")
    hoje = date.today()
    cenario_sucesso: dict[str, int] | None = None
    cenario_falha: dict[str, int] | None = None
    resultado_sucesso: dict[str, object] | None = None
    resultado_falha: dict[str, object] | None = None

    try:
        testar_agendador()

        cenario_sucesso = criar_cenario(hoje)
        resultado_sucesso = executar_rotina(
            hoje,
            provedor_whatsapp=ProvedorSimulado(),
            emprestimo_ids=[cenario_sucesso["emprestimo_id"]],
            enviar_email=False,
        )
        etapas = resultado_sucesso["etapas"]
        assert isinstance(etapas, dict)
        assert etapas["prazos"]["status"] == "ok"
        assert etapas["whatsapp"]["status"] == "ok"
        assert etapas["whatsapp"]["enviados"] == 1
        assert etapas["relatorio"]["status"] == "ok"
        assert etapas["email"]["status"] == "desativado"
        assert resultado_sucesso["sucesso"] is True
        conferir_status_mensagem(cenario_sucesso["emprestimo_id"], "enviado")
        print("[OK] Fluxo percorreu prazos → WhatsApp simulado → PDF sem usar rede externa")
        print("[OK] A mensagem de teste foi persistida como enviada")

        cenario_falha = criar_cenario(hoje)
        resultado_falha = executar_rotina(
            hoje,
            provedor_whatsapp=ProvedorSimulado(falhar_se_contem="vence em 2 dias"),
            emprestimo_ids=[cenario_falha["emprestimo_id"]],
            enviar_email=False,
        )
        etapas_falha = resultado_falha["etapas"]
        assert isinstance(etapas_falha, dict)
        assert etapas_falha["whatsapp"]["status"] == "parcial"
        assert etapas_falha["whatsapp"]["falhas"] == 1
        assert etapas_falha["relatorio"]["status"] == "ok"
        assert etapas_falha["email"]["status"] == "desativado"
        assert resultado_falha["sucesso"] is False
        conferir_status_mensagem(cenario_falha["emprestimo_id"], "falha")
        print("[OK] Falha simulada no WhatsApp não impediu a geração do relatório")
        print("[OK] A falha isolada ficou registrada sem encerrar o fluxo")

        print("\n=== Teste do fluxo principal passou ===")
        return 0
    except AssertionError:
        print("\n[ERRO] Uma validação do fluxo principal não produziu o resultado esperado.")
        return 1
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        for resultado in (resultado_sucesso, resultado_falha):
            if resultado:
                try:
                    remover_pdf(resultado)
                except Exception as erro:
                    print(f"[AVISO] Não foi possível remover um PDF de teste: {erro}")

        for cenario in (cenario_sucesso, cenario_falha):
            if cenario:
                try:
                    limpar_cenario(cenario)
                except Exception as erro:
                    print(f"[AVISO] Não foi possível limpar um cenário temporário: {erro}")

        if cenario_sucesso or cenario_falha:
            print("[OK] Dados temporários do teste foram removidos do PostgreSQL.")


if __name__ == "__main__":
    raise SystemExit(main())
