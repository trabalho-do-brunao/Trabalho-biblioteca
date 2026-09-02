const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const DEFAULT_TIMEOUT_MS = 10000

export class ApiError extends Error {
  constructor(message, { type = 'http', status = null, details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.type = type
    this.status = status
    this.details = details
  }
}

function mensagemHttpPadrao(status) {
  if (status === 400) return 'Os dados enviados são inválidos.'
  if (status === 401) return 'Seu acesso não foi autorizado.'
  if (status === 403) return 'Você não possui permissão para realizar esta operação.'
  if (status === 404) return 'O recurso solicitado não foi encontrado.'
  if (status === 409) return 'A operação não pôde ser concluída porque existe um conflito nos dados.'
  if (status === 422) return 'Revise os campos informados e tente novamente.'
  if (status >= 500) return 'O servidor encontrou um problema. Tente novamente em instantes.'
  return `A operação não pôde ser concluída (HTTP ${status}).`
}

function extrairMensagemSegura(payload, status) {
  if (!payload || typeof payload !== 'object') return mensagemHttpPadrao(status)

  if (typeof payload.detail === 'string' && payload.detail.length <= 300) {
    return payload.detail
  }

  if (typeof payload.message === 'string' && payload.message.length <= 300) {
    return payload.message
  }

  return mensagemHttpPadrao(status)
}

export function mensagemErroApi(error) {
  if (!(error instanceof ApiError)) {
    return 'Ocorreu um erro inesperado. Tente novamente.'
  }

  if (error.type === 'timeout') {
    return 'O servidor demorou para responder. Verifique a conexão e tente novamente.'
  }

  if (error.type === 'connection') {
    return 'Não foi possível conectar ao servidor do BiblioAvisa. Verifique se o backend está em execução.'
  }

  if (error.type === 'invalid-response') {
    return 'O servidor respondeu em um formato inesperado. Tente novamente.'
  }

  return error.message || mensagemHttpPadrao(error.status)
}

async function lerResposta(resposta) {
  const contentType = resposta.headers.get('content-type') || ''
  if (resposta.status === 204) return null

  if (contentType.includes('application/json')) {
    try {
      return await resposta.json()
    } catch {
      throw new ApiError('O servidor respondeu em um formato inválido.', {
        type: 'invalid-response',
        status: resposta.status,
      })
    }
  }

  const texto = await resposta.text()
  return texto || null
}

async function requisicao(caminho, opcoes = {}) {
  const controller = new AbortController()
  const timeoutMs = opcoes.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      signal: opcoes.signal || controller.signal,
      headers: {
        Accept: 'application/json',
        ...(opcoes.body && !opcoes.headers?.['Content-Type'] ? { 'Content-Type': 'application/json' } : {}),
        ...(opcoes.headers || {}),
      },
    })

    const payload = await lerResposta(resposta)

    if (!resposta.ok) {
      throw new ApiError(extrairMensagemSegura(payload, resposta.status), {
        status: resposta.status,
        details: payload,
      })
    }

    return payload
  } catch (error) {
    if (error instanceof ApiError) throw error

    if (error?.name === 'AbortError') {
      throw new ApiError('Tempo de resposta excedido.', { type: 'timeout' })
    }

    if (error instanceof TypeError) {
      throw new ApiError('Falha de conexão com a API.', { type: 'connection' })
    }

    throw new ApiError('Falha inesperada ao acessar a API.', { type: 'unknown' })
  } finally {
    clearTimeout(timeoutId)
  }
}

export function verificarSaudeApi() {
  return requisicao('/api/health')
}

export { API_URL, requisicao }
