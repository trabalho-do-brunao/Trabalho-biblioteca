import { useMemo, useState } from 'react'
import { Download, ExternalLink, FileText, Mail, RefreshCcw } from 'lucide-react'

import Button from '../components/ui/Button'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import { enviarRelatorioEmail, gerarRelatorioPdf } from '../services/relatorios'
import './relatorios.css'

function isoLocal(data) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function periodoPadrao() {
  const hoje = new Date()
  const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
  return {
    dataInicio: isoLocal(inicio),
    dataFim: isoLocal(hoje),
  }
}

function validarPeriodo(dataInicio, dataFim) {
  if (!dataInicio || !dataFim) return 'Informe a data inicial e a data final.'
  if (dataInicio > dataFim) return 'A data inicial não pode ser posterior à data final.'
  return null
}

export default function Relatorios() {
  const padrao = useMemo(() => periodoPadrao(), [])
  const [dataInicio, setDataInicio] = useState(padrao.dataInicio)
  const [dataFim, setDataFim] = useState(padrao.dataFim)
  const [feedback, setFeedback] = useState(null)
  const [gerando, setGerando] = useState(false)
  const [enviando, setEnviando] = useState(false)

  const gerar = async (modo) => {
    const erroPeriodo = validarPeriodo(dataInicio, dataFim)
    if (erroPeriodo) {
      setFeedback({ type: 'error', message: erroPeriodo })
      return
    }

    setGerando(true)
    setFeedback(null)
    try {
      const { blob, filename } = await gerarRelatorioPdf(dataInicio, dataFim)
      const url = URL.createObjectURL(blob)

      if (modo === 'abrir') {
        const novaAba = window.open(url, '_blank', 'noopener,noreferrer')
        if (!novaAba) {
          setFeedback({ type: 'info', message: 'O navegador bloqueou a nova aba. Use “Baixar PDF” para acessar o relatório.' })
        } else {
          setFeedback({ type: 'success', message: 'Relatório gerado e aberto em uma nova aba.' })
        }
        window.setTimeout(() => URL.revokeObjectURL(url), 60000)
        return
      }

      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      setFeedback({ type: 'success', message: 'Relatório PDF gerado e baixado com sucesso.' })
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setGerando(false)
    }
  }

  const enviarEmail = async () => {
    const erroPeriodo = validarPeriodo(dataInicio, dataFim)
    if (erroPeriodo) {
      setFeedback({ type: 'error', message: erroPeriodo })
      return
    }

    setEnviando(true)
    setFeedback(null)
    try {
      const resposta = await enviarRelatorioEmail(dataInicio, dataFim)
      setFeedback({ type: 'success', message: resposta.mensagem || 'Relatório enviado por e-mail.' })
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setEnviando(false)
    }
  }

  const restaurarPeriodo = () => {
    const novo = periodoPadrao()
    setDataInicio(novo.dataInicio)
    setDataFim(novo.dataFim)
    setFeedback(null)
  }

  return (
    <section className="page relatorios-page">
      <header className="page-header relatorios-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Relatórios</h1>
          <p>Gere o relatório operacional da biblioteca e, quando configurado, envie-o por e-mail.</p>
        </div>
      </header>

      <div className="relatorios-grid">
        <section className="relatorios-panel" aria-labelledby="periodo-relatorio">
          <div className="relatorios-panel-heading">
            <div className="relatorios-icon"><FileText aria-hidden="true" /></div>
            <div>
              <h2 id="periodo-relatorio">Período do relatório</h2>
              <p>O PDF usa as mesmas regras de relatório já existentes no backend.</p>
            </div>
          </div>

          <div className="relatorios-periodo">
            <label>
              <span>Data inicial</span>
              <input
                type="date"
                value={dataInicio}
                onChange={(event) => setDataInicio(event.target.value)}
                max={dataFim || undefined}
                title="Primeiro dia incluído no relatório"
              />
            </label>
            <label>
              <span>Data final</span>
              <input
                type="date"
                value={dataFim}
                onChange={(event) => setDataFim(event.target.value)}
                min={dataInicio || undefined}
                title="Último dia incluído no relatório"
              />
            </label>
          </div>

          <button
            type="button"
            className="relatorios-reset"
            onClick={restaurarPeriodo}
            title="Voltar ao período do mês atual"
          >
            <RefreshCcw aria-hidden="true" />
            Usar mês atual
          </button>
        </section>

        <section className="relatorios-panel relatorios-actions-panel" aria-labelledby="acoes-relatorio">
          <div>
            <h2 id="acoes-relatorio">Gerar relatório</h2>
            <p>O arquivo inclui mensagens enviadas, empréstimos atrasados e próximos do vencimento.</p>
          </div>

          <div className="relatorios-actions">
            <Button
              type="button"
              onClick={() => gerar('abrir')}
              disabled={gerando || enviando}
              title="Gerar o PDF e abrir em uma nova aba"
            >
              <ExternalLink aria-hidden="true" />
              {gerando ? 'Gerando...' : 'Abrir PDF'}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => gerar('baixar')}
              disabled={gerando || enviando}
              title="Gerar o PDF e salvar no computador"
            >
              <Download aria-hidden="true" />
              Baixar PDF
            </Button>

            <Button
              type="button"
              variant="dark"
              onClick={enviarEmail}
              disabled={gerando || enviando}
              title="Gerar o relatório e enviar ao destinatário configurado no servidor"
            >
              <Mail aria-hidden="true" />
              {enviando ? 'Enviando...' : 'Enviar por e-mail'}
            </Button>
          </div>

          <p className="relatorios-security-note">
            O endereço e as credenciais SMTP permanecem no servidor e não são exibidos nesta tela.
          </p>
        </section>
      </div>

      {feedback ? (
        <Feedback type={feedback.type} className="relatorios-feedback">{feedback.message}</Feedback>
      ) : null}
    </section>
  )
}
