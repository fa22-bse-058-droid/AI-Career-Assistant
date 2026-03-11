import { motion } from 'framer-motion'

export default function AdminPanelPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">Admin Panel</h1>
        <p className="text-slate-400">Platform management, user control, and analytics</p>
      </motion.div>
      <div className="glass-card p-8 text-center">
        <p className="text-slate-400">Admin dashboard with full platform controls</p>
      </div>
    </div>
  )
}
