import { useEffect, useMemo, useState } from 'react'
import { BookCheck, History, Plus, RotateCcw, Search } from 'lucide-react'

import EmprestimoFormModal from '../components/emprestimos/EmprestimoFormModal'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import {
  listarEmprestimosAtivos,
  listarHistoricoEmprestimos,
  registrarDevolucao,
  registrarEmprestimo,
} from '../services/emprestimos'
import { listarLivros } from '../services/livros'
import { listarUsuarios } from '../services/usuarios'
import './emprestimos.css'

function formatarData(valor) {
  if (!valor) return '—'
  const data = new Date(`${valor}T00:00:00`)
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleDateString('pt-BR')
}

function textoStatus(status) {
  if (status === 'devolvido') return 'Devolvido'
  if (status === 'atrasado') return 'Atrasado'
  return 'Ativo'
}

export default function Emprestimos() {
  const [ativos, setAtivos] = useState([])
  const [historico, setHistorico] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [livrosDisponiveis, setLivrosDisponiveis] = useState([])
  const [visao, setVisao] = useState('ativos')
  const [busca, setBusca] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [devolvendo, setDevolvendo] = useState(null)

  const carregar = async () => {
    setCarregando(true)
    try {
      const [resAtivos, resHistorico, resUsuarios, resLivros] = await Promise.all([
        listarEmprestimosAtivos(),
        listarHistoricoEmprestimos(),
        listarUsuarios({ incluirInativos: false }),
        listarLivros(),
      ])
      setAtivos(resAtivos.emprestimos || [])
      setHistorico(resHistorico.emprestimos || [])
      setUsuarios(resUsuarios.usuarios || [])
      setLivrosDisponiveis((resLivros.livros || []).filter((livro) => Number(livro.quantidade_disponivel) > 0))
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  const registros = visao === 'ativos' ? ativos : historico
  const filtrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase('pt-BR')
    if (!termo) return registros
    return registros.filter((item) => [
      item.id,
      item.usuario_nome,
      item.usuario_telefone,
      item.livro_titulo,
      item.livro_isbn,
      item.status,
    ].some((valor) => String(valor ?? '').toLocaleLowerCase('pt-BR').includes(termo)))
  }, [busca, registros])

  const salvar = async (dados) => {
    setSalvando(true)
    setFeedback(null)
    try {
      const resposta = await registrarEmprestimo(dados)
      setFeedback({ type: 'success', message: resposta.mensagem })
      setModalAberto(false)
      await carregar()
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setSalvando(false)
    }
  }

  const devolver = async (emprestimo) => {
    const confirmar = window.confirm(
      `Confirmar a devolução de “${emprestimo.livro_titulo}” por ${emprestimo.usuario_nome}?`,
    )
    if (!confirmar) return

    setDevolvendo(emprestimo.id)
    setFeedback(null)
    try {
      const resposta = await registrarDevolucao(emprestimo.id)
      setFeedback({ type: 'success', message: resposta.mensagem })
      await carregar()
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setDevolvendo(null)
    }
  }

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'usuario_nome', label: 'Usuário' },
    {
      key: 'livro_titulo',
      label: 'Livro',
      render: (item) => (
        <div className="emprestimos-book-cell">
          <strong>{item.livro_titulo}</strong>
          <small>{item.livro_isbn || 'ISBN não informado'}</small>
        </div>
      ),
    },
    {
      key: 'data_emprestimo',
      label: 'Retirada',
      render: (item) => formatarData(item.data_emprestimo),
    },
    {
      key: 'data_prevista_devolucao',
      label: 'Prazo',
      render: (item) => formatarData(item.data_prevista_devolucao),
    },
    {
      key: 'status',
      label: 'Situação',
      render: (item) => (
        <span className={`emprestimos-status ${item.status || 'ativo'}`}>
          {textoStatus(item.status)}
        </span>
      ),
    },
    ...(visao === 'historico' ? [{
      key: 'data_devolucao',
      label: 'Devolução',
      render: (item) => formatarData(item.data_devolucao),
    }] : []),
    ...(visao === 'ativos' ? [{
      key: 'acoes',
      label: 'Ações',
      render: (item) => (
        <Button
          type="button"
          variant="ghost"
          className="emprestimos-return-button"
          onClick={() => devolver(item)}
          disabled={devolvendo === item.id}
          title={`Registrar devolução de ${item.livro_titulo}`}
        >
          <RotateCcw aria-hidden="true" />
          {devolvendo === item.id ? 'Devolvendo...' : 'Devolver'}
        </Button>
      ),
    }] : []),
  ]

  return (
    <section className="page emprestimos-page">
      <header className="page-header emprestimos-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Empréstimos</h1>
          <p>Registre retiradas, acompanhe prazos e devolva exemplares ao acervo.</p>
        </div>
        <Button type="button" onClick={() => { setModalAberto(true); setFeedback(null) }}>
          <Plus aria-hidden="true" />
          Novo empréstimo
        </Button>
      </header>

      <div className="emprestimos-tabs" role="tablist" aria-label="Visualização dos empréstimos">
        <button
          type="button"
          className={visao === 'ativos' ? 'active' : ''}
          onClick={() => setVisao('ativos')}
          role="tab"
          aria-selected={visao === 'ativos'}
        >
          <BookCheck aria-hidden="true" /> Em aberto <span>{ativos.length}</span>
        </button>
        <button
          type="button"
          className={visao === 'historico' ? 'active' : ''}
          onClick={() => setVisao('historico')}
          role="tab"
          aria-selected={visao === 'historico'}
        >
          <History aria-hidden="true" /> Histórico <span>{historico.length}</span>
        </button>
      </div>

      <div className="emprestimos-toolbar">
        <label className="emprestimos-search">
          <span className="sr-only">Pesquisar empréstimos</span>
          <Search aria-hidden="true" />
          <input
            type="search"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Pesquisar por usuário, livro, ISBN, status ou ID..."
            aria-label="Pesquisar empréstimos"
          />
        </label>
        <span className="emprestimos-count">
          {carregando ? 'Carregando...' : `${filtrados.length} registro(s)`}
        </span>
      </div>

      {feedback ? <Feedback type={feedback.type} className="emprestimos-feedback">{feedback.message}</Feedback> : null}

      <DataTable
        columns={columns}
        rows={filtrados}
        emptyMessage={carregando ? 'Carregando empréstimos...' : visao === 'ativos' ? 'Nenhum empréstimo em aberto.' : 'Nenhum empréstimo no histórico.'}
      />

      {modalAberto ? (
        <EmprestimoFormModal
          usuarios={usuarios}
          livros={livrosDisponiveis}
          saving={salvando}
          onSave={salvar}
          onClose={() => { if (!salvando) setModalAberto(false) }}
        />
      ) : null}
    </section>
  )
}
