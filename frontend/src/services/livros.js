import { requisicao } from './api'

export function listarLivros({ busca = '' } = {}) {
  const params = new URLSearchParams()
  if (busca.trim()) params.set('busca', busca.trim())
  const query = params.toString()
  return requisicao(`/api/livros${query ? `?${query}` : ''}`)
}

export function consultarLivroPorIsbn(isbn) {
  return requisicao(`/api/livros/consulta-isbn/${encodeURIComponent(isbn.trim())}`)
}

export function cadastrarLivro(dados) {
  return requisicao('/api/livros', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
