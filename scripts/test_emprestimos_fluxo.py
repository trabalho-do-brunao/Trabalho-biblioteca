"""Teste manual do fluxo de empréstimos, devoluções e controle de estoque."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import conectar
from app.repositories.emprestimos import (
    EmprestimoJaDevolvidoError,
    LivroIndisponivelError,
    buscar_emprestimos_ativos,
    buscar_historico_emprestimos,
    registrar_devolucao,
    registrar_emprestimo,
)


def _criar_dados_temporarios() -> tuple[int, int]:
    sufixo = uuid4().hex[:10]
    telefone = f"5599{sufixo[:9]}"
    isbn = f"TESTE-{sufixo}"
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
                    "Usuário Temporário Empréstimos",
                    telefone,
                    f"emprestimos-{sufixo}@teste.local",
                ),
            )
            usuario_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO livros (
                    titulo,
                    autor,
                    isbn,
                    quantidade_total,
                    quantidade_disponivel
                )
                VALUES (%s, %s, %s, 1, 1)
                RETURNING id;
                """,
                (
                    "Livro Temporário Empréstimos",
                    "Teste Automatizado",
                    isbn,
                ),
            )
            livro_id = cursor.fetchone()[0]

        conexao.commit()
        return usuario_id, livro_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _consultar_estoque(livro_id: int) -> tuple[int, int]:
    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT quantidade_total, quantidade_disponivel
                FROM livros
                WHERE id = %s;
                """,
                (livro_id,),
            )
            resultado = cursor.fetchone()
            if not resultado:
                raise AssertionError("Livro temporário não encontrado durante o teste.")
            return resultado[0], resultado[1]
    finally:
        conexao.close()


def _limpar_dados(usuario_id: int | None, livro_id: int | None) -> None:
    if usuario_id is None and livro_id is None:
        return

    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            if usuario_id is not None:
                cursor.execute("DELETE FROM emprestimos WHERE usuario_id = %s;", (usuario_id,))
            elif livro_id is not None:
                cursor.execute("DELETE FROM emprestimos WHERE livro_id = %s;", (livro_id,))

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
    print("=== Teste de empréstimos, devoluções e estoque ===\n")

    usuario_id: int | None = None
    livro_id: int | None = None

    try:
        usuario_id, livro_id = _criar_dados_temporarios()
        print(f"[OK] Usuário temporário criado: ID {usuario_id}")
        print(f"[OK] Livro temporário criado: ID {livro_id}, estoque 1/1")

        prazo = date.today() + timedelta(days=7)
        emprestimo = registrar_emprestimo(usuario_id, livro_id, prazo)
        emprestimo_id = int(emprestimo["id"])

        assert emprestimo["status"] == "ativo"
        assert emprestimo["quantidade_disponivel"] == 0
        assert _consultar_estoque(livro_id) == (1, 0)
        print(f"[OK] Empréstimo registrado: ID {emprestimo_id}")
        print("[OK] Estoque reduzido de 1 para 0")

        try:
            registrar_emprestimo(usuario_id, livro_id, prazo)
        except LivroIndisponivelError:
            print("[OK] Segundo empréstimo bloqueado por falta de exemplar")
        else:
            raise AssertionError("O sistema permitiu empréstimo sem exemplar disponível.")

        ativos = buscar_emprestimos_ativos(usuario_id)
        if not any(int(item["id"]) == emprestimo_id for item in ativos):
            raise AssertionError("O empréstimo criado não apareceu na consulta de ativos.")
        print("[OK] Empréstimo apareceu na consulta de ativos do usuário")

        devolucao = registrar_devolucao(emprestimo_id)
        assert devolucao["status"] == "devolvido"
        assert devolucao["quantidade_disponivel"] == 1
        assert _consultar_estoque(livro_id) == (1, 1)
        print("[OK] Devolução registrada")
        print("[OK] Estoque restaurado de 0 para 1")

        try:
            registrar_devolucao(emprestimo_id)
        except EmprestimoJaDevolvidoError:
            print("[OK] Segunda devolução do mesmo empréstimo foi bloqueada")
        else:
            raise AssertionError("O sistema permitiu devolver o mesmo empréstimo duas vezes.")

        ativos_depois = buscar_emprestimos_ativos(usuario_id)
        if any(int(item["id"]) == emprestimo_id for item in ativos_depois):
            raise AssertionError("Empréstimo devolvido continuou aparecendo como ativo.")
        print("[OK] Empréstimo devolvido não aparece mais como ativo")

        historico = buscar_historico_emprestimos(usuario_id)
        registro = next(
            (item for item in historico if int(item["id"]) == emprestimo_id),
            None,
        )
        if not registro or registro["status"] != "devolvido":
            raise AssertionError("O histórico não registrou corretamente a devolução.")
        print("[OK] Histórico contém o empréstimo finalizado")

        print("\n=== Todos os testes de empréstimos passaram ===")
        return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            _limpar_dados(usuario_id, livro_id)
            if usuario_id is not None or livro_id is not None:
                print("[OK] Dados temporários removidos do banco.")
        except Exception as erro_limpeza:
            print(f"[AVISO] Falha ao remover dados temporários: {erro_limpeza}")


if __name__ == "__main__":
    raise SystemExit(main())
