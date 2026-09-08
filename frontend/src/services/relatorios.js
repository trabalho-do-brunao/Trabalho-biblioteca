import { API_URL, ApiError, requisicao } from './api.js'

function periodoQuery(dataInicio, dataFim) {
  const params = new URLSearchParams({
    data_inicio: dataInicio,
    data_fim: dataFim,
  })
  return params.toString()
}

async function erroPdf(resposta) {
  try {
    const payload = await resposta.json()
    if (typeof payload?.detail === 'string') return payload.detail
  } catch {
    // O backend pode responder sem JSON em falhas inesperadas.
  }
  return `Não foi possível gerar o relatório (HTTP ${resposta.status}).`
}

export async function gerarRelatorioPdf(dataInicio, dataFim) {
  let resposta
  try {
    resposta = await fetch(`${API_URL}/api/relatorios/pdf?${periodoQuery(dataInicio, dataFim)}`, {
      headers: { Accept: 'application/pdf' },
    })
  } catch (erro) {
    throw new ApiError('Não foi possível conectar ao servidor do BiblioAvisa.', {
      type: 'connection',
      details: erro,
    })
  }

  if (!resposta.ok) {
    throw new ApiError(await erroPdf(resposta), { status: resposta.status })
  }

  const blob = await resposta.blob()
  if (!blob.size) {
    throw new ApiError('O servidor gerou um PDF vazio.', { type: 'invalid-response' })
  }

  const disposition = resposta.headers.get('content-disposition') || ''
  const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i)
  const filename = match ? decodeURIComponent(match[1].replace(/\"/g, '')) : 'relatorio_biblioavisa.pdf'

  return { blob, filename }
}

export function enviarRelatorioEmail(dataInicio, dataFim) {
  return requisicao('/api/relatorios/email', {
    method: 'POST',
    body: JSON.stringify({
      data_inicio: dataInicio,
      data_fim: dataFim,
    }),
    timeoutMs: 30000,
  })
}
