import { requisicao } from './api'

export function listarEventosAuditoria({
  acao = '',
  entidade = '',
  entidadeId = '',
  limite = 20,
  deslocamento = 0,
} = {}) {
  const params = new URLSearchParams()
  params.set('limite', String(limite))
  params.set('deslocamento', String(deslocamento))
  if (acao) params.set('acao', acao)
  if (entidade) params.set('entidade', entidade)
  if (entidadeId !== '' && entidadeId !== null && entidadeId !== undefined) {
    params.set('entidade_id', String(entidadeId))
  }
  return requisicao(`/api/auditoria/eventos?${params.toString()}`)
}
