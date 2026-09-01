"""Teste integrado e temporário do diferencial de análise de risco de atraso."""

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
from app.services.risco_atraso import classificar_risco_atraso


def _criar_usuario(cursor, sufixo: str, nome: str) -> int:
    telefone = f"5598{str(uuid.uuid4().int)[-9:]}"
    cursor.execute(
        """
        INSERT INTO usuarios (nome, telefone, email)
        VALUES (%s, %s, %s)
        RETURNING id;
        """,
        (f"{nome} {sufixo}", telefone, f"risco-{sufixo}-{nome.lower()}@teste.local"),
    )
    return int(cursor.fetchone()["id"])


def _criar_emprestimo(
    cursor,
    usuario_id: int,
    livro_id: int,
    inicio: date,
    prazo: date,
    devolucao: date | None = None,
) -> int:
    status = "devolvido" if devolucao is not None else "ativo"
    cursor.execute(
        """
        INSERT INTO emprestimos (
            usuario_id,
            livro_id,
            data_emprestimo,
            data_prevista_devolucao,
            data_devolucao,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (usuario_id, livro_id, inicio, prazo, devolucao, status),
    )
    return int(cursor.fetchone()["id"])


def criar_cenario(hoje: date) -> dict[str, object]:
    sufixo = str(uuid.uuid4().int)[-7:]
    conexao = conectar()
    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO livros (
                    titulo, autor, quantidade_total, quantidade_disponivel
                )
                VALUES (%s, 'Autor Teste', 20, 20)
                RETURNING id;
                """,
                (f"Livro Risco {sufixo}",),
            )
            livro_id = int(cursor.fetchone()["id"])

            usuarios = {
                "sem_historico": _criar_usuario(cursor, sufixo, "SemHistorico"),
                "baixo": _criar_usuario(cursor, sufixo, "Baixo"),
                "medio": _criar_usuario(cursor, sufixo, "Medio"),
                "alto": _criar_usuario(cursor, sufixo, "Alto"),
            }

            base = hoje - timedelta(days=60)

            # Baixo: duas devoluções no prazo.
            for deslocamento in (0, 20):
                inicio = base + timedelta(days=deslocamento)
                prazo = inicio + timedelta(days=7)
                _criar_emprestimo(cursor, usuarios["baixo"], livro_id, inicio, prazo, prazo)

            # Médio: uma devolução anterior após o prazo.
            inicio = base
            prazo = inicio + timedelta(days=7)
            _criar_emprestimo(
                cursor,
                usuarios["medio"],
                livro_id,
                inicio,
                prazo,
                prazo + timedelta(days=2),
            )

            # Alto: duas devoluções anteriores após o prazo.
            for deslocamento in (0, 20):
                inicio = base + timedelta(days=deslocamento)
                prazo = inicio + timedelta(days=7)
                _criar_emprestimo(
                    cursor,
                    usuarios["alto"],
                    livro_id,
                    inicio,
                    prazo,
                    prazo + timedelta(days=2),
                )

            ativos = {
                "sem_historico": _criar_emprestimo(
                    cursor,
                    usuarios["sem_historico"],
                    livro_id,
                    hoje - timedelta(days=5),
                    hoje + timedelta(days=5),
                ),
                "baixo": _criar_emprestimo(
                    cursor,
                    usuarios["baixo"],
                    livro_id,
                    hoje - timedelta(days=5),
                    hoje + timedelta(days=3),
                ),
                "medio": _criar_emprestimo(
                    cursor,
                    usuarios["medio"],
                    livro_id,
                    hoje - timedelta(days=5),
                    hoje + timedelta(days=3),
                ),
                "alto_5": _criar_emprestimo(
                    cursor,
                    usuarios["alto"],
                    livro_id,
                    hoje - timedelta(days=5),
                    hoje + timedelta(days=5),
                ),
                "alto_2": _criar_emprestimo(
                    cursor,
                    usuarios["alto"],
                    livro_id,
                    hoje - timedelta(days=5),
                    hoje + timedelta(days=2),
                ),
            }

        conexao.commit()
        return {
            "livro_id": livro_id,
            "usuarios": usuarios,
            "ativos": ativos,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def limpar_cenario(cenario: dict[str, object] | None) -> None:
    if not cenario:
        return

    usuarios = cenario["usuarios"]
    assert isinstance(usuarios, dict)
    usuario_ids = list(usuarios.values())

    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM mensagens WHERE usuario_id = ANY(%s);", (usuario_ids,))
            cursor.execute("DELETE FROM renovacoes WHERE emprestimo_id IN (SELECT id FROM emprestimos WHERE usuario_id = ANY(%s));", (usuario_ids,))
            cursor.execute("DELETE FROM emprestimos WHERE usuario_id = ANY(%s);", (usuario_ids,))
            cursor.execute("DELETE FROM usuarios WHERE id = ANY(%s);", (usuario_ids,))
            cursor.execute("DELETE FROM livros WHERE id = %s;", (cenario["livro_id"],))
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def main() -> int:
    print("=== Teste do diferencial de análise de risco ===\n")
    hoje = date.today()
    cenario: dict[str, object] | None = None

    try:
        # Testes rápidos da regra pura.
        assert classificar_risco_atraso(0, 0).classificacao == "sem_historico"
        assert classificar_risco_atraso(3, 0).classificacao == "baixo"
        assert classificar_risco_atraso(3, 1).classificacao == "medio"
        assert classificar_risco_atraso(3, 2).classificacao == "alto"
        assert classificar_risco_atraso(0, 0, 1).classificacao == "alto"
        print("[OK] Regra determinística classifica sem histórico, baixo, médio e alto")

        cenario = criar_cenario(hoje)
        ativos = cenario["ativos"]
        usuarios = cenario["usuarios"]
        assert isinstance(ativos, dict)
        assert isinstance(usuarios, dict)

        resultado = verificar_prazos(hoje, list(ativos.values()))
        assert resultado["processados"] == 5

        analises = {
            item["usuario_id"]: item
            for item in resultado["analises_risco"]
        }
        assert analises[usuarios["sem_historico"]]["classificacao"] == "sem_historico"
        assert analises[usuarios["baixo"]]["classificacao"] == "baixo"
        assert analises[usuarios["medio"]]["classificacao"] == "medio"
        assert analises[usuarios["alto"]]["classificacao"] == "alto"
        print("[OK] Histórico real do PostgreSQL produziu as quatro classificações esperadas")

        assert analises[usuarios["medio"]]["dias_lembrete_adicional"] == 3
        assert analises[usuarios["alto"]]["dias_lembrete_adicional"] == 5
        print("[OK] Risco médio agenda +3 dias e risco alto agenda +5 dias")

        mensagens = resultado["mensagens"]
        risco = [item for item in mensagens if item.get("origem") == "analise_risco"]
        obrigatorias = [item for item in mensagens if item.get("origem") != "analise_risco"]

        assert {item["emprestimo_id"] for item in risco} == {
            ativos["medio"],
            ativos["alto_5"],
        }
        assert all(item["tipo"] == "outro" for item in risco)
        print("[OK] Somente os empréstimos médio (+3) e alto (+5) receberam lembrete extra")

        assert len(obrigatorias) == 1
        assert obrigatorias[0]["emprestimo_id"] == ativos["alto_2"]
        assert obrigatorias[0]["tipo"] == "aviso_2_dias"
        print("[OK] Aviso obrigatório de 2 dias continua funcionando para usuário de alto risco")

        segunda = verificar_prazos(hoje, list(ativos.values()))
        assert segunda["mensagens"] == []
        print("[OK] Segunda execução não duplicou lembretes extras nem avisos obrigatórios")

        conexao = conectar()
        try:
            with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT emprestimo_id, tipo, status
                    FROM mensagens
                    WHERE usuario_id = ANY(%s)
                    ORDER BY id;
                    """,
                    (list(usuarios.values()),),
                )
                persistidas = [dict(linha) for linha in cursor.fetchall()]
        finally:
            conexao.close()

        assert len(persistidas) == 3
        assert sum(1 for item in persistidas if item["tipo"] == "outro") == 2
        assert sum(1 for item in persistidas if item["tipo"] == "aviso_2_dias") == 1
        print("[OK] Decisões que geraram lembrete ficaram registradas em mensagens como pendentes")

        print("\n=== Teste de análise de risco passou ===")
        return 0
    except AssertionError:
        print("\n[ERRO] Uma validação da análise de risco não produziu o resultado esperado.")
        return 1
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            limpar_cenario(cenario)
            if cenario:
                print("[OK] Dados temporários removidos do PostgreSQL.")
        except Exception as erro:
            print(f"[AVISO] Não foi possível limpar todos os dados temporários: {erro}")


if __name__ == "__main__":
    raise SystemExit(main())
