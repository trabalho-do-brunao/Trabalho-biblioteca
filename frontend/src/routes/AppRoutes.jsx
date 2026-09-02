import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from '../components/layout/AppLayout'
import Configuracoes from '../pages/Configuracoes'
import Dashboard from '../pages/Dashboard'
import Emprestimos from '../pages/Emprestimos'
import Livros from '../pages/Livros'
import Login from '../pages/Login'
import Relatorios from '../pages/Relatorios'
import Usuarios from '../pages/Usuarios'
import WhatsApp from '../pages/WhatsApp'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/livros" element={<Livros />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/emprestimos" element={<Emprestimos />} />
        <Route path="/whatsapp" element={<WhatsApp />} />
        <Route path="/relatorios" element={<Relatorios />} />
        <Route path="/configuracoes" element={<Configuracoes />} />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
