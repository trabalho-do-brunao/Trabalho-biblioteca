import { requisicao } from './api'

export function listarUsuarios({ busca = '', incluirInativos = true } = {}) {
  const params = new URLSearchParams()
  if (busca.trim()) params.set('busca', busca.trim())
  params.set('incluir_inativos', String(incluirInativos))
  return requisicao(`/api/usuarios?${params.toString()}`)
}

export function cadastrarUsuario(dados) {
  return requisicao('/api/usuarios', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function atualizarUsuario(usuarioId, dados) {
  return requisicao(`/api/usuarios/${usuarioId}`, {
    method: 'PATCH',
    body: JSON.stringify(dados),
  })
}

export function alterarStatusUsuario(usuarioId, ativo) {
  return requisicao(`/api/usuarios/${usuarioId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ ativo }),
  })
}
