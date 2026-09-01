import { Link } from 'react-router-dom'

export default function Login() {
  return (
    <main className="login-foundation">
      <div className="login-foundation-card">
        <span className="login-foundation-brand">BiblioAvisa</span>
        <h1>Tela de acesso</h1>
        <p>O layout definitivo do login será implementado na próxima etapa a partir do Figma.</p>
        <Link to="/dashboard" className="primary-button">Entrar no protótipo</Link>
      </div>
    </main>
  )
}
