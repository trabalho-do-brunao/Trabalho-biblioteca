"""Rotas HTTP para empréstimos e devoluções da biblioteca."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.repositories.emprestimos import (
    EmprestimoError,
    EmprestimoJaDevolvidoError,
    EmprestimoNaoEncontradoError,
    LivroIndisponivelError,
    LivroNaoEncontradoError,
    UsuarioNaoEncontradoError,
    buscar_emprestimos_ativos,
    buscar_historico_emprestimos,
    registrar_devolucao,
    registrar_emprestimo,
)
from app.services.lembrete_renovacao import (
    EmprestimoLembreteNaoEncontradoError,
    EmprestimoNaoElegivelLembreteError,
    EnvioLembreteRenovacaoError,
    LembreteRenovacaoError,
    enviar_lembrete_renovacao_manual,
)


router = APIRouter(prefix="/api/emprestimos", tags=["emprestimos"])


class EmprestimoEntrada(BaseModel):
    usuario_id: int = Field(ge=1)
    livro_id: int = Field(ge=1)
    data_prevista_devolucao: date
    data_emprestimo: date | None = None


class DevolucaoEntrada(BaseModel):
    data_devolucao: date | None = None


def _situacao_atual(emprestimos: list[dict[str, object]]) -> list[dict[str, object]]:
    """Deriva a situação exibida pela data atual sem alterar o histórico salvo no banco."""
    hoje = date.today()
    resultado: list[dict[str, object]] = []

    for item in emprestimos:
        registro = dict(item)
        prazo = registro.get("data_prevista_devolucao")
        devolvido = registro.get("status") == "devolvido" or registro.get("data_devolucao") is not None

        if not devolvido and isinstance(prazo, date):
            registro["status"] = "atrasado" if prazo < hoje else "ativo"

        resultado.append(registro)

    return resultado


def _erro_operacao(erro: Exception) -> HTTPException:
    if isinstance(
        erro,
        (
            UsuarioNaoEncontradoError,
            LivroNaoEncontradoError,
            EmprestimoNaoEncontradoError,
            EmprestimoLembreteNaoEncontradoError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro))
    if isinstance(
        erro,
        (
            LivroIndisponivelError,
            EmprestimoJaDevolvidoError,
            EmprestimoNaoElegivelLembreteError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
    if isinstance(erro, EnvioLembreteRenovacaoError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro))
    if isinstance(erro, (EmprestimoError, LembreteRenovacaoError, ValueError)):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))
    if isinstance(erro, ConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o banco de dados. Tente novamente em instantes.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Não foi possível concluir a operação com o empréstimo.",
    )


@router.get("/ativos")
def listar_ativos(usuario_id: int | None = Query(default=None, ge=1)) -> dict[str, object]:
    """Lista empréstimos ainda em aberto, opcionalmente filtrados por usuário."""
    try:
        emprestimos = _situacao_atual(buscar_emprestimos_ativos(usuario_id))
        return {"emprestimos": emprestimos, "total": len(emprestimos)}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.get("/historico")
def listar_historico(usuario_id: int | None = Query(default=None, ge=1)) -> dict[str, object]:
    """Lista o histórico de empréstimos, incluindo devoluções concluídas."""
    try:
        emprestimos = _situacao_atual(buscar_historico_emprestimos(usuario_id))
        return {"emprestimos": emprestimos, "total": len(emprestimos)}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.post("", status_code=status.HTTP_201_CREATED)
def cadastrar(dados: EmprestimoEntrada) -> dict[str, object]:
    """Registra um empréstimo usando as regras transacionais existentes no backend."""
    try:
        emprestimo = registrar_emprestimo(
            dados.usuario_id,
            dados.livro_id,
            dados.data_prevista_devolucao,
            dados.data_emprestimo,
        )
        return {"emprestimo": emprestimo, "mensagem": "Empréstimo registrado com sucesso."}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.post("/{emprestimo_id}/devolucao")
def devolver(emprestimo_id: int, dados: DevolucaoEntrada) -> dict[str, object]:
    """Finaliza um empréstimo e devolve o exemplar ao estoque."""
    try:
        emprestimo = registrar_devolucao(emprestimo_id, dados.data_devolucao)
        return {"emprestimo": emprestimo, "mensagem": "Devolução registrada com sucesso."}
    except Exception as erro:
        raise _erro_operacao(erro) from erro


@router.post("/{emprestimo_id}/lembrete-renovacao")
def enviar_lembrete_renovacao(emprestimo_id: int) -> dict[str, object]:
    """Envia um convite manual de renovação sem alterar os avisos automáticos."""
    try:
        return enviar_lembrete_renovacao_manual(emprestimo_id)
    except Exception as erro:
        raise _erro_operacao(erro) from erro
