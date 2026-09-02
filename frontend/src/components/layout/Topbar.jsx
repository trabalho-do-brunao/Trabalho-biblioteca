import { Bell, CircleUserRound, Menu } from 'lucide-react'

import Tooltip from '../ui/Tooltip'

export default function Topbar({ onToggleSidebar }) {
  return (
    <header className="topbar">
      <Tooltip content="Abrir ou recolher o menu lateral">
        <button
          type="button"
          className="topbar-icon-button topbar-menu"
          onClick={onToggleSidebar}
          aria-label="Abrir ou recolher menu lateral"
        >
          <Menu />
        </button>
      </Tooltip>

      <div className="topbar-actions">
        <Tooltip content="Notificações do sistema">
          <button type="button" className="topbar-icon-button" aria-label="Notificações">
            <Bell />
          </button>
        </Tooltip>
        <Tooltip content="Perfil e opções da conta">
          <button type="button" className="topbar-icon-button" aria-label="Perfil">
            <CircleUserRound />
          </button>
        </Tooltip>
      </div>
    </header>
  )
}
