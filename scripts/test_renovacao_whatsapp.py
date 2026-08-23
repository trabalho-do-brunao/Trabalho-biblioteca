"""Teste integrado da renovação por resposta no WhatsApp, sem rede externa."""

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
from app.services.renovacao_whatsapp import processar_resposta_whatsapp
from app.services.whatsapp import ProvedorSimulado


def criar_cenario() -> dict[str, object]:
    sufixo = str(uuid.uuid4().int)[-9:]
    telefone = f"5598{sufixo}"
    hoje = date.today()
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, telefone, email)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (f"Teste Renovação {sufixo}", telefone, f"renovacao{sufixo}@teste.local"),
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
                VALUES (%s, 'Autor de Teste', 3, 0)
                RETURNING id;
                """,
                (f"Livro Teste Renovação {sufixo}",),
            )
            livro_id = cursor.fetchone()["id"]

            data_emprestimo = hoje - timedelta(days=10)
            prazos = {
                "ativo_alvo": hoje + timedelta(days=3),
                "ativo_outro": hoje + timedelta(days=5),
                "atrasado": hoje - timedelta(days=1),
            }
            emprestimos: dict[str, int] = {}

            for nome, prazo in prazos.items():
                status = "atrasado" if nome == "atrasado" else "ativo"
                cursor.execute(
                    """
                    INSERT INTO emprestimos (
                        usuario_id,
                        livro_id,
                        data_emprestimo,
                        data_prevista_devolucao,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (usuario_id, livro_id, data_emprestimo, prazo, status),
                )
                emprestimos[nome] = cursor.fetchone()["id"]

            alerta_ativo = f"alerta-ativo-{uuid.uuid4().hex}"
            alerta_atrasado = f"alerta-atrasado-{uuid.uuid4().hex}"

            cursor.execute(
                """
                INSERT INTO mensagens (
                    usuario_id, emprestimo_id, direcao, tipo, mensagem,
                    status, identificador_externo, data_referencia
                )
                VALUES
                    (%s, %s, 'enviada', 'aviso_vencimento', 'Aviso do empréstimo ativo', 'enviado', %s, %s),
                    (%s, %s, 'enviada', 'aviso_atraso', 'Aviso do empréstimo atrasado', 'enviado', %s, %s);
                """,
                (
                    usuario_id,
                    emprestimos["ativo_alvo"],
                    alerta_ativo,
                    hoje,
                    usuario_id,
                    emprestimos["atrasado"],
                    alerta_atrasado,
                    hoje,
                ),
            )

            # Este aviso não foi enviado e deve desaparecer quando o prazo for renovado.
            cursor.execute(
                """
                INSERT INTO mensagens (
                    usuario_id, emprestimo_id, direcao, tipo, mensagem,
                    status, data_referencia
                )
                VALUES (%s, %s, 'enviada', 'aviso_2_dias', 'Aviso pendente antigo', 'pendente', %s);
                """,
                (usuario_id, emprestimos["ativo_alvo"], hoje),
            )

        conexao.commit()
        return {
            "usuario_id": usuario_id,
            "livro_id": livro_id,
            "telefone": telefone,
            "emprestimos": emprestimos,
            "prazos": prazos,
            "alerta_ativo": alerta_ativo,
            "alerta_atrasado": alerta_atrasado,
            "hoje": hoje,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def conferir_banco(cenario: dict[str, object]) -> None:
    usuario_id = int(cenario["usuario_id"])
    emprestimos = cenario["emprestimos"]
    prazos = cenario["prazos"]
    assert isinstance(emprestimos, dict)
    assert isinstance(prazos, dict)

    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, data_prevista_devolucao, status
                FROM emprestimos
                WHERE id = ANY(%s);
                """,
                (list(emprestimos.values()),),
            )
            por_id = {linha["id"]: dict(linha) for linha in cursor.fetchall()}

            assert por_id[emprestimos["ativo_alvo"]]["data_prevista_devolucao"] == prazos["ativo_alvo"] + timedelta(days=7)
            assert por_id[emprestimos["ativo_outro"]]["data_prevista_devolucao"] == prazos["ativo_outro"]
            assert por_id[emprestimos["atrasado"]]["data_prevista_devolucao"] == prazos["atrasado"]

            cursor.execute(
                """
                SELECT emprestimo_id, data_anterior, nova_data, status, motivo_recusa
                FROM renovacoes
                WHERE emprestimo_id = ANY(%s)
                ORDER BY id;
                """,
                (list(emprestimos.values()),),
            )
            renovacoes = [dict(linha) for linha in cursor.fetchall()]
            assert len(renovacoes) == 2
            assert renovacoes[0]["emprestimo_id"] == emprestimos["ativo_alvo"]
            assert renovacoes[0]["status"] == "aprovada"
            assert renovacoes[0]["data_anterior"] == prazos["ativo_alvo"]
            assert renovacoes[0]["nova_data"] == prazos["ativo_alvo"] + timedelta(days=7)
            assert renovacoes[1]["emprestimo_id"] == emprestimos["atrasado"]
            assert renovacoes[1]["status"] == "recusada"
            assert renovacoes[1]["nova_data"] is None
            assert renovacoes[1]["motivo_recusa"]

            cursor.execute(
                """
                SELECT direcao, tipo, status, identificador_externo, mensagem
                FROM mensagens
                WHERE usuario_id = %s
                ORDER BY id;
                """,
                (usuario_id,),
            )
            mensagens = [dict(linha) for linha in cursor.fetchall()]

            recebidas = [item for item in mensagens if item["direcao"] == "recebida"]
            respostas = [
                item
                for item in mensagens
                if item["direcao"] == "enviada"
                and item["tipo"] in {"confirmacao_renovacao", "recusa_renovacao", "outro"}
            ]
            assert len(recebidas) == 4
            assert len(respostas) == 4
            assert all(item["status"] == "recebido" for item in recebidas)
            assert all(item["status"] == "enviado" for item in respostas)
            assert all(item["identificador_externo"] for item in respostas)

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM mensagens
                WHERE emprestimo_id = %s
                  AND direcao = 'enviada'
                  AND status = 'pendente'
                  AND tipo IN ('aviso_2_dias', 'aviso_vencimento', 'aviso_atraso');
                """,
                (emprestimos["ativo_alvo"],),
            )
            assert cursor.fetchone()["total"] == 0
    finally:
        conexao.close()


def limpar_cenario(cenario: dict[str, object] | None) -> None:
    if not cenario:
        return

    usuario_id = int(cenario["usuario_id"])
    emprestimos = cenario["emprestimos"]
    assert isinstance(emprestimos, dict)
    ids = list(emprestimos.values())
    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM mensagens WHERE usuario_id = %s;", (usuario_id,))
            cursor.execute("DELETE FROM renovacoes WHERE emprestimo_id = ANY(%s);", (ids,))
            cursor.execute("DELETE FROM emprestimos WHERE id = ANY(%s);", (ids,))
            cursor.execute("DELETE FROM livros WHERE id = %s;", (cenario["livro_id"],))
            cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste de renovação por resposta no WhatsApp ===\n")
    cenario: dict[str, object] | None = None
    provedor = ProvedorSimulado()

    try:
        cenario = criar_cenario()
        telefone = str(cenario["telefone"])
        emprestimos = cenario["emprestimos"]
        prazos = cenario["prazos"]
        assert isinstance(emprestimos, dict)
        assert isinstance(prazos, dict)
        print(f"[OK] Cenário temporário criado para o usuário {cenario['usuario_id']}")

        id_entrada_aprovada = f"entrada-aprovada-{uuid.uuid4().hex}"
        aprovada = processar_resposta_whatsapp(
            telefone=telefone,
            texto="RENOVAR",
            identificador_externo=id_entrada_aprovada,
            mensagem_citada_id=str(cenario["alerta_ativo"]),
            provedor=provedor,
            data_referencia=cenario["hoje"],
        )
        assert aprovada["status"] == "aprovada"
        assert aprovada["emprestimo_id"] == emprestimos["ativo_alvo"]
        assert aprovada["data_anterior"] == prazos["ativo_alvo"]
        assert aprovada["nova_data"] == prazos["ativo_alvo"] + timedelta(days=7)
        assert aprovada["envio"]["status"] == "enviado"
        print("[OK] Resposta ao aviso correto renovou somente o empréstimo escolhido")

        duplicada = processar_resposta_whatsapp(
            telefone=telefone,
            texto="RENOVAR",
            identificador_externo=id_entrada_aprovada,
            mensagem_citada_id=str(cenario["alerta_ativo"]),
            provedor=provedor,
            data_referencia=cenario["hoje"],
        )
        assert duplicada["status"] == "duplicada"
        assert provedor.quantidade_envios == 1
        print("[OK] Reentrega do mesmo webhook não renovou nem respondeu duas vezes")

        recusada = processar_resposta_whatsapp(
            telefone=telefone,
            texto="Renovar",
            identificador_externo=f"entrada-atrasada-{uuid.uuid4().hex}",
            mensagem_citada_id=str(cenario["alerta_atrasado"]),
            provedor=provedor,
            data_referencia=cenario["hoje"],
        )
        assert recusada["status"] == "recusada"
        assert recusada["emprestimo_id"] == emprestimos["atrasado"]
        assert recusada["motivo_recusa"]
        assert recusada["envio"]["status"] == "enviado"
        print("[OK] Empréstimo atrasado foi recusado e recebeu o motivo da recusa")

        invalida = processar_resposta_whatsapp(
            telefone=telefone,
            texto="OI",
            identificador_externo=f"entrada-invalida-{uuid.uuid4().hex}",
            provedor=provedor,
            data_referencia=cenario["hoje"],
        )
        assert invalida["status"] == "comando_invalido"
        assert invalida["envio"]["status"] == "enviado"
        print("[OK] Comando inválido recebeu orientação para usar RENOVAR")

        ambigua = processar_resposta_whatsapp(
            telefone=telefone,
            texto="RENOVAR",
            identificador_externo=f"entrada-ambigua-{uuid.uuid4().hex}",
            provedor=provedor,
            data_referencia=cenario["hoje"],
        )
        assert ambigua["status"] == "recusada"
        assert ambigua["renovacao_id"] is None
        assert "mais de um empréstimo" in ambigua["resposta"]
        assert ambigua["envio"]["status"] == "enviado"
        print("[OK] RENOVAR sem citar aviso não escolheu livro quando havia múltiplos empréstimos")

        assert provedor.quantidade_envios == 4
        conferir_banco(cenario)
        print("[OK] Histórico, novas datas e mensagens foram persistidos corretamente")
        print("[OK] Aviso pendente do prazo antigo foi removvido após a renovação")

        print("\n=== Todos os testes de renovação passaram ===")
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
