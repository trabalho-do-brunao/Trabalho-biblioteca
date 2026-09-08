import { useEffect, useState } from 'react'
import { ArrowLeft, LibraryBig, UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Feedback from '../components/ui/Feedback'
import TextField from '../components/ui/TextField'
import {
  cadastrarAdministrador,
  consultarStatusCadastroAdministrador,
  mensagemErroApi,
} from '../services/api'
import { somenteDigitos } from '../utils/masks'
import { cpfValido, dataBrValida, emailValido, obrigatorio } from '../utils/validation'
import './cadastro.css'

const FORM_INICIAL = {
  nome: '',
  sobrenome: '',
  cpf: '',
  dataNascimento: '',
  whatsapp: '',
  email: '',
  senha: '',
  confirmarSenha: '',
}

function dataNoFuturo(valor) {
  if (!dataBrValida(valor)) return false
  const [dia, mes, ano] = valor.split('/').map(Number)
  const data = new Date(ano, mes - 1, dia)
  const hoje = new Date()
  hoje.setHours(23, 59, 59, 999)
  return data > hoje
}

export default function Cadastro() {
  const navigate = useNavigate()
  const { authenticated } = useAuth()
  const [form, setForm] = useState(FORM_INICIAL)
  const [errors, setErrors] = useState({})
  const [feedback, setFeedback] = useState('')
  const [feedbackType, setFeedbackType] = useState('info')
  const [statusCadastro, setStatusCadastro] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let ativo = true

    consultarStatusCadastroAdministrador()
      .then((resposta) => {
        if (ativo) setStatusCadastro(resposta)
      })
      .catch((error) => {
        if (ativo) {
          setFeedbackType('error')
          setFeedback(mensagemErroApi(error))
        }
      })
      .finally(() => {
        if (ativo) setLoading(false)
      })

    return () => {
      ativo = false
    }
  }, [authenticated])

  const atualizarCampo = (campo) => (event) => {
    setForm((atual) => ({ ...atual, [campo]: event.target.value }))
    setErrors((atual) => ({ ...atual, [campo]: '' }))
    setFeedback('')
  }

  const validar = () => {
    const novosErros = {}

    if (!obrigatorio(form.nome) || form.nome.trim().length < 2) {
      novosErros.nome = 'Informe o nome.'
    }

    if (!obrigatorio(form.sobrenome) || form.sobrenome.trim().length < 2) {
      novosErros.sobrenome = 'Informe o sobrenome.'
    }

    if (!cpfValido(form.cpf)) {
      novosErros.cpf = 'Informe um CPF válido.'
    }

    if (!dataBrValida(form.dataNascimento)) {
      novosErros.dataNascimento = 'Informe uma data válida no formato DD/MM/AAAA.'
    } else if (dataNoFuturo(form.dataNascimento)) {
      novosErros.dataNascimento = 'A data de nascimento não pode estar no futuro.'
    }

    const telefone = somenteDigitos(form.whatsapp)
    if (![10, 11].includes(telefone.length)) {
      novosErros.whatsapp = 'Informe um WhatsApp com DDD.'
    }

    if (!emailValido(form.email)) {
      novosErros.email = 'Informe um e-mail válido.'
    }

    if (form.senha.length < 8) {
      novosErros.senha = 'A senha deve ter pelo menos 8 caracteres.'
    }

    if (form.confirmarSenha !== form.senha) {
      novosErros.confirmarSenha = 'As senhas não coincidem.'
    }

    setErrors(novosErros)
    return Object.keys(novosErros).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!validar()) return

    setSubmitting(true)
    setFeedback('')

    try {
      const resposta = await cadastrarAdministrador({
        nome: form.nome.trim(),
        sobrenome: form.sobrenome.trim(),
        cpf: form.cpf,
        data_nascimento: form.dataNascimento,
        whatsapp: form.whatsapp,
        email: form.email.trim(),
        senha: form.senha,
      })

      if (resposta.first_admin && !authenticated) {
        navigate('/login', {
          replace: true,
          state: { message: 'Conta criada com sucesso. Agora faça login para entrar no BiblioAvisa.' },
        })
        return
      }

      setForm(FORM_INICIAL)
      setFeedbackType('success')
      setFeedback('Conta administrativa criada com sucesso.')
    } catch (error) {
      setFeedbackType('error')
      setFeedback(mensagemErroApi(error))
    } finally {
      setSubmitting(false)
    }
  }

  const podeCadastrar = statusCadastro?.can_register

  return (
    <main className="cadastro-page">
      <section className="cadastro-visual" aria-label="Ilustração da biblioteca">
        <div className="cadastro-library-scene">
          <LibraryBig className="cadastro-library-icon" aria-hidden="true" />
          <div className="cadastro-library-books" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <p>
            Crie uma conta de acesso para administrar o acervo e acompanhar os empréstimos.
          </p>
        </div>
      </section>

      <Card className="cadastro-panel" as="section">
        <div className="cadastro-heading">
          <UserPlus aria-hidden="true" />
          <div>
            <h1>CRIE SUA CONTA</h1>
            <p>{authenticated ? 'Cadastre outro administrador do sistema.' : 'Preencha seus dados para criar o primeiro acesso.'}</p>
          </div>
        </div>

        {loading ? (
          <Feedback type="info">Verificando disponibilidade do cadastro...</Feedback>
        ) : !podeCadastrar ? (
          <div className="cadastro-restrito">
            <Feedback type="info">
              Já existe uma conta administrativa. Novos cadastros precisam ser feitos por um administrador autenticado.
            </Feedback>
            <Button variant="dark" type="button" onClick={() => navigate('/login')}>
              Voltar para o login
            </Button>
          </div>
        ) : (
          <form className="cadastro-form" onSubmit={handleSubmit} noValidate>
            <div className="cadastro-grid">
              <TextField
                id="cadastro-nome"
                label="Nome:"
                placeholder="Digite seu nome"
                autoComplete="given-name"
                value={form.nome}
                onChange={atualizarCampo('nome')}
                error={errors.nome}
                tooltip="Informe somente seu primeiro nome ou nome principal."
              />

              <TextField
                id="cadastro-sobrenome"
                label="Sobrenome:"
                placeholder="Digite seu sobrenome"
                autoComplete="family-name"
                value={form.sobrenome}
                onChange={atualizarCampo('sobrenome')}
                error={errors.sobrenome}
              />

              <TextField
                id="cadastro-cpf"
                label="CPF:"
                placeholder="000.000.000-00"
                inputMode="numeric"
                mask="cpf"
                value={form.cpf}
                onChange={atualizarCampo('cpf')}
                error={errors.cpf}
                tooltip="O CPF é validado antes do cadastro e não pode ser repetido."
              />

              <TextField
                id="cadastro-data"
                label="Data de nascimento:"
                placeholder="DD/MM/AAAA"
                inputMode="numeric"
                mask="dataBr"
                value={form.dataNascimento}
                onChange={atualizarCampo('dataNascimento')}
                error={errors.dataNascimento}
              />

              <TextField
                id="cadastro-whatsapp"
                label="WhatsApp:"
                placeholder="(00) 00000-0000"
                inputMode="tel"
                autoComplete="tel"
                mask="telefoneBr"
                value={form.whatsapp}
                onChange={atualizarCampo('whatsapp')}
                error={errors.whatsapp}
                tooltip="Informe DDD e número. O sistema armazena o telefone normalizado."
              />

              <TextField
                id="cadastro-email"
                label="E-mail:"
                type="email"
                placeholder="nome@dominio.com"
                autoComplete="email"
                value={form.email}
                onChange={atualizarCampo('email')}
                error={errors.email}
              />

              <TextField
                id="cadastro-senha"
                label="Senha:"
                type="password"
                placeholder="Mínimo de 8 caracteres"
                autoComplete="new-password"
                value={form.senha}
                onChange={atualizarCampo('senha')}
                error={errors.senha}
                tooltip="A senha é armazenada somente como hash seguro no banco."
              />

              <TextField
                id="cadastro-confirmar-senha"
                label="Confirmar senha:"
                type="password"
                placeholder="Digite a senha novamente"
                autoComplete="new-password"
                value={form.confirmarSenha}
                onChange={atualizarCampo('confirmarSenha')}
                error={errors.confirmarSenha}
              />
            </div>

            {feedback ? <Feedback type={feedbackType}>{feedback}</Feedback> : null}

            <div className="cadastro-actions">
              <button
                type="button"
                className="cadastro-back"
                onClick={() => navigate(authenticated ? '/configuracoes' : '/login')}
              >
                <ArrowLeft aria-hidden="true" />
                {authenticated ? 'Voltar às configurações' : 'Já tenho uma conta'}
              </button>

              <Button className="cadastro-submit" variant="dark" type="submit" disabled={submitting}>
                {submitting ? 'Cadastrando...' : 'Cadastrar'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </main>
  )
}
