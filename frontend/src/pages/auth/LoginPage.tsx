import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, AlertTriangle } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import api from '@/api/axios'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [lockoutSeconds, setLockoutSeconds] = useState<number | null>(null)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    setLockoutSeconds(null)
    try {
      const response = await api.post('/auth/login/', data)
      const { user, access, refresh } = response.data

      // Fetch user details
      const userRes = await api.get('/auth/me/', {
        headers: { Authorization: `Bearer ${access}` },
      })
      setAuth(userRes.data, access, refresh)
      navigate('/dashboard')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Login failed'
      const lockout = err.response?.data?.lockout_seconds_remaining
      if (lockout) {
        setLockoutSeconds(lockout)
      }
      setError('root', { message: detail })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left: Animated Gradient */}
      <div className="hidden lg:flex flex-1 hero-gradient relative items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.05)_1px,transparent_1px)] bg-[size:40px_40px]" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="relative z-10 text-center px-8"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center mx-auto mb-6">
            <span className="text-white font-black text-2xl">AI</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">AI Career Platform</h2>
          <p className="text-slate-400 max-w-sm">
            Your intelligent career assistant powered by cutting-edge AI
          </p>
        </motion.div>
      </div>

      {/* Right: Login Form */}
      <div className="flex-1 flex items-center justify-center px-6 bg-[#0D1117]">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-full max-w-md"
        >
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
            <p className="text-slate-400">Sign in to your account</p>
          </div>

          {errors.root && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 mb-6"
            >
              <AlertTriangle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-red-400 text-sm">{errors.root.message}</p>
                {lockoutSeconds && (
                  <p className="text-red-300 text-xs mt-1">
                    Account locked for {Math.ceil(lockoutSeconds / 60)} minutes
                  </p>
                )}
              </div>
            </motion.div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="text-sm text-slate-400 mb-1.5 block">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  {...register('email')}
                  type="email"
                  placeholder="you@example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/30 transition-all"
                />
              </div>
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1.5 block">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-10 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/30 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="glow-button w-full py-3 rounded-lg text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <motion.div
                    className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </motion.button>
          </form>

          <p className="text-center text-slate-400 text-sm mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-accent-blue hover:text-accent-purple transition-colors">
              Create one
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
