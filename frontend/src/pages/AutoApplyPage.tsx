import { motion } from 'framer-motion'

export default function AutoApplyPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">Auto-Apply</h1>
        <p className="text-slate-400">Automatically apply to matching jobs based on your CV</p>
      </motion.div>
      <div className="glass-card p-8 text-center">
        <p className="text-slate-400">Configure your auto-apply settings and let AI do the work</p>
      </div>
    </div>
  )
}
