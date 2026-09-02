import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'

import Sidebar from './Sidebar'
import Topbar from './Topbar'
import './layout.css'

const MOBILE_BREAKPOINT = 820

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== 'undefined' && window.innerWidth >= MOBILE_BREAKPOINT,
  )

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < MOBILE_BREAKPOINT) {
        setSidebarOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const closeOnMobile = () => {
    if (window.innerWidth < MOBILE_BREAKPOINT) {
      setSidebarOpen(false)
    }
  }

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <Sidebar open={sidebarOpen} onNavigate={closeOnMobile} />
      <Topbar onToggleSidebar={() => setSidebarOpen((open) => !open)} />

      <main className="app-content">
        <Outlet />
      </main>

      <button
        className="sidebar-backdrop"
        type="button"
        aria-label="Fechar menu lateral"
        onClick={() => setSidebarOpen(false)}
      />
    </div>
  )
}
