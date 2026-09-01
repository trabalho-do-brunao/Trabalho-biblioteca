"""Teste integrado da classificação de prazos e preparação de avisos."""

from __future__ import annotations

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.automation.verificar_prazos import verificar_prazos
from app.db import conectar


def criar_cenario(data_referencia: date) -> dict[str, object]:
    """Cria somente os dados temporários usados neste teste."""
    sufixo = str(uuid.uuid4().int)[-9:]
    telefone = f"5599{sufixo}"
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (f"Teste Prazos {sufixo}", telefone, f"prazos{sufixo}@teste.local"),
            )
            usuario_id = cursor.fetchone()["id"]

            cursor.execute(
                """
                INSERT INTO livros (
                    titulo,
                    autor,
                    quantidade_total,
                    quantidade_disponivel
                )
                VALUES (%s, %s, 4, 0)
                RETURNING id;
                """,
                (f"Livro Teste Prazos {sufixo}", "Autor de Teste"),
            )
            livro_id = cursor.fetchone()["id"]

            data_emprestimo = data_referencia - timedelta(days=15)
            cenarios = {
                # +4 continua classificado como "em_dia", mas não coincide com
                # os lembretes adicionais da análise de risco (+3 ou +5 dias).
                "em_dia": data_referencia + timedelta(days=4),
                "faltam_2_dias": data_referencia + timedelta(days=2),
                "vence_hoje": data_referencia,
                "vencido": data_referencia - timedelta(days=1),
            }
            emprestimos: dict[str, int] = {}

            for classificacao, prazo in cenarios.items():
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
                    (usuario_id, livro_id, data_emprestimo, prazo),
                )
                emprestimos[classificacao] = cursor.fetchone()["id"]

        conexao.commit()
        return {
            "usuario_id": usuario_id,
            "livro_id": livro_id,
            "emprestimos": emprestimos,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def conferir_banco(
    emprestimos: dict[str, int],
    data_referencia: date,
) -> None:
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            ids = list(emprestimos.values())

            cursor.execute(
                """
                SELECT id, status
                FROM emprestimos
                WHERE id = ANY(%s);
                """,
                (ids,),
            )
            status_por_id = {linha["id"]: linha["status"] for linha in cursor.fetchall()}

            assert status_por_id[emprestimos["vencido"]] == "atrasado"
            assert status_por_id[emprestimos["em_dia"]] == "ativo"
            assert status_por_id[emprestimos["faltam_2_dias"]] == "ativo"
            assert status_por_id[emprestimos["vence_hoje"]] == "ativo"

            cursor.execute(
                """
                SELECT emprestimo_id, tipo, status, data_referencia
                FROM mensagens
                WHERE emprestimo_id = ANY(%s)
                ORDER BY emprestimo_id, tipo;
                """,
                (ids,),
            )
            mensagens = [dict(linha) for linha in cursor.fetchall()]

            assert len(mensagens) == 3
            assert all(mensagem["status"] == "pendente" for mensagem in mensagens)
            assert all(
                mensagem["data_referencia"] == data_referencia
                for mensagem in mensagens
            )

            tipo_por_emprestimo = {
                mensagem["emprestimo_id"]: mensagem["tipo"]
                for mensagem in mensagens
            }

            assert tipo_por_emprestimo[emprestimos["faltam_2_dias"]] == "aviso_2_dias"
            assert tipo_por_emprestimo[emprestimos["vence_hoje"]] == "aviso_vencimento"
            assert tipo_por_emprestimo[emprestimos["vencido"]] == "aviso_atraso"
            assert emprestimos["em_dia"] not in tipo_por_emprestimo
    finally:
        conexao.close()


def limpar_cenario(cenario: dict[str, object] | None) -> None:
    if not cenario:
        return

    emprestimos = cenario["emprestimos"]
    assert isinstance(emprestimos, dict)
    ids = list(emprestimos.values())
    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM mensagens WHERE emprestimo_id = ANY(%s);", (ids,))
            cursor.execute("DELETE FROM emprestimos WHERE id = ANY(%s);", (ids,))
            cursor.execute("DELETE FROM livros WHERE id = %s;", (cenario["livro_id"],))
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (cenario["usuario_id"],))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste de verificação automática dos prazos ===\n")
    hoje = date.today()
    cenario: dict[str, object] | None = None

    try:
        cenario = criar_cenario(hoje)
        emprestimos = cenario["emprestimos"]
        assert isinstance(emprestimos, dict)
        ids = list(emprestimos.values())

        print(f"[OK] Cenário temporário criado com 4 empréstimos: {ids}")

        resultado = verificar_prazos(hoje, ids)

        assert resultado["processados"] == 4
        assert resultado["atualizados_para_atrasado"] == 1
        print("[OK] Os 4 empréstimos temporários foram processados")
        print("[OK] Empréstimo vencido foi atualizado para status atrasado")

        classificacoes = resultado["classificacoes"]
        assert classificacoes == {
            "em_dia": 1,
            "faltam_2_dias": 1,
            "vence_hoje": 1,
            "vencido": 1,
        }
        print("[OK] Classificações em dia, +2 dias, hoje e vencido estão corretas")

        resultados_por_id = {
            item["id"]: item["classificacao"]
            for item in resultado["emprestimos"]
        }
        assert resultados_por_id[emprestimos["em_dia"]] == "em_dia"
        assert resultados_por_id[emprestimos["faltam_2_dias"]] == "faltam_2_dias"
        assert resultados_por_id[emprestimos["vence_hoje"]] == "vence_hoje"
        assert resultados_por_id[emprestimos["vencido"]] == "vencido"

        mensagens = resultado["mensagens"]
        assert len(mensagens) == 3
        assert {mensagem["tipo"] for mensagem in mensagens} == {
            "aviso_2_dias",
            "aviso_vencimento",
            "aviso_atraso",
        }
        print("[OK] Foram preparadas somente as 3 mensagens necessárias")

        conferir_banco(emprestimos, hoje)
        print("[OK] Mensagens pendentes e status foram persistidos corretamente")

        segunda_execucao = verificar_prazos(hoje, ids)
        assert segunda_execucao["processados"] == 4
        assert segunda_execucao["atualizados_para_atrasado"] == 0
        assert segunda_execucao["mensagens"] == []
        print("[OK] Segunda execução não duplicou avisos do mesmo dia")

        conferir_banco(emprestimos, hoje)
        print("[OK] O banco continua com apenas 3 avisos após a segunda execução")

        print("\n=== Todos os testes de prazos passaram ===")
        return 0
    except AssertionError:
        print("\n[ERRO] Uma das validações do teste não produziu o resultado esperado.")
        return 1
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            limpar_cenario(cenario)
            if cenario:
                print("[OK] Dados temporários removidos do banco.")
        except Exception as erro:
            print(f"[AVISO] Não foi possível limpar todos os dados temporários: {erro}")


if __name__ == "__main__":
    raise SystemExit(main())
