import { motion } from 'framer-motion'

export default function ResourceHubPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">Resource Hub</h1>
        <p className="text-slate-400">Personalized learning recommendations based on your skill gaps</p>
      </motion.div>
      <div className="glass-card p-8 text-center">
        <p className="text-slate-400">Upload your CV to get personalized resource recommendations</p>
      </div>
    </div>
  )
}
