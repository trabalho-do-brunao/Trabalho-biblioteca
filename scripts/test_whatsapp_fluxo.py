"""Teste do fluxo de mensagens sem enviar nada ao WhatsApp real."""

from __future__ import annotations

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.automation.enviar_mensagens import processar_mensagens_pendentes
from app.db import conectar
from app.services.whatsapp import ProvedorSimulado


def criar_cenario() -> dict[str, object]:
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
                (f"Teste WhatsApp {sufixo}", telefone, f"whatsapp{sufixo}@teste.local"),
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
                VALUES (%s, %s, 1, 0)
                RETURNING id;
                """,
                (f"Livro Teste WhatsApp {sufixo}", "Autor de Teste"),
            )
            livro_id = cursor.fetchone()["id"]

            hoje = date.today()
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
                (usuario_id, livro_id, hoje, hoje + timedelta(days=7)),
            )
            emprestimo_id = cursor.fetchone()["id"]

            mensagens_teste = [
                ("aviso_2_dias", "Mensagem simulada de sucesso 1."),
                ("aviso_vencimento", "[FALHA_TESTE] Mensagem que deve falhar."),
                ("aviso_atraso", "Mensagem simulada de sucesso 2."),
            ]
            mensagem_ids: list[int] = []

            for tipo, mensagem in mensagens_teste:
                cursor.execute(
                    """
                    INSERT INTO mensagens (
                        usuario_id,
                        emprestimo_id,
                        direcao,
                        tipo,
                        mensagem,
                        status,
                        data_referencia
                    )
                    VALUES (%s, %s, 'enviada', %s, %s, 'pendente', %s)
                    RETURNING id;
                    """,
                    (usuario_id, emprestimo_id, tipo, mensagem, hoje),
                )
                mensagem_ids.append(cursor.fetchone()["id"])

        conexao.commit()
        return {
            "usuario_id": usuario_id,
            "livro_id": livro_id,
            "emprestimo_id": emprestimo_id,
            "mensagem_ids": mensagem_ids,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def conferir_status(mensagem_ids: list[int]) -> dict[int, dict[str, object]]:
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, status, identificador_externo
                FROM mensagens
                WHERE id = ANY(%s)
                ORDER BY id;
                """,
                (mensagem_ids,),
            )
            return {linha["id"]: dict(linha) for linha in cursor.fetchall()}
    finally:
        conexao.close()


def limpar_cenario(cenario: dict[str, object] | None) -> None:
    if not cenario:
        return

    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "DELETE FROM mensagens WHERE id = ANY(%s);",
                (cenario["mensagem_ids"],),
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


def main() -> int:
    print("=== Teste simulado do fluxo WhatsApp ===\n")
    cenario: dict[str, object] | None = None

    try:
        cenario = criar_cenario()
        mensagem_ids = cenario["mensagem_ids"]
        assert isinstance(mensagem_ids, list)
        print(f"[OK] 3 mensagens temporárias criadas: {mensagem_ids}")

        provedor = ProvedorSimulado(falhar_se_contem="[FALHA_TESTE]")
        resultados = processar_mensagens_pendentes(
            provedor=provedor,
            mensagem_ids=mensagem_ids,
        )

        assert len(resultados) == 3
        assert [item["status"] for item in resultados] == ["enviado", "falha", "enviado"]
        print("[OK] Sucesso, falha simulada e continuidade foram processados na ordem esperada")

        banco = conferir_status(mensagem_ids)
        assert banco[mensagem_ids[0]]["status"] == "enviado"
        assert banco[mensagem_ids[0]]["identificador_externo"] == "simulado-1"
        assert banco[mensagem_ids[1]]["status"] == "falha"
        assert banco[mensagem_ids[1]]["identificador_externo"] is None
        assert banco[mensagem_ids[2]]["status"] == "enviado"
        assert banco[mensagem_ids[2]]["identificador_externo"] == "simulado-3"
        print("[OK] Status enviado/falha e IDs externos foram persistidos no PostgreSQL")

        segunda_execucao = processar_mensagens_pendentes(
            provedor=provedor,
            mensagem_ids=mensagem_ids,
        )
        assert segunda_execucao == []
        print("[OK] Mensagens já processadas não foram enviadas novamente")

        print("\n=== Todos os testes simulados de WhatsApp passaram ===")
        return 0
    except AssertionError:
        print("\n[ERRO] Uma das validações não produziu o resultado esperado.")
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
