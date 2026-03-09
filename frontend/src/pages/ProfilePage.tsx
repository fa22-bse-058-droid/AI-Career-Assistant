import { motion } from 'framer-motion'

export default function ProfilePage() {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">Profile</h1>
        <p className="text-slate-400">Manage your account and career preferences</p>
      </motion.div>
      <div className="glass-card p-8 text-center">
        <p className="text-slate-400">Update your profile, avatar, and career goals</p>
      </div>
    </div>
  )
}
