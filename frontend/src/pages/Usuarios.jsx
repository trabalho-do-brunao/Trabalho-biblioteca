import { useEffect, useState } from 'react'
import { Pencil, Plus, Search, UserCheck, UserX } from 'lucide-react'

import UsuarioFormModal from '../components/usuarios/UsuarioFormModal'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import {
  alterarStatusUsuario,
  atualizarUsuario,
  cadastrarUsuario,
  listarUsuarios,
} from '../services/usuarios'
import { formatarTelefoneArmazenado } from '../utils/masks'
import './usuarios.css'

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([])
  const [busca, setBusca] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [usuarioEditando, setUsuarioEditando] = useState(null)
  const [salvando, setSalvando] = useState(false)
  const [alterandoStatus, setAlterandoStatus] = useState(null)

  const carregar = async (termo = '') => {
    setCarregando(true)
    try {
      const resposta = await listarUsuarios({ busca: termo, incluirInativos: true })
      setUsuarios(resposta.usuarios || [])
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => carregar(busca), 300)
    return () => window.clearTimeout(timer)
  }, [busca])

  const abrirCadastro = () => {
    setUsuarioEditando(null)
    setModalAberto(true)
    setFeedback(null)
  }

  const abrirEdicao = (usuario) => {
    setUsuarioEditando(usuario)
    setModalAberto(true)
    setFeedback(null)
  }

  const salvar = async (dados) => {
    setSalvando(true)
    try {
      const resposta = usuarioEditando
        ? await atualizarUsuario(usuarioEditando.id, dados)
        : await cadastrarUsuario(dados)

      setFeedback({ type: 'success', message: resposta.mensagem })
      setModalAberto(false)
      setUsuarioEditando(null)
      await carregar(busca)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setSalvando(false)
    }
  }

  const mudarStatus = async (usuario) => {
    const proximoAtivo = !usuario.ativo
    const acao = proximoAtivo ? 'ativar' : 'inativar'
    const confirmar = window.confirm(`Deseja realmente ${acao} ${usuario.nome}?`)
    if (!confirmar) return

    setAlterandoStatus(usuario.id)
    setFeedback(null)
    try {
      const resposta = await alterarStatusUsuario(usuario.id, proximoAtivo)
      setFeedback({ type: 'success', message: resposta.mensagem })
      await carregar(busca)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setAlterandoStatus(null)
    }
  }

  const columns = [
    { key: 'nome', label: 'Nome' },
    {
      key: 'telefone',
      label: 'WhatsApp',
      render: (usuario) => formatarTelefoneArmazenado(usuario.telefone),
    },
    {
      key: 'email',
      label: 'E-mail',
      render: (usuario) => usuario.email || '—',
    },
    {
      key: 'ativo',
      label: 'Situação',
      render: (usuario) => (
        <span className={`usuarios-status ${usuario.ativo ? 'ativo' : 'inativo'}`}>
          {usuario.ativo ? 'Ativo' : 'Inativo'}
        </span>
      ),
    },
    {
      key: 'acoes',
      label: 'Ações',
      render: (usuario) => (
        <div className="usuarios-actions">
          <button
            type="button"
            className="usuarios-action-button"
            onClick={() => abrirEdicao(usuario)}
            title={`Editar ${usuario.nome}`}
            aria-label={`Editar ${usuario.nome}`}
          >
            <Pencil aria-hidden="true" />
          </button>
          <button
            type="button"
            className={`usuarios-action-button ${usuario.ativo ? 'danger' : 'success'}`}
            onClick={() => mudarStatus(usuario)}
            disabled={alterandoStatus === usuario.id}
            title={usuario.ativo ? `Inativar ${usuario.nome}` : `Ativar ${usuario.nome}`}
            aria-label={usuario.ativo ? `Inativar ${usuario.nome}` : `Ativar ${usuario.nome}`}
          >
            {usuario.ativo ? <UserX aria-hidden="true" /> : <UserCheck aria-hidden="true" />}
          </button>
        </div>
      ),
    },
  ]

  return (
    <section className="page usuarios-page">
      <header className="page-header usuarios-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Usuários</h1>
          <p>Cadastre e gerencie os leitores usados nos empréstimos e notificações.</p>
        </div>
        <Button type="button" onClick={abrirCadastro}>
          <Plus aria-hidden="true" />
          Adicionar Usuário
        </Button>
      </header>

      <div className="usuarios-toolbar">
        <label className="usuarios-search">
          <span className="sr-only">Pesquisar usuários</span>
          <Search aria-hidden="true" />
          <input
            type="search"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Pesquisar por nome, e-mail, telefone ou ID..."
            aria-label="Pesquisar usuários"
          />
        </label>
        <span className="usuarios-count">
          {carregando ? 'Carregando...' : `${usuarios.length} usuário(s)`}
        </span>
      </div>

      {feedback ? (
        <Feedback type={feedback.type} className="usuarios-feedback">{feedback.message}</Feedback>
      ) : null}

      <DataTable
        columns={columns}
        rows={usuarios}
        emptyMessage={carregando ? 'Carregando usuários...' : 'Nenhum usuário encontrado.'}
      />

      {modalAberto ? (
        <UsuarioFormModal
          usuario={usuarioEditando}
          onClose={() => {
            if (!salvando) {
              setModalAberto(false)
              setUsuarioEditando(null)
            }
          }}
          onSave={salvar}
          saving={salvando}
        />
      ) : null}
    </section>
  )
}
