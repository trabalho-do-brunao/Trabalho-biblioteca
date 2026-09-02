const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function requisicao(caminho, opcoes = {}) {
  const resposta = await fetch(`${API_URL}${caminho}`, {
    ...opcoes,
    headers: {
      Accept: 'application/json',
      ...(opcoes.headers || {}),
    },
  })

  if (!resposta.ok) {
    throw new Error(`API respondeu com HTTP ${resposta.status}`)
  }

  return resposta.json()
}

export function verificarSaudeApi() {
  return requisicao('/api/health')
}

export { API_URL, requisicao }
