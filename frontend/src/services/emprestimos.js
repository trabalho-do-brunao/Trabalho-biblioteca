import { requisicao } from './api'

export function listarEmprestimosAtivos({ usuarioId } = {}) {
  const params = new URLSearchParams()
  if (usuarioId) params.set('usuario_id', String(usuarioId))
  const query = params.toString()
  return requisicao(`/api/emprestimos/ativos${query ? `?${query}` : ''}`)
}

export function listarHistoricoEmprestimos({ usuarioId } = {}) {
  const params = new URLSearchParams()
  if (usuarioId) params.set('usuario_id', String(usuarioId))
  const query = params.toString()
  return requisicao(`/api/emprestimos/historico${query ? `?${query}` : ''}`)
}

export function registrarEmprestimo(dados) {
  return requisicao('/api/emprestimos', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function registrarDevolucao(emprestimoId, dados = {}) {
  return requisicao(`/api/emprestimos/${emprestimoId}/devolucao`, {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
