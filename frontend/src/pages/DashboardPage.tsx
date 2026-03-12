import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  FileText, Briefcase, MessageCircle, Video,
  TrendingUp, Users, Zap, Bell, ArrowRight, Activity,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/api/axios'

function StatCard({ label, value, icon: Icon, color, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <p className="text-slate-400 text-sm">{label}</p>
        <div className={`w-10 h-10 rounded-lg bg-${color}/10 border border-${color}/20 flex items-center justify-center`}>
          <Icon size={18} className={`text-${color}`} />
        </div>
      </div>
      <motion.p
        className="text-3xl font-bold text-white"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.2 }}
      >
        {value ?? '—'}
      </motion.p>
    </motion.div>
  )
}

const quickActions = [
  { to: '/cv', icon: FileText, label: 'Analyze CV', color: 'accent-blue' },
  { to: '/jobs', icon: Briefcase, label: 'Browse Jobs', color: 'accent-purple' },
  { to: '/chat', icon: MessageCircle, label: 'Ask AI', color: 'accent-cyan' },
  { to: '/interview', icon: Video, label: 'Mock Interview', color: 'accent-blue' },
]

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [cvRes, matchRes, notifRes] = await Promise.allSettled([
        api.get('/cv/list/'),
        api.get('/jobs/matches/'),
        api.get('/notifications/'),
      ])
      return {
        cvCount: cvRes.status === 'fulfilled' ? cvRes.value.data.count : 0,
        matchCount: matchRes.status === 'fulfilled' ? matchRes.value.data.count : 0,
        notifCount: notifRes.status === 'fulfilled'
          ? notifRes.value.data.results?.filter((n: any) => !n.is_read).length
          : 0,
      }
    },
  })

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'},{' '}
            <span className="gradient-text">{user?.full_name?.split(' ')[0] || user?.email}</span> 👋
          </h1>
          <p className="text-slate-400 mt-1">Here's your career progress overview</p>
        </div>
        <motion.div
          className="flex items-center gap-2 px-4 py-2 rounded-full glass-card text-sm text-slate-400"
          animate={{ scale: [1, 1.02, 1] }}
          transition={{ repeat: Infinity, duration: 3 }}
        >
          <Activity size={14} className="text-accent-green" />
          <span>All systems online</span>
        </motion.div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="CVs Uploaded" value={stats?.cvCount} icon={FileText} color="accent-blue" delay={0.1} />
        <StatCard label="Job Matches" value={stats?.matchCount} icon={Briefcase} color="accent-purple" delay={0.2} />
        <StatCard label="Unread Notifications" value={stats?.notifCount} icon={Bell} color="accent-cyan" delay={0.3} />
        <StatCard label="Target Role" value={user?.profile?.target_role || 'Not set'} icon={TrendingUp} color="accent-green" delay={0.4} />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action, i) => (
            <motion.div
              key={action.to}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              whileHover={{ scale: 1.05, y: -2 }}
            >
              <Link
                to={action.to}
                className="flex flex-col items-center gap-3 p-6 glass-card hover:bg-white/10 transition-all group"
              >
                <div className={`w-12 h-12 rounded-xl bg-${action.color}/10 border border-${action.color}/20 flex items-center justify-center group-hover:shadow-glow transition-all`}>
                  <action.icon size={22} className={`text-${action.color}`} />
                </div>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  {action.label}
                </span>
                <ArrowRight size={14} className="text-slate-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Navigation to all modules */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">All Modules</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { to: '/resources', icon: TrendingUp, label: 'Resource Hub' },
            { to: '/forum', icon: Users, label: 'Community Forum' },
            { to: '/auto-apply', icon: Zap, label: 'Auto-Apply' },
            { to: '/notifications', icon: Bell, label: 'Notifications' },
          ].map((item, i) => (
            <motion.div
              key={item.to}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + i * 0.1 }}
            >
              <Link
                to={item.to}
                className="flex items-center gap-3 p-4 glass-card hover:bg-white/10 transition-all group"
              >
                <item.icon size={18} className="text-accent-blue group-hover:text-accent-purple transition-colors" />
                <span className="text-sm text-slate-300 group-hover:text-white transition-colors">{item.label}</span>
                <ArrowRight size={14} className="text-slate-600 ml-auto group-hover:text-white group-hover:translate-x-1 transition-all" />
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
