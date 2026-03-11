import { motion } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Bell, CheckCheck } from 'lucide-react'
import api from '@/api/axios'

export default function NotificationsPage() {
  const { data, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/notifications/').then((r) => r.data.results || r.data),
  })

  const markAllRead = useMutation({
    mutationFn: () => api.post('/notifications/mark-read/'),
    onSuccess: () => refetch(),
  })

  const notifications = data || []

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Notifications</h1>
          <p className="text-slate-400">{notifications.filter((n: any) => !n.is_read).length} unread</p>
        </div>
        <button
          onClick={() => markAllRead.mutate()}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <CheckCheck size={16} /> Mark all read
        </button>
      </motion.div>

      <div className="space-y-3">
        {notifications.map((notif: any, i: number) => (
          <motion.div
            key={notif.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`glass-card p-4 flex items-start gap-4 ${
              !notif.is_read ? 'border-l-2 border-l-accent-blue shadow-glow' : ''
            }`}
          >
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center flex-shrink-0">
              <Bell size={14} className="text-accent-blue" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium">{notif.title}</p>
              <p className="text-slate-400 text-xs mt-0.5">{notif.message}</p>
              <p className="text-slate-600 text-xs mt-1">
                {new Date(notif.created_at).toLocaleString()}
              </p>
            </div>
            {!notif.is_read && (
              <div className="w-2 h-2 rounded-full bg-accent-blue flex-shrink-0 mt-1 animate-pulse" />
            )}
          </motion.div>
        ))}

        {notifications.length === 0 && (
          <div className="text-center py-16 text-slate-500">
            <Bell size={48} className="mx-auto mb-4 opacity-30" />
            <p>No notifications yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
