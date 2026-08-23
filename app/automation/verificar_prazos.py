"""Verificação dos prazos de empréstimos e preparação de avisos pendentes."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import psycopg2
from psycopg2.extras import RealDictCursor

from app.db import conectar


CLASSIFICACOES = ("em_dia", "faltam_2_dias", "vence_hoje", "vencido")
TIPO_POR_CLASSIFICACAO = {
    "faltam_2_dias": "aviso_2_dias",
    "vence_hoje": "aviso_vencimento",
    "vencido": "aviso_atraso",
}


def _normalizar_data(valor: date | str | None) -> date:
    if valor is None:
        return date.today()

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError as erro:
            raise ValueError("data_referencia deve estar no formato AAAA-MM-DD.") from erro

    raise ValueError("data_referencia deve ser uma data ou texto no formato AAAA-MM-DD.")


def _normalizar_ids(valores: Iterable[int] | None) -> list[int] | None:
    if valores is None:
        return None

    ids: list[int] = []

    for valor in valores:
        try:
            identificador = int(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError("emprestimo_ids deve conter apenas números inteiros.") from erro

        if identificador <= 0:
            raise ValueError("emprestimo_ids deve conter apenas IDs maiores que zero.")

        if identificador not in ids:
            ids.append(identificador)

    return ids


def classificar_prazo(
    data_prevista_devolucao: date,
    data_referencia: date | str | None = None,
) -> str:
    """Classifica um prazo em relação à data informada ou ao dia atual."""
    hoje = _normalizar_data(data_referencia)
    dias_para_vencimento = (data_prevista_devolucao - hoje).days

    if dias_para_vencimento < 0:
        return "vencido"

    if dias_para_vencimento == 0:
        return "vence_hoje"

    if dias_para_vencimento == 2:
        return "faltam_2_dias"

    return "em_dia"


def _montar_mensagem(emprestimo: dict[str, object], classificacao: str) -> str:
    usuario = str(emprestimo["usuario_nome"])
    livro = str(emprestimo["livro_titulo"])
    prazo = emprestimo["data_prevista_devolucao"]

    if not isinstance(prazo, date):
        raise ValueError("O empréstimo retornou uma data prevista inválida.")

    prazo_formatado = prazo.strftime("%d/%m/%Y")

    if classificacao == "faltam_2_dias":
        return (
            f'Olá, {usuario}! O empréstimo do livro "{livro}" vence em 2 dias, '
            f"em {prazo_formatado}."
        )

    if classificacao == "vence_hoje":
        return (
            f'Olá, {usuario}! O empréstimo do livro "{livro}" vence hoje '
            f"({prazo_formatado})."
        )

    if classificacao == "vencido":
        return (
            f'Olá, {usuario}! O empréstimo do livro "{livro}" está vencido desde '
            f"{prazo_formatado}."
        )

    raise ValueError(f"Classificação sem aviso associado: {classificacao}.")


def _resultado_vazio(data_referencia: date) -> dict[str, object]:
    return {
        "data_referencia": data_referencia,
        "processados": 0,
        "atualizados_para_atrasado": 0,
        "classificacoes": {nome: 0 for nome in CLASSIFICACOES},
        "emprestimos": [],
        "mensagens": [],
    }


def verificar_prazos(
    data_referencia: date | str | None = None,
    emprestimo_ids: Iterable[int] | None = None,
) -> dict[str, object]:
    """Analisa empréstimos não devolvidos e registra os avisos necessários.

    Quando ``emprestimo_ids`` é omitido, todos os empréstimos ativos ou atrasados
    são processados. O filtro opcional existe para execuções dirigidas e testes,
    evitando que dados fora do cenário desejado sejam modificados.

    Avisos necessários são inseridos em ``mensagens`` com status ``pendente``.
    O índice único do banco impede que o mesmo tipo de aviso seja registrado mais
    de uma vez para o mesmo empréstimo e data de referência.
    """
    hoje = _normalizar_data(data_referencia)
    ids = _normalizar_ids(emprestimo_ids)
    resultado = _resultado_vazio(hoje)

    if ids == []:
        return resultado

    filtro_ids = ""
    parametros: list[object] = []

    if ids is not None:
        filtro_ids = "AND e.id = ANY(%s)"
        parametros.append(ids)

    conexao = conectar()

    try:
        with conexao.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT
                    e.id,
                    e.usuario_id,
                    u.nome AS usuario_nome,
                    u.telefone AS usuario_telefone,
                    e.livro_id,
                    l.titulo AS livro_titulo,
                    e.data_emprestimo,
                    e.data_prevista_devolucao,
                    e.status
                FROM emprestimos e
                INNER JOIN usuarios u ON u.id = e.usuario_id
                INNER JOIN livros l ON l.id = e.livro_id
                WHERE e.status IN ('ativo', 'atrasado')
                  AND e.data_devolucao IS NULL
                  {filtro_ids}
                ORDER BY e.data_prevista_devolucao, e.id;
                """,
                tuple(parametros),
            )
            emprestimos = [dict(linha) for linha in cursor.fetchall()]

            resultado["processados"] = len(emprestimos)
            classificacoes = resultado["classificacoes"]
            emprestimos_resultado = resultado["emprestimos"]
            mensagens_resultado = resultado["mensagens"]

            assert isinstance(classificacoes, dict)
            assert isinstance(emprestimos_resultado, list)
            assert isinstance(mensagens_resultado, list)

            for emprestimo in emprestimos:
                prazo = emprestimo["data_prevista_devolucao"]
                if not isinstance(prazo, date):
                    raise ValueError(
                        f"Empréstimo {emprestimo['id']} retornou uma data prevista inválida."
                    )

                dias_para_vencimento = (prazo - hoje).days
                classificacao = classificar_prazo(prazo, hoje)
                classificacoes[classificacao] += 1

                status_final = str(emprestimo["status"])

                if classificacao == "vencido" and status_final != "atrasado":
                    cursor.execute(
                        """
                        UPDATE emprestimos
                        SET status = 'atrasado', atualizado_em = NOW()
                        WHERE id = %s
                          AND status <> 'atrasado';
                        """,
                        (emprestimo["id"],),
                    )
                    if cursor.rowcount:
                        resultado["atualizados_para_atrasado"] = (
                            int(resultado["atualizados_para_atrasado"]) + 1
                        )
                    status_final = "atrasado"

                emprestimos_resultado.append(
                    {
                        "id": emprestimo["id"],
                        "usuario_id": emprestimo["usuario_id"],
                        "livro_id": emprestimo["livro_id"],
                        "data_prevista_devolucao": prazo,
                        "dias_para_vencimento": dias_para_vencimento,
                        "classificacao": classificacao,
                        "status": status_final,
                    }
                )

                tipo = TIPO_POR_CLASSIFICACAO.get(classificacao)
                if tipo is None:
                    continue

                texto = _montar_mensagem(emprestimo, classificacao)

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
                    ON CONFLICT DO NOTHING
                    RETURNING
                        id,
                        usuario_id,
                        emprestimo_id,
                        direcao,
                        tipo,
                        mensagem,
                        status,
                        data_referencia,
                        data_mensagem;
                    """,
                    (
                        emprestimo["usuario_id"],
                        emprestimo["id"],
                        tipo,
                        texto,
                        hoje,
                    ),
                )
                mensagem_criada = cursor.fetchone()

                if mensagem_criada:
                    mensagem = dict(mensagem_criada)
                    mensagem["usuario_nome"] = emprestimo["usuario_nome"]
                    mensagem["usuario_telefone"] = emprestimo["usuario_telefone"]
                    mensagem["livro_titulo"] = emprestimo["livro_titulo"]
                    mensagens_resultado.append(mensagem)

        conexao.commit()
        return resultado
    except (ValueError, psycopg2.Error):
        conexao.rollback()
        raise
    finally:
        conexao.close()
