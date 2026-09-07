import { useCallback, useEffect, useState } from 'react'
import {
  BookOpenCheck,
  CalendarClock,
  Clock3,
  Library,
  RefreshCw,
  TriangleAlert,
  UsersRound,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import { carregarDashboard } from '../services/dashboard'
import './dashboard.css'

function formatarData(valor) {
  if (!valor) return '—'
  const [ano, mes, dia] = String(valor).slice(0, 10).split('-')
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : String(valor)
}

function textoSituacao(item) {
  const dias = Number(item.dias || 0)
  if (item.situacao === 'atrasado') {
    return dias === 1 ? '1 dia em atraso' : `${dias} dias em atraso`
  }
  if (item.situacao === 'vence_hoje') return 'Vence hoje'
  if (dias === 1) return 'Vence amanhã'
  return `Vence em ${dias} dias`
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setFeedback(null)
    try {
      const resposta = await carregarDashboard({ diasProximos: 2, limite: 10 })
      setDados(resposta)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  const resumo = dados?.resumo || {}
  const atencao = dados?.atencao || []

  const metricas = [
    {
      label: 'Empréstimos em aberto',
      value: resumo.emprestimos_abertos ?? '—',
      detail: 'Empréstimos ainda não devolvidos',
      icon: BookOpenCheck,
      tone: 'primary',
      onClick: () => navigate('/emprestimos'),
    },
    {
      label: 'Próximos do vencimento',
      value: resumo.proximos_vencimento ?? '—',
      detail: 'Vencem hoje ou nos próximos 2 dias',
      icon: Clock3,
      tone: 'warning',
      onClick: () => navigate('/emprestimos'),
    },
    {
      label: 'Empréstimos atrasados',
      value: resumo.emprestimos_atrasados ?? '—',
      detail: 'Precisam de atenção imediata',
      icon: TriangleAlert,
      tone: 'danger',
      onClick: () => navigate('/emprestimos'),
    },
    {
      label: 'Exemplares disponíveis',
      value: resumo.exemplares_disponiveis ?? '—',
      detail: `${resumo.titulos_cadastrados ?? 0} título(s) no acervo`,
      icon: Library,
      tone: 'success',
      onClick: () => navigate('/livros'),
    },
  ]

  const columns = [
    {
      key: 'usuario_nome',
      label: 'Usuário',
      render: (item) => (
        <button
          type="button"
          className="dashboard-table-link"
          onClick={() => navigate(`/usuarios?busca=${encodeURIComponent(item.usuario_id)}`)}
          title="Abrir usuário"
        >
          {item.usuario_nome}
        </button>
      ),
    },
    {
      key: 'livro_titulo',
      label: 'Livro',
      render: (item) => (
        <button
          type="button"
          className="dashboard-table-link"
          onClick={() => navigate(`/livros?busca=${encodeURIComponent(item.livro_id)}`)}
          title="Abrir livro"
        >
          {item.livro_titulo}
        </button>
      ),
    },
    {
      key: 'data_prevista_devolucao',
      label: 'Devolução prevista',
      render: (item) => formatarData(item.data_prevista_devolucao),
    },
    {
      key: 'situacao',
      label: 'Situação',
      render: (item) => (
        <span className={`dashboard-status ${item.situacao}`}>
          {textoSituacao(item)}
        </span>
      ),
    },
  ]

  return (
    <section className="page dashboard-page">
      <header className="page-header dashboard-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Dashboard</h1>
          <p>Acompanhe rapidamente o acervo, os empréstimos e situações que precisam de atenção.</p>
        </div>
        <Button type="button" variant="ghost" onClick={carregar} disabled={carregando}>
          <RefreshCw className={carregando ? 'spin' : ''} aria-hidden="true" />
          {carregando ? 'Atualizando...' : 'Atualizar'}
        </Button>
      </header>

      {feedback ? <Feedback type={feedback.type}>{feedback.message}</Feedback> : null}

      <div className="dashboard-metrics" aria-label="Indicadores da biblioteca">
        {metricas.map((metrica) => {
          const Icon = metrica.icon
          return (
            <button
              key={metrica.label}
              type="button"
              className={`dashboard-metric dashboard-metric-${metrica.tone}`}
              onClick={metrica.onClick}
            >
              <span className="dashboard-metric-icon"><Icon aria-hidden="true" /></span>
              <span className="dashboard-metric-content">
                <span className="dashboard-metric-label">{metrica.label}</span>
                <strong>{carregando && !dados ? '…' : metrica.value}</strong>
                <small>{metrica.detail}</small>
              </span>
            </button>
          )
        })}
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-panel dashboard-attention">
          <div className="dashboard-panel-header">
            <div>
              <span className="dashboard-panel-icon"><CalendarClock aria-hidden="true" /></span>
              <div>
                <h2>Empréstimos que exigem atenção</h2>
                <p>Atrasados e vencimentos previstos até dois dias.</p>
              </div>
            </div>
            <button type="button" className="dashboard-text-action" onClick={() => navigate('/emprestimos')}>
              Ver empréstimos
            </button>
          </div>

          <DataTable
            columns={columns}
            rows={atencao}
            emptyMessage={carregando ? 'Carregando empréstimos...' : 'Nenhum empréstimo exige atenção agora.'}
          />
        </section>

        <aside className="dashboard-panel dashboard-shortcuts">
          <div className="dashboard-panel-header compact">
            <div>
              <h2>Acesso rápido</h2>
              <p>Atalhos para as rotinas mais usadas.</p>
            </div>
          </div>

          <button type="button" onClick={() => navigate('/emprestimos')}>
            <BookOpenCheck aria-hidden="true" />
            <span><strong>Empréstimos</strong><small>Registrar retirada ou devolução</small></span>
          </button>
          <button type="button" onClick={() => navigate('/livros')}>
            <Library aria-hidden="true" />
            <span><strong>Livros</strong><small>Consultar acervo e disponibilidade</small></span>
          </button>
          <button type="button" onClick={() => navigate('/usuarios')}>
            <UsersRound aria-hidden="true" />
            <span><strong>Usuários</strong><small>{resumo.usuarios_ativos ?? 0} usuário(s) ativo(s)</small></span>
          </button>
        </aside>
      </div>
    </section>
  )
}
