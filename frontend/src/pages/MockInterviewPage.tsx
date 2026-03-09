import { motion } from 'framer-motion'

export default function MockInterviewPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">AI Mock Interview</h1>
        <p className="text-slate-400">Practice with AI-evaluated questions and get scored feedback</p>
      </motion.div>
      <div className="glass-card p-8 text-center">
        <p className="text-slate-400">Select a domain and difficulty to begin your mock interview</p>
      </div>
    </div>
  )
}
