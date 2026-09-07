import { useState } from 'react'
import { BookOpen, Search, X } from 'lucide-react'

import Button from '../ui/Button'
import Feedback from '../ui/Feedback'
import TextField from '../ui/TextField'
import { mensagemErroApi } from '../../services/api'
import { cadastrarLivro, consultarLivroPorIsbn } from '../../services/livros'

function normalizarIsbn(valor) {
  return String(valor || '').replace(/[^0-9Xx]/g, '').toUpperCase()
}

function isbnFormatoValido(valor) {
  const isbn = normalizarIsbn(valor)
  if (![10, 13].includes(isbn.length)) return false
  if (isbn.length === 13 && /X/.test(isbn)) return false
  return !/X/.test(isbn.slice(0, -1))
}

export default function LivroCadastroModal({ onClose, onCreated }) {
  const [isbn, setIsbn] = useState('')
  const [resultado, setResultado] = useState(null)
  const [quantidade, setQuantidade] = useState('1')
  const [erroIsbn, setErroIsbn] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [consultando, setConsultando] = useState(false)
  const [salvando, setSalvando] = useState(false)

  const consultar = async (event) => {
    event?.preventDefault()
    setFeedback(null)
    setResultado(null)

    if (!isbnFormatoValido(isbn)) {
      setErroIsbn('Informe um ISBN-10 ou ISBN-13 válido.')
      return
    }

    setErroIsbn('')
    setConsultando(true)
    try {
      const resposta = await consultarLivroPorIsbn(normalizarIsbn(isbn))
      setResultado(resposta)
      if (resposta.ja_cadastrado) {
        setFeedback({
          type: 'warning',
          message: 'Este ISBN já está cadastrado no acervo. A quantidade atual é mostrada abaixo.',
        })
      }
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setConsultando(false)
    }
  }

  const confirmarCadastro = async () => {
    if (!resultado?.livro || resultado.ja_cadastrado) return

    const quantidadeNumero = Number.parseInt(quantidade, 10)
    if (!Number.isInteger(quantidadeNumero) || quantidadeNumero <= 0 || quantidadeNumero > 9999) {
      setFeedback({ type: 'error', message: 'Informe uma quantidade de exemplares entre 1 e 9999.' })
      return
    }

    setSalvando(true)
    setFeedback(null)
    try {
      const resposta = await cadastrarLivro({
        ...resultado.livro,
        quantidade_total: quantidadeNumero,
      })
      onCreated?.(resposta)
    } catch (erro) {
      setFeedback({ type: 'error', message: mensagemErroApi(erro) })
    } finally {
      setSalvando(false)
    }
  }

  const livro = resultado?.livro

  return (
    <div className="livros-modal-backdrop" role="presentation">
      <section className="livros-modal" role="dialog" aria-modal="true" aria-labelledby="livro-form-title">
        <header className="livros-modal-header">
          <div>
            <p className="page-eyebrow">Cadastro pelo Google Books</p>
            <h2 id="livro-form-title">Adicionar livro por ISBN</h2>
          </div>
          <button type="button" className="livros-modal-close" onClick={onClose} aria-label="Fechar formulário" title="Fechar">
            <X aria-hidden="true" />
          </button>
        </header>

        <form className="livros-isbn-form" onSubmit={consultar} noValidate>
          <TextField
            id="livro-isbn"
            label="ISBN"
            value={isbn}
            onChange={(event) => {
              setIsbn(event.target.value)
              setErroIsbn('')
              setResultado(null)
              setFeedback(null)
            }}
            error={erroIsbn}
            tooltip="Use o ISBN-10 ou ISBN-13 impresso no livro. A busca consulta primeiro o acervo e depois a Google Books."
            hint="Pode digitar com ou sem hífens."
            placeholder="Ex.: 9788535902778"
            inputMode="text"
            autoFocus
          />
          <Button type="submit" disabled={consultando}>
            <Search aria-hidden="true" />
            {consultando ? 'Consultando...' : 'Buscar ISBN'}
          </Button>
        </form>

        {feedback ? <Feedback type={feedback.type} className="livros-modal-feedback">{feedback.message}</Feedback> : null}

        {livro ? (
          <div className="livros-preview">
            <div className="livros-preview-cover" aria-hidden={!livro.url_capa}>
              {livro.url_capa ? <img src={livro.url_capa} alt={`Capa de ${livro.titulo}`} /> : <BookOpen aria-hidden="true" />}
            </div>
            <div className="livros-preview-info">
              <span className="livros-preview-source">
                {resultado.ja_cadastrado ? 'Já cadastrado no acervo' : 'Encontrado na Google Books'}
              </span>
              <h3>{livro.titulo}</h3>
              {livro.subtitulo ? <p className="livros-preview-subtitle">{livro.subtitulo}</p> : null}
              <dl>
                <div><dt>Autor</dt><dd>{livro.autor || 'Não informado'}</dd></div>
                <div><dt>ISBN</dt><dd>{livro.isbn}</dd></div>
                <div><dt>Editora</dt><dd>{livro.editora || 'Não informada'}</dd></div>
                <div><dt>Publicação</dt><dd>{livro.data_publicacao || 'Não informada'}</dd></div>
                {livro.numero_paginas ? <div><dt>Páginas</dt><dd>{livro.numero_paginas}</dd></div> : null}
                {resultado.ja_cadastrado ? (
                  <div><dt>Disponibilidade</dt><dd>{livro.quantidade_disponivel} de {livro.quantidade_total}</dd></div>
                ) : null}
              </dl>
            </div>
          </div>
        ) : null}

        {livro && !resultado.ja_cadastrado ? (
          <div className="livros-confirmacao">
            <TextField
              id="livro-quantidade"
              label="Quantidade de exemplares"
              type="number"
              min="1"
              max="9999"
              value={quantidade}
              onChange={(event) => setQuantidade(event.target.value)}
              tooltip="Todos os exemplares serão cadastrados inicialmente como disponíveis."
            />
            <div className="livros-form-actions">
              <Button type="button" variant="ghost" onClick={onClose} disabled={salvando}>Cancelar</Button>
              <Button type="button" onClick={confirmarCadastro} disabled={salvando}>
                {salvando ? 'Cadastrando...' : 'Confirmar cadastro'}
              </Button>
            </div>
          </div>
        ) : (
          <div className="livros-form-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Fechar</Button>
          </div>
        )}
      </section>
    </div>
  )
}
