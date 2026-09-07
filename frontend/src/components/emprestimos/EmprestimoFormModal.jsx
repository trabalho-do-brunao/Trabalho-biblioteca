import { useEffect, useMemo, useState } from 'react'
import { X } from 'lucide-react'

import Button from '../ui/Button'
import Feedback from '../ui/Feedback'
import Tooltip from '../ui/Tooltip'

function dataLocalISO(data = new Date()) {
  const ajustada = new Date(data.getTime() - data.getTimezoneOffset() * 60_000)
  return ajustada.toISOString().slice(0, 10)
}

function prazoPadrao() {
  const data = new Date()
  data.setDate(data.getDate() + 7)
  return dataLocalISO(data)
}

export default function EmprestimoFormModal({ usuarios, livros, onClose, onSave, saving = false }) {
  const hoje = useMemo(() => dataLocalISO(), [])
  const [campos, setCampos] = useState({
    usuario_id: '',
    livro_id: '',
    data_prevista_devolucao: prazoPadrao(),
  })
  const [erros, setErros] = useState({})

  useEffect(() => {
    setErros({})
  }, [usuarios, livros])

  const alterar = (campo) => (event) => {
    setCampos((atual) => ({ ...atual, [campo]: event.target.value }))
    setErros((atual) => ({ ...atual, [campo]: '' }))
  }

  const enviar = async (event) => {
    event.preventDefault()
    const novosErros = {}

    if (!campos.usuario_id) novosErros.usuario_id = 'Selecione um usuário ativo.'
    if (!campos.livro_id) novosErros.livro_id = 'Selecione um livro com exemplar disponível.'
    if (!campos.data_prevista_devolucao) {
      novosErros.data_prevista_devolucao = 'Informe o prazo de devolução.'
    } else if (campos.data_prevista_devolucao < hoje) {
      novosErros.data_prevista_devolucao = 'O prazo não pode ser anterior à data do empréstimo.'
    }

    if (Object.keys(novosErros).length) {
      setErros(novosErros)
      return
    }

    await onSave({
      usuario_id: Number(campos.usuario_id),
      livro_id: Number(campos.livro_id),
      data_prevista_devolucao: campos.data_prevista_devolucao,
    })
  }

  return (
    <div className="emprestimos-modal-backdrop" role="presentation">
      <section className="emprestimos-modal" role="dialog" aria-modal="true" aria-labelledby="emprestimo-form-title">
        <header className="emprestimos-modal-header">
          <div>
            <p className="page-eyebrow">Circulação do acervo</p>
            <h2 id="emprestimo-form-title">Novo empréstimo</h2>
            <p>O estoque será alterado somente depois da confirmação do backend.</p>
          </div>
          <button type="button" className="emprestimos-modal-close" onClick={onClose} aria-label="Fechar formulário" title="Fechar">
            <X aria-hidden="true" />
          </button>
        </header>

        <form className="emprestimos-form" onSubmit={enviar} noValidate>
          <div className="emprestimos-field">
            <div className="emprestimos-label-row">
              <label htmlFor="emprestimo-usuario">Usuário</label>
              <Tooltip content="Somente usuários ativos podem realizar novos empréstimos." label="Ajuda sobre usuário" />
            </div>
            <select
              id="emprestimo-usuario"
              value={campos.usuario_id}
              onChange={alterar('usuario_id')}
              aria-invalid={Boolean(erros.usuario_id)}
            >
              <option value="">Selecione o leitor</option>
              {usuarios.map((usuario) => (
                <option key={usuario.id} value={usuario.id}>{usuario.nome}</option>
              ))}
            </select>
            {erros.usuario_id ? <small className="ui-field-error" role="alert">{erros.usuario_id}</small> : null}
          </div>

          <div className="emprestimos-field">
            <div className="emprestimos-label-row">
              <label htmlFor="emprestimo-livro">Livro</label>
              <Tooltip content="A lista mostra apenas livros que possuem ao menos um exemplar disponível. O backend verifica novamente antes de salvar." label="Ajuda sobre livro" />
            </div>
            <select
              id="emprestimo-livro"
              value={campos.livro_id}
              onChange={alterar('livro_id')}
              aria-invalid={Boolean(erros.livro_id)}
            >
              <option value="">Selecione o livro</option>
              {livros.map((livro) => (
                <option key={livro.id} value={livro.id}>
                  {livro.titulo} — {livro.quantidade_disponivel} disponível(is)
                </option>
              ))}
            </select>
            {erros.livro_id ? <small className="ui-field-error" role="alert">{erros.livro_id}</small> : null}
          </div>

          <div className="emprestimos-date-grid">
            <div className="emprestimos-field">
              <label htmlFor="emprestimo-data">Data do empréstimo</label>
              <input id="emprestimo-data" type="date" value={hoje} readOnly />
              <small className="ui-field-hint">Registrada automaticamente como hoje.</small>
            </div>

            <div className="emprestimos-field">
              <div className="emprestimos-label-row">
                <label htmlFor="emprestimo-prazo">Prazo de devolução</label>
                <Tooltip content="Escolha a data prevista para a devolução. O backend impede datas anteriores ao empréstimo." label="Ajuda sobre prazo" />
              </div>
              <input
                id="emprestimo-prazo"
                type="date"
                min={hoje}
                value={campos.data_prevista_devolucao}
                onChange={alterar('data_prevista_devolucao')}
                aria-invalid={Boolean(erros.data_prevista_devolucao)}
              />
              {erros.data_prevista_devolucao ? <small className="ui-field-error" role="alert">{erros.data_prevista_devolucao}</small> : null}
            </div>
          </div>

          {!usuarios.length ? <Feedback type="warning">Não há usuários ativos disponíveis para empréstimo.</Feedback> : null}
          {!livros.length ? <Feedback type="warning">Não há livros com exemplares disponíveis.</Feedback> : null}

          <div className="emprestimos-form-actions">
            <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>Cancelar</Button>
            <Button type="submit" disabled={saving || !usuarios.length || !livros.length}>
              {saving ? 'Registrando...' : 'Confirmar empréstimo'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  )
}
