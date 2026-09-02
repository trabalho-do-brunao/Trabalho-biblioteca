import { useState } from 'react'
import { ArrowRight, Database, ServerCog, SquareCode } from 'lucide-react'

import { demonstrarIntegracao, mensagemErroApi } from '../../services/api'
import { somenteDigitos } from '../../utils/masks'
import { cpfValido, dataBrValida, emailValido, obrigatorio } from '../../utils/validation'
import Button from '../ui/Button'
import Feedback from '../ui/Feedback'
import TextField from '../ui/TextField'
import './integration-demo.css'

const estadoInicial = {
  nome: '',
  email: '',
  cpf: '',
  telefone: '',
  data: '',
}

function validarFormulario(campos) {
  const erros = {}

  if (!obrigatorio(campos.nome) || campos.nome.trim().length < 2) {
    erros.nome = 'Informe um nome com pelo menos 2 caracteres.'
  }

  if (!emailValido(campos.email)) {
    erros.email = 'Informe um e-mail válido, por exemplo nome@dominio.com.'
  }

  if (!cpfValido(campos.cpf)) {
    erros.cpf = 'Informe um CPF válido.'
  }

  const telefone = somenteDigitos(campos.telefone)
  if (telefone.length < 10 || telefone.length > 11) {
    erros.telefone = 'Informe DDD e telefone com 10 ou 11 dígitos.'
  }

  if (!dataBrValida(campos.data)) {
    erros.data = 'Informe uma data válida no formato DD/MM/AAAA.'
  }

  return erros
}

export default function IntegrationDemo() {
  const [campos, setCampos] = useState(estadoInicial)
  const [erros, setErros] = useState({})
  const [estado, setEstado] = useState('idle')
  const [mensagem, setMensagem] = useState('')
  const [resultado, setResultado] = useState(null)

  const alterar = (campo) => (event) => {
    setCampos((atual) => ({ ...atual, [campo]: event.target.value }))
    setErros((atual) => ({ ...atual, [campo]: '' }))
  }

  const enviar = async (event) => {
    event.preventDefault()
    const novosErros = validarFormulario(campos)

    if (Object.keys(novosErros).length) {
      setErros(novosErros)
      setResultado(null)
      setEstado('error')
      setMensagem('Existem dados inválidos. Corrija os campos destacados antes de enviar ao backend.')
      return
    }

    setEstado('loading')
    setMensagem('Enviando dados do React para o Python e consultando o PostgreSQL...')
    setResultado(null)

    try {
      const resposta = await demonstrarIntegracao(campos)
      setResultado(resposta)
      setEstado('success')
      setMensagem(resposta.mensagem)
    } catch (erro) {
      setEstado('error')
      setMensagem(mensagemErroApi(erro))
    }
  }

  return (
    <section className="integration-demo" aria-labelledby="integration-demo-title">
      <header className="integration-demo-header">
        <div>
          <p className="page-eyebrow">Demonstração técnica</p>
          <h2 id="integration-demo-title">Interface → Python → PostgreSQL → Interface</h2>
          <p>
            Use este formulário para demonstrar máscaras, validações, tooltips, tratamento de erros
            e o processamento completo entre frontend, backend e banco de dados.
          </p>
        </div>
      </header>

      <div className="integration-flow" aria-label="Fluxo da integração">
        <span><SquareCode aria-hidden="true" /> React</span>
        <ArrowRight aria-hidden="true" />
        <span><ServerCog aria-hidden="true" /> Python</span>
        <ArrowRight aria-hidden="true" />
        <span><Database aria-hidden="true" /> PostgreSQL</span>
        <ArrowRight aria-hidden="true" />
        <span><SquareCode aria-hidden="true" /> Resultado</span>
      </div>

      <form className="integration-demo-form" onSubmit={enviar} noValidate>
        <TextField
          id="demo-nome"
          label="Nome"
          value={campos.nome}
          onChange={alterar('nome')}
          error={erros.nome}
          tooltip="O React verifica se o campo foi preenchido antes de enviar os dados ao Python."
          placeholder="Digite um nome"
          autoComplete="off"
        />

        <TextField
          id="demo-email"
          label="E-mail"
          type="email"
          value={campos.email}
          onChange={alterar('email')}
          error={erros.email}
          tooltip="O formato do e-mail é validado no frontend e validado novamente no backend."
          placeholder="nome@dominio.com"
          autoComplete="off"
        />

        <TextField
          id="demo-cpf"
          label="CPF"
          value={campos.cpf}
          onChange={alterar('cpf')}
          error={erros.cpf}
          mask="cpf"
          inputMode="numeric"
          tooltip="A máscara é aplicada enquanto você digita. O dígito verificador também é validado."
          placeholder="000.000.000-00"
          autoComplete="off"
        />

        <TextField
          id="demo-telefone"
          label="Telefone"
          value={campos.telefone}
          onChange={alterar('telefone')}
          error={erros.telefone}
          mask="telefoneBr"
          inputMode="tel"
          tooltip="Este exemplo usa máscara brasileira; a lógica foi isolada para permitir formato internacional depois."
          placeholder="(00) 00000-0000"
          autoComplete="off"
        />

        <TextField
          id="demo-data"
          label="Data"
          value={campos.data}
          onChange={alterar('data')}
          error={erros.data}
          mask="dataBr"
          inputMode="numeric"
          tooltip="A máscara monta DD/MM/AAAA e a validação rejeita datas inexistentes."
          placeholder="DD/MM/AAAA"
          autoComplete="off"
        />

        <div className="integration-demo-submit">
          <Button type="submit" disabled={estado === 'loading'}>
            {estado === 'loading' ? 'Processando...' : 'Processar integração'}
          </Button>
        </div>
      </form>

      {mensagem ? <Feedback type={estado === 'idle' ? 'info' : estado}>{mensagem}</Feedback> : null}

      {resultado ? (
        <div className="integration-result" aria-live="polite">
          <div className="integration-result-card">
            <strong>Processamento no Python</strong>
            <span>Nome: {resultado.processamento.nome_normalizado}</span>
            <span>E-mail normalizado: {resultado.processamento.email_normalizado}</span>
            <span>Data convertida: {resultado.processamento.data_iso}</span>
          </div>

          <div className="integration-result-card">
            <strong>PostgreSQL conectado</strong>
            {Object.entries(resultado.banco.registros).map(([chave, valor]) => (
              <span key={chave}>{chave}: {valor}</span>
            ))}
          </div>

          <div className="integration-result-card integration-result-success">
            <strong>Resultado devolvido à interface</strong>
            <span>{resultado.fluxo.join(' → ')}</span>
            <span>Fluxo concluído sem recarregar a página.</span>
          </div>
        </div>
      ) : null}
    </section>
  )
}
