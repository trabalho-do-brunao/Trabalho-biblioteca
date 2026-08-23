"""Teste real controlado da renovação por resposta no WhatsApp.

Uso:
    python scripts/test_renovacao_real.py preparar
    python scripts/test_renovacao_real.py verificar
    python scripts/test_renovacao_real.py limpar

O estado do teste fica somente em .teste_renovacao_real.json, ignorado pelo Git.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.automation.enviar_mensagens import processar_mensagens_pendentes
from app.db import conectar
from app.repositories.usuarios import normalizar_telefone


STATE_FILE = PROJECT_ROOT / ".teste_renovacao_real.json"
load_dotenv(PROJECT_ROOT / ".env")


def _dias_renovacao() -> int:
    try:
        dias = int((os.getenv("RENOVACAO_DIAS") or "7").strip())
    except ValueError as erro:
        raise ValueError("RENOVACAO_DIAS deve ser um número inteiro.") from erro
    if dias <= 0 or dias > 90:
        raise ValueError("RENOVACAO_DIAS deve estar entre 1 e 90.")
    return dias


def _salvar_estado(estado: dict[str, object]) -> None:
    STATE_FILE.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _ler_estado() -> dict[str, object]:
    if not STATE_FILE.exists():
        raise RuntimeError(
            "Nenhum teste real preparado. Rode primeiro: "
            "python scripts/test_renovacao_real.py preparar"
        )
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def preparar() -> int:
    if STATE_FILE.exists():
        print("[ERRO] Já existe um teste real preparado.")
        print("Verifique-o ou limpe-o antes de criar outro:")
        print("  python scripts/test_renovacao_real.py verificar")
        print("  python scripts/test_renovacao_real.py limpar")
        return 1

    print("=== Preparar teste REAL de renovação ===\n")
    print("O Baileys e o webhook Python devem estar ligados.")
    print("Será enviado exatamente UM aviso real para o número informado.\n")

    try:
        telefone = normalizar_telefone(
            input("Número de destino com DDI e DDD (ex.: 5542...): ").strip()
        )
    except ValueError as erro:
        print(f"\n[ERRO] {erro}")
        return 1

    confirmacao = input(
        f"\nCriar empréstimo temporário e enviar o aviso para {telefone}? Digite SIM: "
    ).strip().upper()
    if confirmacao != "SIM":
        print("[INFO] Teste cancelado. Nada foi alterado.")
        return 0

    hoje = date.today()
    prazo = hoje + timedelta(days=2)
    dias_renovacao = _dias_renovacao()
    conexao = conectar()
    usuario_temporario = False

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone, ativo
                FROM usuarios
                WHERE telefone = %s;
                """,
                (telefone,),
            )
            usuario = cursor.fetchone()

            if usuario and not usuario["ativo"]:
                raise RuntimeError(
                    "Já existe um usuário inativo com este telefone. "
                    "Reative ou ajuste o cadastro antes do teste."
                )

            if not usuario:
                cursor.execute(
                    """
                    INSERT INTO usuarios (nome, telefone, ativo)
                    VALUES ('[TESTE] Renovação WhatsApp', %s, TRUE)
                    RETURNING id, nome, telefone, ativo;
                    """,
                    (telefone,),
                )
                usuario = cursor.fetchone()
                usuario_temporario = True

            cursor.execute(
                """
                INSERT INTO livros (
                    titulo,
                    autor,
                    quantidade_total,
                    quantidade_disponivel
                )
                VALUES (
                    '[TESTE] Livro para renovação via WhatsApp',
                    'BiblioAvisa',
                    1,
                    0
                )
                RETURNING id, titulo;
                """
            )
            livro = cursor.fetchone()

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
                RETURNING id, data_prevista_devolucao;
                """,
                (usuario["id"], livro["id"], hoje, prazo),
            )
            emprestimo = cursor.fetchone()

            texto_aviso = (
                "BiblioAvisa - teste real de renovação. "
                f"Livro: {livro['titulo']}. "
                f"Prazo atual: {prazo.strftime('%d/%m/%Y')}. "
                "Use RESPONDER nesta mensagem e envie RENOVAR para testar a renovação."
            )

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
                VALUES (%s, %s, 'enviada', 'aviso_2_dias', %s, 'pendente', %s)
                RETURNING id;
                """,
                (usuario["id"], emprestimo["id"], texto_aviso, hoje),
            )
            mensagem = cursor.fetchone()

        conexao.commit()
    except Exception as erro:
        conexao.rollback()
        print(f"\n[ERRO] Não foi possível preparar os dados temporários: {erro}")
        return 1
    finally:
        conexao.close()

    estado: dict[str, object] = {
        "criado_em": datetime.now().isoformat(timespec="seconds"),
        "usuario_id": int(usuario["id"]),
        "usuario_temporario": usuario_temporario,
        "livro_id": int(livro["id"]),
        "emprestimo_id": int(emprestimo["id"]),
        "mensagem_aviso_id": int(mensagem["id"]),
        "data_anterior": prazo.isoformat(),
        "dias_renovacao": dias_renovacao,
        "identificador_aviso": None,
    }
    _salvar_estado(estado)

    print("\n[OK] Dados temporários criados no PostgreSQL.")
    print(f"[OK] Empréstimo temporário: {emprestimo['id']}")
    print(f"[OK] Prazo antes da renovação: {prazo.strftime('%d/%m/%Y')}")
    print("[INFO] Enviando o aviso real pelo Baileys...")

    resultados = processar_mensagens_pendentes(
        mensagem_ids=[int(mensagem["id"])],
    )
    resultado = resultados[0] if resultados else {"status": "nao_processado"}

    if resultado.get("status") != "enviado":
        print(f"\n[ERRO] O aviso não foi enviado: {resultado}")
        print("Os dados temporários foram mantidos para diagnóstico.")
        print("Depois, use: python scripts/test_renovacao_real.py limpar")
        return 1

    estado["identificador_aviso"] = resultado.get("identificador_externo")
    _salvar_estado(estado)

    print("\n[OK] Aviso enviado pelo Baileys.")
    print(f"[OK] Message ID: {resultado.get('identificador_externo')}")
    print("\nAGORA, no aparelho de destino:")
    print("1. Abra a mensagem que acabou de chegar.")
    print("2. Use a função RESPONDER nessa mensagem específica.")
    print("3. Envie exatamente: RENOVAR")
    print(f"\nO prazo esperado após a renovação é +{dias_renovacao} dias.")
    print("Quando chegar a confirmação no WhatsApp, rode:")
    print("  python scripts/test_renovacao_real.py verificar")
    return 0


def verificar() -> int:
    try:
        estado = _ler_estado()
    except RuntimeError as erro:
        print(f"[ERRO] {erro}")
        return 1

    emprestimo_id = int(estado["emprestimo_id"])
    data_anterior = date.fromisoformat(str(estado["data_anterior"]))
    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, data_prevista_devolucao, status
                FROM emprestimos
                WHERE id = %s;
                """,
                (emprestimo_id,),
            )
            emprestimo = cursor.fetchone()

            cursor.execute(
                """
                SELECT id, status, data_anterior, nova_data, motivo_recusa
                FROM renovacoes
                WHERE emprestimo_id = %s
                ORDER BY id DESC
                LIMIT 1;
                """,
                (emprestimo_id,),
            )
            renovacao = cursor.fetchone()

            cursor.execute(
                """
                SELECT id, direcao, tipo, status, mensagem, identificador_externo
                FROM mensagens
                WHERE emprestimo_id = %s
                ORDER BY id;
                """,
                (emprestimo_id,),
            )
            mensagens = cursor.fetchall()
    finally:
        conexao.close()

    print("=== Verificação do teste real de renovação ===\n")

    if not emprestimo:
        print("[ERRO] O empréstimo temporário não foi encontrado.")
        return 1

    print(f"Prazo original : {data_anterior.strftime('%d/%m/%Y')}")
    print(f"Prazo atual    : {emprestimo['data_prevista_devolucao'].strftime('%d/%m/%Y')}")

    if not renovacao:
        print("\n[AGUARDANDO] Ainda não existe registro em renovacoes.")
        print("Confirme que você respondeu RENOVAR usando RESPONDER no aviso recebido.")
        print("Observe também os terminais do Baileys e do webhook para mensagens de erro.")
        return 2

    print(f"Renovação      : {renovacao['status']}")
    if renovacao["nova_data"]:
        print(f"Nova data      : {renovacao['nova_data'].strftime('%d/%m/%Y')}")
    if renovacao["motivo_recusa"]:
        print(f"Motivo         : {renovacao['motivo_recusa']}")

    recebida = any(
        item["direcao"] == "recebida" and item["tipo"] == "solicitacao_renovacao"
        for item in mensagens
    )
    confirmacao_enviada = any(
        item["direcao"] == "enviada"
        and item["tipo"] == "confirmacao_renovacao"
        and item["status"] == "enviado"
        for item in mensagens
    )

    aprovada = (
        renovacao["status"] == "aprovada"
        and renovacao["nova_data"] is not None
        and emprestimo["data_prevista_devolucao"] == renovacao["nova_data"]
        and emprestimo["data_prevista_devolucao"] > data_anterior
    )

    print(f"Mensagem RENOVAR registrada : {'SIM' if recebida else 'NÃO'}")
    print(f"Confirmação registrada       : {'SIM' if confirmacao_enviada else 'NÃO'}")

    if aprovada and recebida and confirmacao_enviada:
        print("\n=== TESTE REAL DE RENOVAÇÃO PASSOU ===")
        print("O prazo foi atualizado e o fluxo ficou registrado no PostgreSQL.")
        print("Depois de conferir a confirmação no celular, limpe os dados temporários:")
        print("  python scripts/test_renovacao_real.py limpar")
        return 0

    print("\n[ERRO] O fluxo ainda não atingiu todos os critérios esperados.")
    return 1


def limpar() -> int:
    try:
        estado = _ler_estado()
    except RuntimeError as erro:
        print(f"[ERRO] {erro}")
        return 1

    usuario_id = int(estado["usuario_id"])
    usuario_temporario = bool(estado["usuario_temporario"])
    livro_id = int(estado["livro_id"])
    emprestimo_id = int(estado["emprestimo_id"])

    confirmacao = input(
        "Remover os dados temporários deste teste real? Digite SIM: "
    ).strip().upper()
    if confirmacao != "SIM":
        print("[INFO] Limpeza cancelada.")
        return 0

    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM mensagens WHERE emprestimo_id = %s;", (emprestimo_id,))
            cursor.execute("DELETE FROM renovacoes WHERE emprestimo_id = %s;", (emprestimo_id,))
            cursor.execute("DELETE FROM emprestimos WHERE id = %s;", (emprestimo_id,))
            cursor.execute("DELETE FROM livros WHERE id = %s;", (livro_id,))

            if usuario_temporario:
                # O usuário foi criado exclusivamente para este teste.
                cursor.execute("DELETE FROM mensagens WHERE usuario_id = %s;", (usuario_id,))
                cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))

        conexao.commit()
    except Exception as erro:
        conexao.rollback()
        print(f"[ERRO] Não foi possível limpar os dados temporários: {erro}")
        return 1
    finally:
        conexao.close()

    STATE_FILE.unlink(missing_ok=True)
    print("[OK] Dados temporários removidos do PostgreSQL.")
    print("[OK] Estado local do teste removido.")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1].lower() not in {"preparar", "verificar", "limpar"}:
        print("Uso:")
        print("  python scripts/test_renovacao_real.py preparar")
        print("  python scripts/test_renovacao_real.py verificar")
        print("  python scripts/test_renovacao_real.py limpar")
        return 1

    comando = sys.argv[1].lower()
    if comando == "preparar":
        return preparar()
    if comando == "verificar":
        return verificar()
    return limpar()


if __name__ == "__main__":
    raise SystemExit(main())
