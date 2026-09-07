import { requisicao } from './api'

export function listarMensagensWhatsapp({
  busca = '',
  status = '',
  tipo = '',
  direcao = '',
  dataInicio = '',
  dataFim = '',
} = {}) {
  const params = new URLSearchParams()
  if (busca.trim()) params.set('busca', busca.trim())
  if (status) params.set('status', status)
  if (tipo) params.set('tipo', tipo)
  if (direcao) params.set('direcao', direcao)
  if (dataInicio) params.set('data_inicio', dataInicio)
  if (dataFim) params.set('data_fim', dataFim)

  const query = params.toString()
  return requisicao(`/api/whatsapp/mensagens${query ? `?${query}` : ''}`)
}
