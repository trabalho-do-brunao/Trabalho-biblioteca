import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, ClipboardList, RefreshCw, Search, ShieldCheck } from 'lucide-react'

import Button from '../components/ui/Button'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import { listarEventosAuditoria } from '../services/auditoria'
import './auditoria.css'

const LIMITE = 20

const ACOES = [
  ['usuario.criado', 'Usuário criado'],
  ['usuario.atualizado', 'Usuário atualizado'],
  ['usuario.status_alterado', 'Status de usuário alterado'],
  ['livro.criado', 'Livro criado'],
  ['livro.atualizado', 'Livro atualizado'],
  ['emprestimo.criado', 'Empréstimo criado'],
  ['emprestimo.devolvido', 'Empréstimo devolvido'],
  ['renovacao.aprovada', 'Renovação aprovada'],
  ['renovacao.recusada', 'Renovação recusada'],
  ['configuracao.alterada', 'Configuração alterada'],
]

const ENTIDADES = [
  ['usuario', 'Usuário'],
  ['livro', 'Livro'],
  ['emprestimo', 'Empréstimo'],
  ['renovacao', 'Renovação'],
  ['configuracao', 'Configuração'],
]

function rotuloAcao(acao) {
  return ACOES.find(([valor]) => valor === acao)?.[1] || acao || '—'
}

function rotuloEntidade(entidade) {
  return ENTIDADES.find(([valor]) => valor === entidade)?.[1] || entidade || '—'
}

function formatarData(valor) {
  if (!valor) return '—'
  const data = new Date(valor)
  if (Number.isNaN(data.getTime())) return '—'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(data)
}

export default function Auditoria() {
  const [filtros, setFiltros] = useState({ acao: '', entidade: '', entidadeId: '' })
  const [filtrosAplicados, setFiltrosAplicados] = useState(filtros)
  const [eventos, setEventos] = useState([])
  const [total, setTotal] = useState(0)
  const [deslocamento, setDeslocamento] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)

  const carregar = async (filtrosAtuais, offset) => {
    setCarregando(true)
    setFeedback(null)
    try {
      const resposta = await listarEventosAuditoria({
        ...filtrosAtuais,
        limite: LIMITE,
        deslocamento: offset,
      })
      setEventos(Array.isArray(resposta.eventos) ? resposta.eventos : [])
      setTotal(Number(resposta.total) || 0)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    listarEventosAuditoria({
      ...filtrosAplicados,
      limite: LIMITE,
      deslocamento,
    })
      .then((resposta) => {
        if (!ativo) return
        setEventos(Array.isArray(resposta.eventos) ? resposta.eventos : [])
        setTotal(Number(resposta.total) || 0)
        setFeedback(null)
      })
      .catch((erro) => {
        if (ativo) setFeedback({ type: 'error', message: mensagemErroApi(erro) })
      })
      .finally(() => {
        if (ativo) setCarregando(false)
      })
    return () => { ativo = false }
  }, [filtrosAplicados, deslocamento])

  const aplicarFiltros = (event) => {
    event.preventDefault()
    if (filtros.entidadeId && (!/^\d+$/.test(filtros.entidadeId) || Number(filtros.entidadeId) < 1)) {
      setFeedback({ type: 'error', message: 'O ID do registro deve ser um número inteiro positivo.' })
      return
    }
    setFeedback(null)
    setDeslocamento(0)
    setFiltrosAplicados({ ...filtros })
  }

  const limparFiltros = () => {
    const limpos = { acao: '', entidade: '', entidadeId: '' }
    setFiltros(limpos)
    setFiltrosAplicados(limpos)
    setDeslocamento(0)
    setFeedback(null)
  }

  const paginaAtual = Math.floor(deslocamento / LIMITE) + 1
  const totalPaginas = Math.max(1, Math.ceil(total / LIMITE))
  const inicio = total === 0 ? 0 : deslocamento + 1
  const fim = Math.min(deslocamento + eventos.length, total)

  return (
    <section className="page auditoria-page">
      <header className="page-header auditoria-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Auditoria</h1>
          <p>Consulte o histórico de ações administrativas realizadas no sistema.</p>
        </div>
        <div className="auditoria-readonly">
          <ShieldCheck aria-hidden="true" />
          Consulta somente leitura
        </div>
      </header>

      <form className="auditoria-filters" onSubmit={aplicarFiltros}>
        <div className="auditoria-filter-heading">
          <div>
            <h2>Filtrar eventos</h2>
            <p>Combine os filtros para localizar um registro específico.</p>
          </div>
          <ClipboardList aria-hidden="true" />
        </div>

        <div className="auditoria-filter-fields">
          <label>
            <span>Ação</span>
            <select
              value={filtros.acao}
              onChange={(event) => setFiltros((atual) => ({ ...atual, acao: event.target.value }))}
            >
              <option value="">Todas as ações</option>
              {ACOES.map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
            </select>
          </label>

          <label>
            <span>Entidade</span>
            <select
              value={filtros.entidade}
              onChange={(event) => setFiltros((atual) => ({ ...atual, entidade: event.target.value }))}
            >
              <option value="">Todas as entidades</option>
              {ENTIDADES.map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
            </select>
          </label>

          <label>
            <span>ID do registro</span>
            <input
              type="number"
              min="1"
              step="1"
              inputMode="numeric"
              placeholder="Ex.: 125"
              value={filtros.entidadeId}
              onChange={(event) => setFiltros((atual) => ({ ...atual, entidadeId: event.target.value }))}
            />
          </label>
        </div>

        <div className="auditoria-filter-actions">
          <Button type="submit" disabled={carregando}>
            <Search aria-hidden="true" />
            Aplicar filtros
          </Button>
          <Button type="button" variant="ghost" onClick={limparFiltros} disabled={carregando}>
            Limpar
          </Button>
        </div>
      </form>

      {feedback ? <Feedback type={feedback.type} className="auditoria-feedback">{feedback.message}</Feedback> : null}

      <section className="auditoria-results" aria-labelledby="auditoria-results-title">
        <div className="auditoria-results-heading">
          <div>
            <h2 id="auditoria-results-title">Eventos registrados</h2>
            <p>{carregando ? 'Atualizando histórico...' : `${total} evento(s) encontrado(s)`}</p>
          </div>
          <Button
            type="button"
            variant="ghost"
            onClick={() => carregar(filtrosAplicados, deslocamento)}
            disabled={carregando}
            title="Atualizar histórico"
          >
            <RefreshCw aria-hidden="true" />
            Atualizar
          </Button>
        </div>

        <div className="auditoria-table-wrap">
          <table className="auditoria-table">
            <thead>
              <tr>
                <th scope="col">Data e hora</th>
                <th scope="col">Ação</th>
                <th scope="col">Entidade</th>
                <th scope="col">ID do registro</th>
                <th scope="col">ID do administrador</th>
              </tr>
            </thead>
            <tbody>
              {eventos.map((evento) => (
                <tr key={evento.id}>
                  <td data-label="Data e hora">{formatarData(evento.criado_em)}</td>
                  <td data-label="Ação"><span className="auditoria-action">{rotuloAcao(evento.acao)}</span></td>
                  <td data-label="Entidade">{rotuloEntidade(evento.entidade)}</td>
                  <td data-label="ID do registro">{evento.entidade_id ?? '—'}</td>
                  <td data-label="ID do administrador">{evento.ator_id ?? '—'}</td>
                </tr>
              ))}
              {!eventos.length && (
                <tr>
                  <td className="auditoria-empty" colSpan="5">
                    {carregando ? 'Carregando eventos...' : 'Nenhum evento encontrado para os filtros informados.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <footer className="auditoria-pagination">
          <span>{inicio}–{fim} de {total}</span>
          <div>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeslocamento((atual) => Math.max(0, atual - LIMITE))}
              disabled={carregando || deslocamento === 0}
              title="Página anterior"
            >
              <ChevronLeft aria-hidden="true" />
              Anterior
            </Button>
            <span className="auditoria-page-number">Página {paginaAtual} de {totalPaginas}</span>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setDeslocamento((atual) => atual + LIMITE)}
              disabled={carregando || deslocamento + LIMITE >= total}
              title="Próxima página"
            >
              Próxima
              <ChevronRight aria-hidden="true" />
            </Button>
          </div>
        </footer>
      </section>
    </section>
  )
}
