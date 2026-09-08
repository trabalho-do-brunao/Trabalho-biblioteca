import { UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'

export default function Configuracoes() {
  const navigate = useNavigate()

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <span className="page-eyebrow">Administração</span>
          <h1>Configurações</h1>
          <p>Preferências e opções administrativas do BiblioAvisa.</p>
        </div>
      </header>

      <Card className="page-card">
        <div className="api-health-card">
          <UserPlus aria-hidden="true" />
          <div style={{ flex: 1 }}>
            <strong>Contas administrativas</strong>
            <p>Cadastre outra pessoa autorizada a acessar o painel administrativo.</p>
          </div>
          <Button variant="primary" type="button" onClick={() => navigate('/cadastro')}>
            Cadastrar administrador
          </Button>
        </div>
      </Card>
    </div>
  )
}
