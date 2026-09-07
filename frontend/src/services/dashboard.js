import { requisicao } from './api'

export function carregarDashboard({ diasProximos = 2, limite = 10 } = {}) {
  const params = new URLSearchParams()
  params.set('dias_proximos', String(diasProximos))
  params.set('limite', String(limite))
  return requisicao(`/api/dashboard?${params.toString()}`)
}
