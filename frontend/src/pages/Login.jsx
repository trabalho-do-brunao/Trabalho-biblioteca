import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Feedback from '../components/ui/Feedback'
import TextField from '../components/ui/TextField'
import { mensagemErroApi } from '../services/api'
import { emailValido, obrigatorio } from '../utils/validation'
import './login.css'

function LoginArtwork() {
  return (
    <svg
      className="login-artwork"
      viewBox="0 0 640 500"
      aria-hidden="true"
      focusable="false"
    >
      <ellipse cx="318" cy="438" rx="238" ry="18" fill="rgba(0, 29, 91, 0.18)" />

      <g className="login-artwork-shelf">
        <rect x="390" y="174" width="170" height="226" rx="9" fill="#ff806f" />
        <rect x="405" y="190" width="140" height="176" rx="4" fill="#ffac75" />
        <rect x="405" y="244" width="140" height="8" fill="#d95f68" />
        <rect x="405" y="310" width="140" height="8" fill="#d95f68" />
        <rect x="405" y="365" width="140" height="8" fill="#d95f68" />
        <rect x="420" y="204" width="16" height="38" rx="3" fill="#1d4ed8" />
        <rect x="439" y="198" width="14" height="44" rx="3" fill="#ef3d78" />
        <rect x="456" y="207" width="15" height="35" rx="3" fill="#7c3aed" />
        <rect x="491" y="210" width="37" height="8" rx="3" fill="#2dd4bf" />
        <rect x="487" y="221" width="43" height="8" rx="3" fill="#f43f5e" />
        <rect x="430" y="268" width="64" height="10" rx="3" fill="#2563eb" />
        <rect x="444" y="281" width="58" height="10" rx="3" fill="#f43f5e" />
        <rect x="505" y="327" width="20" height="38" rx="3" fill="#7c3aed" />
        <rect x="481" y="337" width="20" height="28" rx="3" fill="#14b8a6" />
      </g>

      <g className="login-artwork-books">
        <rect x="96" y="354" width="134" height="38" rx="5" fill="#ff536f" />
        <rect x="111" y="343" width="160" height="16" rx="4" fill="#ffb36d" />
        <rect x="126" y="327" width="154" height="16" rx="4" fill="#65d9bf" />
        <rect x="204" y="389" width="160" height="42" rx="6" fill="#ec3f70" />
        <rect x="204" y="382" width="164" height="10" rx="4" fill="#ff9f6a" />
        <rect x="363" y="391" width="40" height="40" rx="4" fill="#ffbd80" />
      </g>

      <g className="login-artwork-person">
        <path d="M180 282c17-53 80-71 119-37 24 22 31 63 19 108H174c-9-25-6-50 6-71Z" fill="#54d6b7" />
        <path d="M192 350h116l-11 49h-44l-11-27-16 27h-53Z" fill="#083a73" />
        <circle cx="238" cy="154" r="52" fill="#ffad93" />
        <path d="M189 151c1-43 25-73 58-73 35 0 61 28 59 65-14-8-25-23-31-42-22 20-50 26-86 22Z" fill="#06184d" />
        <path d="M282 89c5-18 17-27 34-26-4 12-13 21-27 27Z" fill="#06184d" />
        <path d="M207 166c12 10 22 10 34 0" fill="none" stroke="#06184d" strokeWidth="5" strokeLinecap="round" />
        <path d="M258 166c12 10 22 10 34 0" fill="none" stroke="#06184d" strokeWidth="5" strokeLinecap="round" />
        <path d="M244 192c9 7 21 8 31 1" fill="none" stroke="#cb4b63" strokeWidth="4" strokeLinecap="round" />
        <path d="M176 265c-24 11-39 30-47 56" fill="none" stroke="#ffad93" strokeWidth="18" strokeLinecap="round" />
        <path d="M303 267c28 16 46 38 57 66" fill="none" stroke="#ffad93" strokeWidth="18" strokeLinecap="round" />
        <g transform="translate(105 220) rotate(-15 78 72)">
          <rect x="20" y="12" width="145" height="145" rx="8" fill="#7578df" />
          <rect x="32" y="22" width="122" height="125" rx="5" fill="#8b8de8" />
          <path d="M93 23v124" stroke="#6769ce" strokeWidth="4" />
          <path d="M32 26c25 4 45 9 61 18 17-9 38-14 61-18v121c-25-2-45 2-61 11-16-9-36-13-61-11Z" fill="#7c7fe1" />
        </g>
      </g>
    </svg>
  )
}

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
      <section className="login-visual" aria-label="Ilustração de leitura e biblioteca">
        <LoginArtwork />
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

          <button
            className="login-create-account"
            type="button"
            onClick={() => navigate('/cadastro')}
          >
            OU CRIE SUA CONTA
          </button>

          {feedback ? (
            <Feedback className="login-feedback" type={feedbackType}>
              {feedback}
            </Feedback>
          ) : null}
        </form>
      </Card>
    </main>
  )
}
