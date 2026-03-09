import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Zap, Brain, Target, Shield, TrendingUp, Users } from 'lucide-react'

const features = [
  { icon: Brain, title: 'AI CV Analyzer', desc: 'Get scored 0-100 with skill gap detection', color: 'accent-blue' },
  { icon: Target, title: 'Smart Job Matching', desc: 'MiniLM semantic similarity matching', color: 'accent-purple' },
  { icon: Zap, title: 'Auto-Apply', desc: 'Automatically apply to matching jobs', color: 'accent-cyan' },
  { icon: Users, title: 'AI Mock Interviews', desc: 'Practice with AI-evaluated responses', color: 'accent-blue' },
  { icon: TrendingUp, title: 'Resource Hub', desc: 'Personalized learning recommendations', color: 'accent-purple' },
  { icon: Shield, title: 'Career Forum', desc: 'Community with gamified rewards', color: 'accent-cyan' },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0F1E] overflow-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-[#0A0F1E]/80 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <span className="font-bold text-white">Career Platform</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-slate-400 hover:text-white transition-colors text-sm">
            Sign In
          </Link>
          <Link
            to="/register"
            className="glow-button px-4 py-2 rounded-lg text-white text-sm font-medium"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-gradient relative flex flex-col items-center justify-center min-h-screen text-center px-4 pt-20">
        {/* Animated grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

        {/* Floating orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-accent-blue/5 blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-accent-purple/5 blur-3xl animate-float" style={{ animationDelay: '1.5s' }} />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 max-w-4xl"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-blue/10 border border-accent-blue/20 text-accent-blue text-sm mb-6"
          >
            <Zap size={14} />
            <span>Powered by AI & Machine Learning</span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight">
            Land Your{' '}
            <span className="gradient-text">Dream Career</span>
            {' '}Faster
          </h1>

          <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            AI-powered CV analysis, smart job matching, automated applications, and personalized
            interview coaching — all in one platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/register"
                className="glow-button inline-flex items-center gap-2 px-8 py-4 rounded-xl text-white font-semibold text-lg"
              >
                Start Free <ArrowRight size={20} />
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl text-white font-semibold text-lg glass-card hover:bg-white/10 transition-all"
              >
                Sign In
              </Link>
            </motion.div>
          </div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          <div className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-1">
            <div className="w-1 h-2 bg-white/40 rounded-full" />
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-24 px-4 max-w-6xl mx-auto">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.h2
            variants={itemVariants}
            className="text-4xl font-bold text-center text-white mb-4"
          >
            Everything You Need to Succeed
          </motion.h2>
          <motion.p
            variants={itemVariants}
            className="text-slate-400 text-center mb-16 max-w-2xl mx-auto"
          >
            10 powerful AI modules designed to accelerate your career journey
          </motion.p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                whileHover={{ y: -4, scale: 1.02 }}
                className="glass-card p-6 cursor-default group"
              >
                <div className={`w-12 h-12 rounded-xl bg-${feature.color}/10 border border-${feature.color}/20 flex items-center justify-center mb-4 group-hover:shadow-glow transition-all`}>
                  <feature.icon size={24} className={`text-${feature.color}`} />
                </div>
                <h3 className="text-white font-semibold mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* CTA */}
      <section className="py-24 text-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="glass-card max-w-3xl mx-auto p-12"
        >
          <h2 className="text-4xl font-bold text-white mb-4">Ready to launch your career?</h2>
          <p className="text-slate-400 mb-8">Join thousands of students getting hired faster with AI.</p>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              to="/register"
              className="glow-button inline-flex items-center gap-2 px-10 py-4 rounded-xl text-white font-bold text-lg"
            >
              Get Started Free <ArrowRight size={20} />
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-slate-500 text-sm">
        <p>© 2024 AI Career Platform — Built by FA22-BSE-058 @ COMSATS University</p>
      </footer>
    </div>
  )
}
