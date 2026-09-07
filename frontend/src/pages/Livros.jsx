import { useEffect, useState } from 'react'
import { BookOpen, Plus, Search } from 'lucide-react'

import LivroCadastroModal from '../components/livros/LivroCadastroModal'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Feedback from '../components/ui/Feedback'
import { mensagemErroApi } from '../services/api'
import { listarLivros } from '../services/livros'
import './livros.css'

export default function Livros() {
  const [livros, setLivros] = useState([])
  const [busca, setBusca] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [feedback, setFeedback] = useState(null)
  const [modalAberto, setModalAberto] = useState(false)

  const carregar = async (termo = '') => {
    setCarregando(true)
    try {
      const resposta = await listarLivros({ busca: termo })
      setLivros(resposta.livros || [])
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

  const cadastroConcluido = async (resposta) => {
    setModalAberto(false)
    setFeedback({ type: 'success', message: resposta.mensagem || 'Livro cadastrado com sucesso.' })
    await carregar(busca)
  }

  const columns = [
    {
      key: 'capa',
      label: 'Capa',
      render: (livro) => (
        <div className="livros-table-cover">
          {livro.url_capa ? <img src={livro.url_capa} alt="" /> : <BookOpen aria-hidden="true" />}
        </div>
      ),
    },
    {
      key: 'titulo',
      label: 'Livro',
      render: (livro) => (
        <div className="livros-title-cell">
          <strong>{livro.titulo}</strong>
          {livro.autor ? <span>{livro.autor}</span> : null}
        </div>
      ),
    },
    {
      key: 'isbn',
      label: 'ISBN',
      render: (livro) => livro.isbn || '—',
    },
    {
      key: 'quantidade_total',
      label: 'Exemplares',
      render: (livro) => livro.quantidade_total,
    },
    {
      key: 'quantidade_disponivel',
      label: 'Disponíveis',
      render: (livro) => (
        <span className={`livros-disponibilidade ${livro.quantidade_disponivel > 0 ? 'disponivel' : 'indisponivel'}`}>
          {livro.quantidade_disponivel}
        </span>
      ),
    },
    {
      key: 'situacao',
      label: 'Situação',
      render: (livro) => livro.quantidade_disponivel > 0 ? 'Disponível' : 'Sem exemplar disponível',
    },
  ]

  return (
    <section className="page livros-page">
      <header className="page-header livros-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>Livros</h1>
          <p>Consulte o acervo e cadastre novos títulos a partir do ISBN.</p>
        </div>
        <Button type="button" onClick={() => {
          setModalAberto(true)
          setFeedback(null)
        }}>
          <Plus aria-hidden="true" />
          Adicionar por ISBN
        </Button>
      </header>

      <div className="livros-toolbar">
        <label className="livros-search">
          <span className="sr-only">Pesquisar livros</span>
          <Search aria-hidden="true" />
          <input
            type="search"
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Pesquisar por título, autor, ISBN, editora ou ID..."
            aria-label="Pesquisar livros"
          />
        </label>
        <span className="livros-count">
          {carregando ? 'Carregando...' : `${livros.length} livro(s)`}
        </span>
      </div>

      {feedback ? (
        <Feedback type={feedback.type} className="livros-feedback">{feedback.message}</Feedback>
      ) : null}

      <DataTable
        columns={columns}
        rows={livros}
        emptyMessage={carregando ? 'Carregando acervo...' : 'Nenhum livro encontrado.'}
      />

      {modalAberto ? (
        <LivroCadastroModal
          onClose={() => setModalAberto(false)}
          onCreated={cadastroConcluido}
        />
      ) : null}
    </section>
  )
}
