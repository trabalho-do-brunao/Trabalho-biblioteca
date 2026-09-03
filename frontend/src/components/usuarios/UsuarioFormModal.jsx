import { useEffect, useState } from 'react'
import { X } from 'lucide-react'

import Button from '../ui/Button'
import Feedback from '../ui/Feedback'
import TextField from '../ui/TextField'
import { emailValido, obrigatorio } from '../../utils/validation'
import { somenteDigitos } from '../../utils/masks'

const vazio = { nome: '', telefone: '', email: '' }

function validarTelefone(valor) {
  const texto = String(valor || '').trim()
  const digitos = somenteDigitos(texto)
  const internacional = texto.startsWith('+') || texto.startsWith('00')
  return internacional ? digitos.length >= 8 && digitos.length <= 15 : [10, 11].includes(digitos.length)
}

export default function UsuarioFormModal({ usuario, onClose, onSave, saving = false }) {
  const [campos, setCampos] = useState(vazio)
  const [erros, setErros] = useState({})

  useEffect(() => {
    setCampos(usuario ? {
      nome: usuario.nome || '',
      telefone: usuario.telefone ? `+${usuario.telefone}` : '',
      email: usuario.email || '',
    } : vazio)
    setErros({})
  }, [usuario])

  const alterar = (campo) => (event) => {
    setCampos((atual) => ({ ...atual, [campo]: event.target.value }))
    setErros((atual) => ({ ...atual, [campo]: '' }))
  }

  const enviar = async (event) => {
    event.preventDefault()
    const novosErros = {}

    if (!obrigatorio(campos.nome) || campos.nome.trim().length < 2) {
      novosErros.nome = 'Informe um nome com pelo menos 2 caracteres.'
    }

    if (!validarTelefone(campos.telefone)) {
      novosErros.telefone = 'Informe DDD + número ou um telefone internacional iniciado por + ou 00.'
    }

    if (campos.email.trim() && !emailValido(campos.email)) {
      novosErros.email = 'Informe um e-mail válido.'
    }

    if (Object.keys(novosErros).length) {
      setErros(novosErros)
      return
    }

    await onSave({
      nome: campos.nome.trim(),
      telefone: campos.telefone.trim(),
      email: campos.email.trim() || null,
    })
  }

  return (
    <div className="usuarios-modal-backdrop" role="presentation">
      <section className="usuarios-modal" role="dialog" aria-modal="true" aria-labelledby="usuario-form-title">
        <header className="usuarios-modal-header">
          <div>
            <p className="page-eyebrow">Gestão de usuários</p>
            <h2 id="usuario-form-title">{usuario ? 'Editar usuário' : 'Adicionar usuário'}</h2>
          </div>
          <button type="button" className="usuarios-modal-close" onClick={onClose} aria-label="Fechar formulário" title="Fechar">
            <X aria-hidden="true" />
          </button>
        </header>

        <form className="usuarios-form" onSubmit={enviar} noValidate>
          <TextField
            id="usuario-nome"
            label="Nome"
            value={campos.nome}
            onChange={alterar('nome')}
            error={erros.nome}
            tooltip="Nome do leitor que será usado nos empréstimos e mensagens do BiblioAvisa."
            placeholder="Digite o nome completo"
            autoComplete="name"
          />

          <TextField
            id="usuario-telefone"
            label="WhatsApp / Telefone"
            value={campos.telefone}
            onChange={alterar('telefone')}
            error={erros.telefone}
            mask="telefoneFlexivel"
            tooltip="Para o Brasil, informe DDD + número. Para outro país, comece com + e o código internacional."
            hint="Ex.: (41) 99999-9999 ou +14155552671"
            placeholder="DDD + número ou +código do país"
            inputMode="tel"
            autoComplete="tel"
          />

          <TextField
            id="usuario-email"
            label="E-mail (opcional)"
            type="email"
            value={campos.email}
            onChange={alterar('email')}
            error={erros.email}
            tooltip="O e-mail é opcional e poderá ser usado por relatórios ou contatos futuros."
            placeholder="nome@dominio.com"
            autoComplete="email"
          />

          {usuario && !usuario.ativo ? (
            <Feedback type="warning">Este usuário está inativo. Editar os dados não altera sua situação.</Feedback>
          ) : null}

          <div className="usuarios-form-actions">
            <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Salvando...' : usuario ? 'Salvar alterações' : 'Cadastrar usuário'}</Button>
          </div>
        </form>
      </section>
    </div>
  )
}
