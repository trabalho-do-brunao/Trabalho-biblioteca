import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import {
  consultarSessaoAdministrador,
  loginAdministrador,
  logoutAdministrador,
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [admin, setAdmin] = useState(null)
  const [loading, setLoading] = useState(true)

  const atualizarSessao = useCallback(async () => {
    try {
      const resposta = await consultarSessaoAdministrador()
      setAdmin(resposta?.authenticated ? resposta.admin : null)
      return resposta?.authenticated ? resposta.admin : null
    } catch {
      setAdmin(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    atualizarSessao()
  }, [atualizarSessao])

  useEffect(() => {
    const handleUnauthorized = () => {
      setAdmin(null)
      setLoading(false)
    }

    window.addEventListener('biblioavisa:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('biblioavisa:unauthorized', handleUnauthorized)
  }, [])

  const entrar = useCallback(async (email, senha) => {
    const resposta = await loginAdministrador(email, senha)
    setAdmin(resposta.admin)
    setLoading(false)
    return resposta.admin
  }, [])

  const sair = useCallback(async () => {
    await logoutAdministrador()
    setAdmin(null)
    setLoading(false)
  }, [])

  const valor = useMemo(
    () => ({
      admin,
      authenticated: Boolean(admin),
      loading,
      entrar,
      sair,
      atualizarSessao,
    }),
    [admin, loading, entrar, sair, atualizarSessao],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider.')
  }
  return contexto
}
