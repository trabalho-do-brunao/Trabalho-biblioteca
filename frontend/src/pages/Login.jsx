import { useState } from 'react'
import { LibraryBig } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Feedback from '../components/ui/Feedback'
import TextField from '../components/ui/TextField'
import { emailValido, obrigatorio } from '../utils/validation'
import './login.css'

export default function Login() {
  const navigate = useNavigate()
  const [feedback, setFeedback] = useState('')
  const [form, setForm] = useState({ email: '', senha: '' })
  const [errors, setErrors] = useState({})

  const atualizarCampo = (campo) => (event) => {
    setForm((atual) => ({ ...atual, [campo]: event.target.value }))
    setErrors((atual) => ({ ...atual, [campo]: '' }))
  }

  const handleSubmit = (event) => {
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

    if (Object.keys(novosErros).length === 0) {
      navigate('/dashboard')
    }
  }

  const showFutureFeature = (feature) => {
    setFeedback(`${feature} será conectado em uma etapa posterior do projeto.`)
  }

  return (
    <main className="login-page">
      <section className="login-visual" aria-label="Ilustração da biblioteca">
        <div className="login-library-scene">
          <LibraryBig className="login-library-icon" aria-hidden="true" />
          <div className="login-library-books" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <p className="login-visual-caption">
            Organize o acervo, acompanhe empréstimos e mantenha os leitores informados.
          </p>
        </div>
      </section>

      <Card className="login-panel" as="section">
        <h1 className="login-title">FAÇA LOGIN</h1>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <TextField
            id="login-email"
            label="E-mail:"
            type="email"
            autoComplete="email"
            placeholder="Digite seu E-mail"
            value={form.email}
            onChange={atualizarCampo('email')}
            error={errors.email}
            tooltip="Use um endereço no formato nome@dominio.com. Nesta etapa o login ainda é apenas de desenvolvimento."
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
            tooltip="Campo obrigatório para validar o formulário. A autenticação real será implementada em uma etapa específica."
          />

          <div className="login-socials" aria-label="Opções futuras de acesso social">
            <button
              className="login-social-button login-social-google"
              type="button"
              aria-label="Entrar com Google"
              onClick={() => showFutureFeature('O acesso com Google')}
            >
              G
            </button>
            <button
              className="login-social-button login-social-facebook"
              type="button"
              aria-label="Entrar com Facebook"
              onClick={() => showFutureFeature('O acesso com Facebook')}
            >
              f
            </button>
          </div>

          <Button className="login-submit" variant="dark" type="submit">
            Entrar
          </Button>

          <button
            className="login-create-account"
            type="button"
            onClick={() => showFutureFeature('O cadastro de conta')}
          >
            Ou crie sua conta
          </button>

          {feedback ? (
            <Feedback className="login-feedback" type="info">
              {feedback}
            </Feedback>
          ) : null}
        </form>
      </Card>
    </main>
  )
}
