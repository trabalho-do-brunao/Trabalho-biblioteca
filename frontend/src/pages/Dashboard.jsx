import { useEffect, useState } from 'react'
import { CircleCheck, CircleX, LoaderCircle } from 'lucide-react'

import { verificarSaudeApi } from '../services/api'

export default function Dashboard() {
  const [api, setApi] = useState({ status: 'carregando', mensagem: 'Verificando API Python...' })

  useEffect(() => {
    let ativo = true

    verificarSaudeApi()
      .then((dados) => {
        if (ativo) {
          setApi({ status: 'ok', mensagem: `${dados.service} conectada (${dados.environment})` })
        }
      })
      .catch((erro) => {
        if (ativo) {
          setApi({ status: 'erro', mensagem: erro.message })
        }
      })

    return () => {
      ativo = false
    }
  }, [])

  const Icon = api.status === 'ok' ? CircleCheck : api.status === 'erro' ? CircleX : LoaderCircle

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Dashboard</h1>
          <p>A estrutura visual está pronta para receber o dashboard definitivo do Figma.</p>
        </div>
      </header>

      <div className="page-card api-health-card">
        <Icon className={api.status === 'carregando' ? 'spin' : ''} aria-hidden="true" />
        <div>
          <strong>Conexão React → Python</strong>
          <p className={`api-status ${api.status}`}>{api.mensagem}</p>
        </div>
      </div>
    </section>
  )
}
