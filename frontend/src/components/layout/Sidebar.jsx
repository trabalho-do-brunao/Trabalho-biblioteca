import {
  BarChart3,
  BookOpen,
  BookOpenCheck,
  House,
  LogOut,
  MessageCircle,
  Settings,
  Users,
} from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'

const items = [
  { to: '/dashboard', label: 'Dashboard', icon: House },
  { to: '/livros', label: 'Livros', icon: BookOpen },
  { to: '/usuarios', label: 'Usuários', icon: Users },
  { to: '/emprestimos', label: 'Empréstimos', icon: BookOpenCheck },
  { to: '/whatsapp', label: 'WhatsApp', icon: MessageCircle },
  { to: '/relatorios', label: 'Relatórios', icon: BarChart3 },
  { to: '/configuracoes', label: 'Configurações', icon: Settings },
]

export default function Sidebar({ open, onNavigate }) {
  const navigate = useNavigate()

  const handleExit = () => {
    onNavigate?.()
    navigate('/login')
  }

  return (
    <aside className="sidebar" aria-label="Navegação principal">
      <div className="sidebar-brand" title="Biblioteca">
        <span className="sidebar-brand-full">BIBLIOTECA</span>
        <span className="sidebar-brand-short" aria-hidden="true">B</span>
      </div>

      <nav className="sidebar-nav">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={!open ? label : undefined}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
            onClick={onNavigate}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <button className="sidebar-exit" type="button" onClick={handleExit} title={!open ? 'Sair' : undefined}>
        <LogOut aria-hidden="true" />
        <span>Sair</span>
      </button>
    </aside>
  )
}
