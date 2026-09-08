import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import loginReading from '../assets/auth/login-reading.webp'
import { useAuth } from '../auth/AuthContext'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Feedback from '../components/ui/Feedback'
import TextField from '../components/ui/TextField'
import { mensagemErroApi } from '../services/api'
import { emailValido, obrigatorio } from '../utils/validation'
import './login.css'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { authenticated, entrar, loading } = useAuth()
  const [feedback, setFeedback] = useState(location.state?.message || '')
  const [feedbackType, setFeedbackType] = useState(location.state?.message ? 'success' : 'info')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ email: '', senha: '' })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!loading && authenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [authenticated, loading, navigate])

  const atualizarCampo = (campo) => (event) => {
    setForm((atual) => ({ ...atual, [campo]: event.target.value }))
    setErrors((atual) => ({ ...atual, [campo]: '' }))
    setFeedback('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const novosErros = {}

    if (!obrigatorio(form.email)) {
      novosErros.email = 'Informe o e-mail.'
    } else if (!emailValido(form.email)) {
      novosErros.email = 'Digite um e-mail válido, por exemplo nome@dominio.com.'
    }

    if (!obrigatorio(form.senha)) {
      novosErros.senha = 'Informe a senha.'
    }

    setErrors(novosErros)
    if (Object.keys(novosErros).length > 0) return

    setSubmitting(true)
    setFeedback('')

    try {
      await entrar(form.email, form.senha)
      const destino = location.state?.from || '/dashboard'
      navigate(destino, { replace: true })
    } catch (error) {
      setFeedbackType('error')
      setFeedback(mensagemErroApi(error))
    } finally {
      setSubmitting(false)
    }
  }

  const showFutureFeature = (feature) => {
    setFeedbackType('info')
    setFeedback(feature)
  }

  return (
    <main className="login-page">
      <div className="login-layout">
        <section className="login-visual" aria-label="Ilustração de leitura e biblioteca">
          <img className="login-artwork" src={loginReading} alt="Pessoa lendo ao lado de livros e uma estante" />
        </section>

        <Card className="login-panel" as="section">
          <h1 className="login-title">FAÇA LOGIN</h1>

          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <TextField
              id="login-email"
              label="E-mail:"
              type="email"
              autoComplete="email"
              placeholder="Digite seu e-mail"
              value={form.email}
              onChange={atualizarCampo('email')}
              error={errors.email}
              tooltip="Informe o e-mail da sua conta administrativa do BiblioAvisa."
            />

            <TextField
              id="login-password"
              label="Senha:"
              type="password"
              autoComplete="current-password"
              placeholder="Digite sua senha"
              value={form.senha}
              onChange={atualizarCampo('senha')}
              error={errors.senha}
              tooltip="A senha é verificada pelo backend e nunca é armazenada em texto puro."
            />

            <div className="login-socials" aria-label="Opções futuras de acesso social">
              <button
                className="login-social-button login-social-google"
                type="button"
                aria-label="Entrar com Google"
                onClick={() => showFutureFeature('O acesso com Google ainda não está habilitado.')}
              >
                G
              </button>
              <button
                className="login-social-button login-social-facebook"
                type="button"
                aria-label="Entrar com Facebook"
                onClick={() => showFutureFeature('O acesso com Facebook ainda não está habilitado.')}
              >
                f
              </button>
            </div>

            <Button className="login-submit" variant="dark" type="submit" disabled={submitting || loading}>
              {submitting ? 'Entrando...' : 'Entrar'}
            </Button>

            <p className="login-no-account">NÃO TEM UMA CONTA?</p>
            <button
              className="login-create-account"
              type="button"
              onClick={() => navigate('/cadastro')}
            >
              CRIE SUA CONTA
            </button>

            {feedback ? (
              <Feedback className="login-feedback" type={feedbackType}>
                {feedback}
              </Feedback>
            ) : null}
          </form>
        </Card>
      </div>
    </main>
  )
}
