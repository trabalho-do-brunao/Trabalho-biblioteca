import { useEffect, useMemo, useState } from 'react'
import {
  ArrowDownLeft,
  ArrowUpRight,
  Clock3,
  Inbox,
  MessageCircle,
  RefreshCw,
  Search,
  Send,
  TriangleAlert,
} from 'lucide-react'

import Button from '../components/ui/Button'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import { listarMensagensWhatsapp } from '../services/whatsapp'
import './whatsapp.css'

const TIPOS = [
  ['', 'Todos os tipos'],
  ['aviso_2_dias', 'Aviso de 2 dias'],
  ['aviso_vencimento', 'Aviso de vencimento'],
  ['aviso_atraso', 'Aviso de atraso'],
  ['solicitacao_renovacao', 'Solicitação de renovação'],
  ['confirmacao_renovacao', 'Confirmação de renovação'],
  ['recusa_renovacao', 'Recusa de renovação'],
  ['consulta', 'Consulta'],
  ['outro', 'Outro'],
]

const STATUS = [
  ['', 'Todos os status'],
  ['pendente', 'Pendente'],
  ['enviado', 'Enviado'],
  ['recebido', 'Recebido'],
  ['falha', 'Falha'],
]

function formatarDataHora(valor) {
  if (!valor) return '—'
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? String(valor) : data.toLocaleString('pt-BR')
}

function formatarData(valor) {
  if (!valor) return '—'
  const data = new Date(`${valor}T00:00:00`)
  return Number.isNaN(data.getTime()) ? String(valor) : data.toLocaleDateString('pt-BR')
}

function textoTipo(tipo) {
  return TIPOS.find(([valor]) => valor === tipo)?.[1] || tipo || 'Outro'
}

function textoStatus(status) {
  return STATUS.find(([valor]) => valor === status)?.[1] || status || '—'
}

function ResumoCard({ icon: Icon, label, value, detail, tone = 'default' }) {
  return (
    <article className={`whatsapp-summary-card ${tone}`}>
      <span className="whatsapp-summary-icon"><Icon aria-hidden="true" /></span>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {detail ? <small>{detail}</small> : null}
      </div>
    </article>
  )
}

function ResultadoRenovacao({ mensagem }) {
  if (!mensagem.renovacao_status) return null

  const aprovada = mensagem.renovacao_status === 'aprovada'
  return (
    <div className={`whatsapp-renewal ${aprovada ? 'approved' : 'rejected'}`}>
      <strong>Renovação {aprovada ? 'aprovada' : 'recusada'}</strong>
      {aprovada ? (
        <span>
          Prazo alterado de {formatarData(mensagem.renovacao_data_anterior)} para{' '}
          {formatarData(mensagem.renovacao_nova_data)}.
        </span>
      ) : (
        <span>{mensagem.renovacao_motivo_recusa || 'Solicitação recusada pelo sistema.'}</span>
      )}
    </div>
  )
}

export default function WhatsApp() {
  const [mensagens, setMensagens] = useState([])
  const [resumo, setResumo] = useState({ total: 0, enviadas: 0, recebidas: 0, pendentes: 0, falhas: 0 })
  const [busca, setBusca] = useState('')
  const [status, setStatus] = useState('')
  const [tipo, setTipo] = useState('')
  const [direcao, setDirecao] = useState('')
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)

  const filtros = useMemo(() => ({
    busca,
    status,
    tipo,
    direcao,
    dataInicio,
    dataFim,
  }), [busca, status, tipo, direcao, dataInicio, dataFim])

  const carregar = async () => {
    setCarregando(true)
    try {
      const resposta = await listarMensagensWhatsapp(filtros)
      setMensagens(resposta.mensagens || [])
      setResumo(resposta.resumo || { total: 0, enviadas: 0, recebidas: 0, pendentes: 0, falhas: 0 })
      setFeedback(null)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(carregar, 250)
    return () => window.clearTimeout(timer)
  }, [filtros])

  const limparFiltros = () => {
    setBusca('')
    setStatus('')
    setTipo('')
    setDirecao('')
    setDataInicio('')
    setDataFim('')
  }

  return (
    <section className="page whatsapp-page">
      <header className="page-header whatsapp-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>WhatsApp</h1>
          <p>Acompanhe avisos, respostas dos leitores e resultados de renovação.</p>
        </div>
        <Button type="button" variant="ghost" onClick={carregar} disabled={carregando}>
          <RefreshCw className={carregando ? 'spin' : ''} aria-hidden="true" />
          Atualizar
        </Button>
      </header>

      <div className="whatsapp-summary-grid">
        <ResumoCard icon={MessageCircle} label="Mensagens" value={resumo.total ?? 0} detail="histórico registrado" />
        <ResumoCard icon={Send} label="Enviadas" value={resumo.enviadas ?? 0} detail={`${resumo.pendentes ?? 0} pendente(s)`} tone="sent" />
        <ResumoCard icon={Inbox} label="Recebidas" value={resumo.recebidas ?? 0} detail="respostas e consultas" tone="received" />
        <ResumoCard icon={TriangleAlert} label="Falhas" value={resumo.falhas ?? 0} detail="exigem atenção" tone="failure" />
      </div>

      <div className="whatsapp-filters">
        <label className="whatsapp-search">
          <span className="sr-only">Pesquisar mensagens</span>
          <Search aria-hidden="true" />
          <input
            type="search"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Pesquisar usuário, livro, mensagem ou ID..."
            aria-label="Pesquisar mensagens"
          />
        </label>

        <select value={direcao} onChange={(event) => setDirecao(event.target.value)} aria-label="Filtrar por direção">
          <option value="">Enviadas e recebidas</option>
          <option value="enviada">Enviadas</option>
          <option value="recebida">Recebidas</option>
        </select>

        <select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filtrar por status">
          {STATUS.map(([valor, label]) => <option key={valor || 'todos'} value={valor}>{label}</option>)}
        </select>

        <select value={tipo} onChange={(event) => setTipo(event.target.value)} aria-label="Filtrar por tipo">
          {TIPOS.map(([valor, label]) => <option key={valor || 'todos'} value={valor}>{label}</option>)}
        </select>

        <label className="whatsapp-date-filter">
          <span>De</span>
          <input type="date" value={dataInicio} onChange={(event) => setDataInicio(event.target.value)} />
        </label>

        <label className="whatsapp-date-filter">
          <span>Até</span>
          <input type="date" value={dataFim} onChange={(event) => setDataFim(event.target.value)} />
        </label>

        <button type="button" className="whatsapp-clear-filters" onClick={limparFiltros}>Limpar filtros</button>
      </div>

      {feedback ? <Feedback type={feedback.type} className="whatsapp-feedback">{feedback.message}</Feedback> : null}

      <div className="whatsapp-list-header">
        <div>
          <h2>Histórico de mensagens</h2>
          <p>{carregando ? 'Atualizando...' : `${mensagens.length} mensagem(ns) encontrada(s)`}</p>
        </div>
        <span className="whatsapp-security-note">Credenciais e sessão do WhatsApp não são exibidas nesta tela.</span>
      </div>

      <div className="whatsapp-message-list" aria-live="polite">
        {!carregando && mensagens.length === 0 ? (
          <div className="whatsapp-empty">
            <MessageCircle aria-hidden="true" />
            <strong>Nenhuma mensagem encontrada.</strong>
            <span>Ajuste os filtros ou aguarde novos registros do BiblioAvisa.</span>
          </div>
        ) : null}

        {mensagens.map((mensagem) => {
          const enviada = mensagem.direcao === 'enviada'
          const DirecaoIcon = enviada ? ArrowUpRight : ArrowDownLeft
          return (
            <article className={`whatsapp-message-card ${enviada ? 'outgoing' : 'incoming'}`} key={mensagem.id}>
              <div className="whatsapp-message-direction">
                <DirecaoIcon aria-hidden="true" />
              </div>

              <div className="whatsapp-message-content">
                <div className="whatsapp-message-meta">
                  <div>
                    <strong>{mensagem.usuario_nome}</strong>
                    <span>
                      {enviada ? 'Enviada pelo sistema' : 'Recebida do usuário'}
                      {mensagem.emprestimo_id ? ` · Empréstimo #${mensagem.emprestimo_id}` : ''}
                    </span>
                    {mensagem.livro_titulo ? <small>{mensagem.livro_titulo}</small> : null}
                  </div>
                  <time>{formatarDataHora(mensagem.data_mensagem)}</time>
                </div>

                <div className="whatsapp-message-tags">
                  <span className={`whatsapp-status ${mensagem.status}`}>{textoStatus(mensagem.status)}</span>
                  <span className="whatsapp-type">{textoTipo(mensagem.tipo)}</span>
                </div>

                <p className="whatsapp-message-text">{mensagem.mensagem}</p>
                <ResultadoRenovacao mensagem={mensagem} />
              </div>
            </article>
          )
        })}
      </div>

      {carregando ? (
        <div className="whatsapp-loading"><Clock3 className="spin" aria-hidden="true" /> Carregando histórico...</div>
      ) : null}
    </section>
  )
}
