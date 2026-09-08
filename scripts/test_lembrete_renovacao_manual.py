"""Valida o lembrete manual de renovação sem enviar WhatsApp real."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.automation.verificar_prazos import verificar_prazos
from app.db import conectar
from app.repositories.emprestimos import registrar_emprestimo
from app.services.lembrete_renovacao import enviar_lembrete_renovacao_manual
from app.services.whatsapp import ResultadoEnvio


class ProvedorTeste:
    def __init__(self) -> None:
        self.envios: list[tuple[str, str]] = []
        self.sufixo = uuid4().hex

    def enviar(self, telefone: str, mensagem: str) -> ResultadoEnvio:
        self.envios.append((telefone, mensagem))
        return ResultadoEnvio(
            provedor="teste-manual",
            identificador_externo=f"manual-{self.sufixo}-{len(self.envios)}",
        )


def _criar_dados() -> tuple[int, int, int, date]:
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
                    "Usuário Teste Lembrete",
                    f"5598{sufixo[:9]}",
                    f"lembrete-{sufixo}@teste.local",
                ),
            )
            usuario_id = int(cursor.fetchone()[0])

            cursor.execute(
                """
                INSERT INTO livros (
                    titulo, autor, isbn, quantidade_total, quantidade_disponivel
                )
                VALUES (%s, %s, %s, 1, 1)
                RETURNING id;
                """,
                (
                    "Livro Teste Lembrete Manual",
                    "Teste Automatizado",
                    f"LEMBRETE-{sufixo}",
                ),
            )
            livro_id = int(cursor.fetchone()[0])
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()

    prazo = date.today() + timedelta(days=2)
    emprestimo = registrar_emprestimo(usuario_id, livro_id, prazo)
    return usuario_id, livro_id, int(emprestimo["id"]), prazo


def _consultar_estado(emprestimo_id: int) -> tuple[date, str, int, list[tuple[str, str, str]]]:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT data_prevista_devolucao, status
                FROM emprestimos
                WHERE id = %s;
                """,
                (emprestimo_id,),
            )
            prazo, status = cursor.fetchone()

            cursor.execute(
                "SELECT COUNT(*) FROM renovacoes WHERE emprestimo_id = %s;",
                (emprestimo_id,),
            )
            renovacoes = int(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT tipo, status, mensagem
                FROM mensagens
                WHERE emprestimo_id = %s
                ORDER BY id;
                """,
                (emprestimo_id,),
            )
            mensagens = [(linha[0], linha[1], linha[2]) for linha in cursor.fetchall()]
            return prazo, status, renovacoes, mensagens
    finally:
        conexao.close()


def _limpar(usuario_id: int | None, livro_id: int | None, emprestimo_id: int | None) -> None:
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            if emprestimo_id is not None:
                cursor.execute("DELETE FROM mensagens WHERE emprestimo_id = %s;", (emprestimo_id,))
                cursor.execute("DELETE FROM renovacoes WHERE emprestimo_id = %s;", (emprestimo_id,))
                cursor.execute("DELETE FROM emprestimos WHERE id = %s;", (emprestimo_id,))
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
    print("=== Teste do lembrete manual de renovação ===\n")
    usuario_id: int | None = None
    livro_id: int | None = None
    emprestimo_id: int | None = None

    try:
        usuario_id, livro_id, emprestimo_id, prazo_original = _criar_dados()
        provedor = ProvedorTeste()

        resultado = enviar_lembrete_renovacao_manual(emprestimo_id, provedor=provedor)
        assert resultado["status"] == "enviado"
        assert len(provedor.envios) == 1
        assert "RENOVAR" in provedor.envios[0][1]
        print("[OK] Lembrete manual foi enviado pelo provedor simulado")

        prazo, status, renovacoes, mensagens = _consultar_estado(emprestimo_id)
        assert prazo == prazo_original
        assert status == "ativo"
        assert renovacoes == 0
        assert any(tipo == "outro" and estado == "enviado" for tipo, estado, _ in mensagens)
        print("[OK] Envio manual não alterou prazo, status ou histórico de renovações")

        verificacao = verificar_prazos(emprestimo_ids=[emprestimo_id])
        assert verificacao["classificacoes"]["faltam_2_dias"] == 1

        _, _, _, mensagens_depois = _consultar_estado(emprestimo_id)
        assert any(tipo == "aviso_2_dias" for tipo, _, _ in mensagens_depois)
        assert any(tipo == "outro" for tipo, _, _ in mensagens_depois)
        print("[OK] Aviso automático de 2 dias continua sendo criado normalmente")

        print("\n=== Lembrete manual validado sem interferir na automação ===")
        return 0
    except Exception as erro:
        print(f"\n[ERRO] {type(erro).__name__}: {erro}")
        return 1
    finally:
        try:
            _limpar(usuario_id, livro_id, emprestimo_id)
            print("[OK] Dados temporários removidos.")
        except Exception as erro_limpeza:
            print(f"[AVISO] Falha ao limpar dados temporários: {erro_limpeza}")


if __name__ == "__main__":
    raise SystemExit(main())
