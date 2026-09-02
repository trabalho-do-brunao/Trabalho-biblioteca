import { Bell, CircleUserRound, Menu } from 'lucide-react'

export default function Topbar({ onToggleSidebar }) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar-icon-button topbar-menu"
        onClick={onToggleSidebar}
        aria-label="Abrir ou recolher menu lateral"
      >
        <Menu />
      </button>

      <div className="topbar-actions">
        <button type="button" className="topbar-icon-button" aria-label="Notificações" title="Notificações">
          <Bell />
        </button>
        <button type="button" className="topbar-icon-button" aria-label="Perfil" title="Perfil">
          <CircleUserRound />
        </button>
      </div>
    </header>
  )
}
