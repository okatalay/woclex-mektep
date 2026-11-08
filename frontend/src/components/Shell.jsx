import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Archive, BookOpen, GraduationCap, LayoutDashboard, LineChart, ListChecks, LogOut, Megaphone, MessageCircle, MoreHorizontal, NotebookPen, Route as RouteIcon, Users } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from './auth.jsx'
import { useLoad } from './hooks'
import { tr } from '../i18n/tr'
import { Sheet } from './ui.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'

export function useNav() {
  const { can, roleKey } = useAuth()
  const { data } = useLoad(() => api.get('/messages/unread-count'), [])
  const manageClasses = can('classroom.create') || can('classroom.manage_all')
  return [
    { to: '/panel', label: 'Ana Sayfa', icon: LayoutDashboard, end: true },
    manageClasses && { to: '/panel/siniflar', label: 'Sınıflarım', icon: GraduationCap },
    manageClasses && { to: '/panel/tilavet', label: 'Tilavet', icon: BookOpen },
    manageClasses && { to: '/panel/rota-arsivi', label: 'Rota', icon: RouteIcon },
    manageClasses && { to: '/panel/arsiv', label: 'Arşiv', icon: Archive },
    manageClasses && { to: '/panel/mufredat', label: 'Müfredat', icon: ListChecks },
    roleKey === 'student' && { to: '/panel/odevlerim', label: 'Ödevlerim', icon: NotebookPen },
    roleKey === 'student' && { to: '/panel/rotalarim', label: 'Rotalarım', icon: RouteIcon },
    roleKey === 'student' && { to: '/panel/gelisimim', label: 'Gelişimim', icon: LineChart },
    roleKey === 'guardian' && { to: '/panel/cocuklarim', label: 'Çocuklarım', icon: Users },
    { to: '/panel/mesajlar', label: 'Mesajlar', icon: MessageCircle, badge: data?.unread_count },
    (roleKey === 'student' || roleKey === 'guardian') && { to: '/panel/duyurular', label: 'Duyurular', icon: Megaphone },
  ].filter(Boolean)
}

export default function Shell() {
  const { user, logout } = useAuth()
  const nav = useNav()
  const [more, setMore] = useState(false)
  const { pathname } = useLocation()
  const primary = nav.slice(0, 4)
  const rest = nav.slice(4)

  return (
    <div className="app">
      <a className="skip" href="#icerik">İçeriğe geç</a>
      <aside className="sidebar" aria-label="Ana menü">
        <NavLink to="/panel" className="brand">
          <span className="brand-mark"><BookOpen size={16} aria-hidden="true" /></span>
          Mektep
        </NavLink>
        <nav className="nav">
          {nav.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              <n.icon size={18} aria-hidden="true" />
              {n.label}
              {n.badge > 0 && <span className="nav-badge">{n.badge}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="me">
            <strong>{user.full_name}</strong>
            <span>{user.organization.name} · {tr.role[user.role.system_key] || user.role.name}</span>
          </div>
          <div className="nav">
            <button className="nav-logout" onClick={logout}><LogOut size={18} aria-hidden="true" />Çıkış yap</button>
          </div>
        </div>
      </aside>

      <main className="main" id="icerik">
        <div className="main-inner" key={pathname.split('/').slice(0, 4).join('/')}>
          <ErrorBoundary resetKey={pathname}>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>

      <nav className="tabbar" aria-label="Sekmeler">
        {primary.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end}>
            <n.icon size={22} aria-hidden="true" />
            {n.label}
            {n.badge > 0 && <span className="nav-badge">{n.badge}</span>}
          </NavLink>
        ))}
        {rest.length > 0 && (
          <button onClick={() => setMore(true)} aria-haspopup="dialog">
            <MoreHorizontal size={22} aria-hidden="true" />
            Diğer
          </button>
        )}
      </nav>
      {more && (
        <Sheet title="Menü" onClose={() => setMore(false)}>
          <nav className="nav" onClick={() => setMore(false)}>
            {rest.map((n) => (
              <NavLink key={n.to} to={n.to}>
                <n.icon size={18} aria-hidden="true" />
                {n.label}
              </NavLink>
            ))}
            <button className="nav-logout" onClick={logout}><LogOut size={18} aria-hidden="true" />Çıkış yap</button>
          </nav>
        </Sheet>
      )}
    </div>
  )
}
