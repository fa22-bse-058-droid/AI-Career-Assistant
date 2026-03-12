import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, FileText, Briefcase, MessageCircle, BookOpen,
  Users, Zap, Bell, Video, Shield, User, LogOut, ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import api from '@/api/axios'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/cv', icon: FileText, label: 'CV Analyzer' },
  { to: '/jobs', icon: Briefcase, label: 'Job Board' },
  { to: '/chat', icon: MessageCircle, label: 'AI Chatbot' },
  { to: '/resources', icon: BookOpen, label: 'Resources' },
  { to: '/forum', icon: Users, label: 'Forum' },
  { to: '/auto-apply', icon: Zap, label: 'Auto-Apply' },
  { to: '/notifications', icon: Bell, label: 'Notifications' },
  { to: '/interview', icon: Video, label: 'Mock Interview' },
  { to: '/profile', icon: User, label: 'Profile' },
]

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/', {})
    } catch {}
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#0A0F1E]">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="flex flex-col bg-[#0D1117] border-r border-white/5 z-10 overflow-hidden"
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-white text-sm"
            >
              Career Platform
            </motion.span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group',
                  isActive
                    ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/20'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    size={18}
                    className={clsx(
                      'flex-shrink-0',
                      isActive ? 'text-accent-blue' : 'text-slate-500 group-hover:text-white'
                    )}
                  />
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </>
              )}
            </NavLink>
          ))}

          {user?.role === 'admin' && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-red-500/20 text-red-400 border border-red-500/20'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                )
              }
            >
              <Shield size={18} className="flex-shrink-0" />
              {!collapsed && <span>Admin Panel</span>}
            </NavLink>
          )}
        </nav>

        {/* Collapse + Logout */}
        <div className="p-2 border-t border-white/5 space-y-1">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
          >
            <LogOut size={18} className="flex-shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center w-full py-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className="min-h-full p-6"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
