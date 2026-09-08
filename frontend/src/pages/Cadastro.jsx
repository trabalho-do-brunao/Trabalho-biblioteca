import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import bookOpen from '../assets/auth/book-open.png'
import { useAuth } from '../auth/AuthContext'
import Button from '../components/ui/Button'
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

    if (!obrigatorio(form.nome) || form.nome.trim().length < 2) novosErros.nome = 'Informe o nome.'
    if (!obrigatorio(form.sobrenome) || form.sobrenome.trim().length < 2) novosErros.sobrenome = 'Informe o sobrenome.'
    if (!cpfValido(form.cpf)) novosErros.cpf = 'Informe um CPF válido.'

    if (!dataBrValida(form.dataNascimento)) {
      novosErros.dataNascimento = 'Informe uma data válida no formato DD/MM/AAAA.'
    } else if (dataNoFuturo(form.dataNascimento)) {
      novosErros.dataNascimento = 'A data de nascimento não pode estar no futuro.'
    }

    const telefone = somenteDigitos(form.whatsapp)
    if (![10, 11].includes(telefone.length)) novosErros.whatsapp = 'Informe um WhatsApp com DDD.'
    if (!emailValido(form.email)) novosErros.email = 'Informe um e-mail válido.'
    if (form.senha.length < 8) novosErros.senha = 'A senha deve ter pelo menos 8 caracteres.'
    if (form.confirmarSenha !== form.senha) novosErros.confirmarSenha = 'As senhas não coincidem.'

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
      <section className="cadastro-shell" aria-labelledby="cadastro-title">
        <h1 id="cadastro-title" className="cadastro-title">REALIZE SEU CADASTRO</h1>

        <div className="cadastro-book-wrap">
          <img className="cadastro-book-image" src={bookOpen} alt="Livro aberto" />

          <div className="cadastro-overlay">
            {loading ? (
              <div className="cadastro-state">
                <Feedback type="info">Verificando disponibilidade do cadastro...</Feedback>
              </div>
            ) : !podeCadastrar ? (
              <div className="cadastro-state">
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
                  <TextField id="cadastro-nome" label="Nome:" placeholder="Digite seu nome" autoComplete="given-name" value={form.nome} onChange={atualizarCampo('nome')} error={errors.nome} tooltip="Informe somente seu primeiro nome ou nome principal." />
                  <TextField id="cadastro-sobrenome" label="Sobrenome:" placeholder="Digite seu sobrenome" autoComplete="family-name" value={form.sobrenome} onChange={atualizarCampo('sobrenome')} error={errors.sobrenome} />
                  <TextField id="cadastro-cpf" label="CPF:" placeholder="Digite seu CPF" inputMode="numeric" mask="cpf" value={form.cpf} onChange={atualizarCampo('cpf')} error={errors.cpf} tooltip="O CPF é validado antes do cadastro e não pode ser repetido." />
                  <TextField id="cadastro-whatsapp" label="WhatsApp:" placeholder="Digite seu WhatsApp" inputMode="tel" autoComplete="tel" mask="telefoneBr" value={form.whatsapp} onChange={atualizarCampo('whatsapp')} error={errors.whatsapp} tooltip="Informe DDD e número. O sistema armazena o telefone normalizado." />
                  <TextField id="cadastro-data" label="Data de nascimento:" placeholder="Digite sua data de nascimento" inputMode="numeric" mask="dataBr" value={form.dataNascimento} onChange={atualizarCampo('dataNascimento')} error={errors.dataNascimento} />
                  <TextField id="cadastro-email" label="E-mail:" type="email" placeholder="Digite seu e-mail" autoComplete="email" value={form.email} onChange={atualizarCampo('email')} error={errors.email} />
                  <TextField id="cadastro-senha" label="Crie uma senha:" type="password" placeholder="Digite uma senha" autoComplete="new-password" value={form.senha} onChange={atualizarCampo('senha')} error={errors.senha} tooltip="A senha é armazenada somente como hash seguro no banco." />
                  <TextField id="cadastro-confirmar-senha" label="Confirme sua senha:" type="password" placeholder="Digite novamente sua senha" autoComplete="new-password" value={form.confirmarSenha} onChange={atualizarCampo('confirmarSenha')} error={errors.confirmarSenha} />
                </div>

                {feedback ? <Feedback className="cadastro-feedback" type={feedbackType}>{feedback}</Feedback> : null}

                <div className="cadastro-actions">
                  <Button className="cadastro-submit" variant="dark" type="submit" disabled={submitting}>
                    {submitting ? 'Criando...' : 'Criar conta'}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}
