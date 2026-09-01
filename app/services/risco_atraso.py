"""Regras determinísticas para classificação de risco de atraso do BiblioAvisa.

A análise é complementar aos avisos obrigatórios. Ela nunca substitui os avisos
2 dias antes, no vencimento e após o vencimento.
"""

from __future__ import annotations

from dataclasses import dataclass


CLASSIFICACOES_RISCO = ("sem_historico", "baixo", "medio", "alto")


@dataclass(frozen=True)
class AnaliseRiscoAtraso:
    classificacao: str
    devolucoes_concluidas: int
    devolucoes_atrasadas: int
    emprestimos_atrasados_abertos: int
    percentual_atrasos: float
    dias_lembrete_adicional: int | None
    motivo: str


def classificar_risco_atraso(
    devolucoes_concluidas: int,
    devolucoes_atrasadas: int,
    emprestimos_atrasados_abertos: int = 0,
) -> AnaliseRiscoAtraso:
    """Classifica o risco a partir do histórico objetivo do usuário.

    Regras:
    - sem histórico: nenhuma devolução concluída e nenhum atraso ainda aberto;
    - baixo: histórico concluído sem atrasos;
    - médio: exatamente uma devolução anterior em atraso;
    - alto: duas ou mais devoluções atrasadas, ou ao menos um empréstimo
      atualmente atrasado.

    Risco médio gera lembrete adicional 3 dias antes do vencimento.
    Risco alto gera lembrete adicional 5 dias antes do vencimento.
    """
    total = int(devolucoes_concluidas)
    atrasadas = int(devolucoes_atrasadas)
    abertas = int(emprestimos_atrasados_abertos)

    if total < 0 or atrasadas < 0 or abertas < 0:
        raise ValueError("Os indicadores de risco não podem ser negativos.")
    if atrasadas > total:
        raise ValueError("Devoluções atrasadas não podem superar as devoluções concluídas.")

    percentual = (atrasadas / total * 100.0) if total else 0.0

    if abertas > 0:
        return AnaliseRiscoAtraso(
            classificacao="alto",
            devolucoes_concluidas=total,
            devolucoes_atrasadas=atrasadas,
            emprestimos_atrasados_abertos=abertas,
            percentual_atrasos=percentual,
            dias_lembrete_adicional=5,
            motivo=(
                f"Usuário possui {abertas} empréstimo(s) atualmente atrasado(s)."
            ),
        )

    if total == 0:
        return AnaliseRiscoAtraso(
            classificacao="sem_historico",
            devolucoes_concluidas=0,
            devolucoes_atrasadas=0,
            emprestimos_atrasados_abertos=0,
            percentual_atrasos=0.0,
            dias_lembrete_adicional=None,
            motivo="Usuário ainda não possui devoluções concluídas para análise.",
        )

    if atrasadas == 0:
        return AnaliseRiscoAtraso(
            classificacao="baixo",
            devolucoes_concluidas=total,
            devolucoes_atrasadas=0,
            emprestimos_atrasados_abertos=0,
            percentual_atrasos=0.0,
            dias_lembrete_adicional=None,
            motivo="Histórico de devoluções concluídas sem atrasos.",
        )

    if atrasadas == 1:
        return AnaliseRiscoAtraso(
            classificacao="medio",
            devolucoes_concluidas=total,
            devolucoes_atrasadas=1,
            emprestimos_atrasados_abertos=0,
            percentual_atrasos=percentual,
            dias_lembrete_adicional=3,
            motivo="Histórico contém uma devolução anterior em atraso.",
        )

    return AnaliseRiscoAtraso(
        classificacao="alto",
        devolucoes_concluidas=total,
        devolucoes_atrasadas=atrasadas,
        emprestimos_atrasados_abertos=0,
        percentual_atrasos=percentual,
        dias_lembrete_adicional=5,
        motivo=f"Histórico contém {atrasadas} devoluções anteriores em atraso.",
    )


def deve_enviar_lembrete_risco(
    analise: AnaliseRiscoAtraso,
    dias_para_vencimento: int,
) -> bool:
    """Indica se hoje é o dia do lembrete adicional daquela classificação."""
    return (
        analise.dias_lembrete_adicional is not None
        and dias_para_vencimento == analise.dias_lembrete_adicional
    )
