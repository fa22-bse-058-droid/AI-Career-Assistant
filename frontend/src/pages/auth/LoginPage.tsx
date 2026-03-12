import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, Zap, Brain, Target, Shield } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import api from '@/api/axios'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

// Floating particle data
const PARTICLES = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 4 + 2,
  duration: Math.random() * 8 + 6,
  delay: Math.random() * 4,
}))

const features = [
  { icon: Brain, text: 'AI-Powered CV Analysis', color: '#3B82F6' },
  { icon: Target, text: 'Smart Job Matching', color: '#8B5CF6' },
  { icon: Zap, text: 'Auto-Apply to 100s of Jobs', color: '#06B6D4' },
  { icon: Shield, text: 'Secure & Private by Design', color: '#10B981' },
]

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [lockoutSeconds, setLockoutSeconds] = useState<number | null>(null)
  const [loginSuccess, setLoginSuccess] = useState(false)
  const lockoutTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    setError,
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const emailValue = watch('email', '')
  const passwordValue = watch('password', '')

  // Countdown timer for lockout
  useEffect(() => {
    if (lockoutSeconds && lockoutSeconds > 0) {
      lockoutTimerRef.current = setInterval(() => {
        setLockoutSeconds((s) => {
          if (s && s <= 1) {
            clearInterval(lockoutTimerRef.current!)
            return null
          }
          return s ? s - 1 : null
        })
      }, 1000)
    }
    return () => {
      if (lockoutTimerRef.current) clearInterval(lockoutTimerRef.current)
    }
  }, [lockoutSeconds])

  const formatCountdown = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    setLockoutSeconds(null)
    try {
      const response = await api.post('/auth/login/', data)
      const { access } = response.data

      // Fetch full user details
      const userRes = await api.get('/auth/me/', {
        headers: { Authorization: `Bearer ${access}` },
      })
      setAuth(userRes.data, access)
      setLoginSuccess(true)
      setTimeout(() => navigate('/dashboard'), 600)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string; lockout_seconds_remaining?: number } } }
      const detail = axiosErr.response?.data?.detail || 'Login failed. Please try again.'
      const lockout = axiosErr.response?.data?.lockout_seconds_remaining
      if (lockout) setLockoutSeconds(lockout)
      setError('root', { message: detail })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex overflow-hidden" style={{ background: '#0A0F1E' }}>
      {/* Left Panel — Animated Gradient */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
        className="hidden lg:flex flex-1 relative items-center justify-center overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #0A0F1E 0%, #0d0626 40%, #1a0533 100%)',
        }}
      >
        {/* Grid overlay */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              'linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* Floating particles */}
        {PARTICLES.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              background: p.id % 3 === 0 ? '#3B82F6' : p.id % 3 === 1 ? '#8B5CF6' : '#06B6D4',
              opacity: 0.4,
            }}
            animate={{
              y: [0, -20, 0],
              opacity: [0.3, 0.7, 0.3],
            }}
            transition={{
              duration: p.duration,
              delay: p.delay,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}

        {/* Glow orbs */}
        <div
          className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute bottom-1/4 right-1/4 w-48 h-48 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)',
          }}
        />

        {/* Content */}
        <div className="relative z-10 text-center px-10 max-w-md">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6"
              style={{
                background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                boxShadow: '0 0 40px rgba(59,130,246,0.4), 0 0 80px rgba(139,92,246,0.2)',
              }}
            >
              <span className="text-white font-black text-3xl">C</span>
            </div>

            <motion.h1
              className="text-4xl font-black mb-2"
              style={{
                background: 'linear-gradient(135deg, #ffffff, #94a3b8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textShadow: 'none',
                filter: 'drop-shadow(0 0 20px rgba(59,130,246,0.4))',
              }}
            >
              CareerAI
            </motion.h1>
            <p className="text-slate-400 mb-10 text-lg">Your AI-powered career accelerator</p>
          </motion.div>

          <motion.div
            className="space-y-4"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: 0.1, delayChildren: 0.5 } },
            }}
          >
            {features.map(({ icon: Icon, text, color }) => (
              <motion.div
                key={text}
                className="flex items-center gap-4 text-left"
                variants={{
                  hidden: { opacity: 0, x: -20 },
                  visible: { opacity: 1, x: 0 },
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: `${color}22`, border: `1px solid ${color}44` }}
                >
                  <Icon size={18} style={{ color }} />
                </div>
                <span className="text-slate-300 text-sm font-medium">{text}</span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Right Panel — Glassmorphism card */}
      <div
        className="flex-1 flex items-center justify-center px-6 py-12"
        style={{ background: '#0A0F1E' }}
      >
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 30 }}
          animate={loginSuccess ? { scale: 1.05, opacity: 0 } : { opacity: 1, y: 0 }}
          transition={loginSuccess ? { duration: 0.5 } : { duration: 0.6, ease: 'easeOut' }}
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-8">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)' }}
            >
              <span className="text-white font-black text-lg">C</span>
            </div>
            <span className="text-white font-bold text-xl">CareerAI</span>
          </div>

          {/* Glass card */}
          <div
            className="rounded-2xl p-8"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
          >
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-white mb-1">Welcome back</h1>
              <p className="text-sm" style={{ color: 'rgba(232,234,240,0.6)' }}>
                Sign in to your CareerAI account
              </p>
            </div>

            {/* Error message */}
            <AnimatePresence>
              {errors.root && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="mb-6 shake"
                >
                  <div
                    className="p-4 rounded-xl"
                    style={{
                      background: 'rgba(239,68,68,0.1)',
                      border: '1px solid rgba(239,68,68,0.3)',
                    }}
                  >
                    <p className="text-sm" style={{ color: '#EF4444' }}>
                      {errors.root.message}
                    </p>
                    {lockoutSeconds && lockoutSeconds > 0 && (
                      <p className="text-xs mt-1" style={{ color: 'rgba(239,68,68,0.8)' }}>
                        Account locked. Try again in{' '}
                        <span className="font-bold font-mono">
                          {formatCountdown(lockoutSeconds)}
                        </span>
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Email field with floating label */}
              <FloatingInput
                id="email"
                type="email"
                label="Email Address"
                icon={<Mail size={16} />}
                registration={register('email')}
                error={errors.email?.message}
                value={emailValue}
              />

              {/* Password field */}
              <FloatingInput
                id="password"
                type={showPassword ? 'text' : 'password'}
                label="Password"
                icon={<Lock size={16} />}
                registration={register('password')}
                error={errors.password?.message}
                value={passwordValue}
                rightElement={
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="p-1 rounded"
                    style={{ color: 'rgba(232,234,240,0.5)' }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                }
              />

              {/* Submit button */}
              <motion.button
                type="submit"
                disabled={isLoading || (lockoutSeconds !== null && lockoutSeconds > 0)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-3 rounded-xl font-semibold text-white relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                style={{
                  background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                }}
                onMouseEnter={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.boxShadow =
                    '0 0 20px rgba(59,130,246,0.5), 0 0 40px rgba(139,92,246,0.3)'
                }}
                onMouseLeave={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.boxShadow = 'none'
                }}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.span
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    />
                    Signing in…
                  </span>
                ) : (
                  'Sign In'
                )}
              </motion.button>
            </form>

            <p className="mt-6 text-center text-sm" style={{ color: 'rgba(232,234,240,0.5)' }}>
              Don&apos;t have an account?{' '}
              <Link
                to="/register"
                className="font-semibold transition-colors"
                style={{ color: '#3B82F6' }}
                onMouseEnter={(e) => ((e.target as HTMLAnchorElement).style.color = '#8B5CF6')}
                onMouseLeave={(e) => ((e.target as HTMLAnchorElement).style.color = '#3B82F6')}
              >
                Create one free
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// ─── Floating-label input component ───────────────────────────────────────────

interface FloatingInputProps {
  id: string
  type: string
  label: string
  icon: React.ReactNode
  registration: ReturnType<ReturnType<typeof useForm>['register']>
  error?: string
  value: string
  rightElement?: React.ReactNode
}

function FloatingInput({
  id,
  type,
  label,
  icon,
  registration,
  error,
  value,
  rightElement,
}: FloatingInputProps) {
  const [focused, setFocused] = useState(false)
  const floated = focused || Boolean(value)

  return (
    <div>
      <div className="relative">
        {/* Icon */}
        <div
          className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors"
          style={{ color: focused ? '#3B82F6' : 'rgba(232,234,240,0.4)' }}
        >
          {icon}
        </div>

        {/* Floating label */}
        <motion.label
          htmlFor={id}
          className="absolute left-11 pointer-events-none origin-left text-sm select-none"
          animate={{
            y: floated ? -20 : 0,
            scale: floated ? 0.82 : 1,
            color: focused ? '#3B82F6' : 'rgba(232,234,240,0.5)',
          }}
          transition={{ duration: 0.18 }}
          style={{ top: '50%', translateY: '-50%' }}
        >
          {label}
        </motion.label>

        <input
          id={id}
          type={type}
          {...registration}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="w-full pl-11 pr-11 pt-5 pb-2 rounded-xl bg-transparent text-white text-sm outline-none transition-all"
          style={{
            background: 'rgba(255,255,255,0.05)',
            border: `1px solid ${
              error
                ? 'rgba(239,68,68,0.5)'
                : focused
                ? 'rgba(59,130,246,0.6)'
                : 'rgba(255,255,255,0.1)'
            }`,
            boxShadow: focused ? '0 0 0 3px rgba(59,130,246,0.1)' : 'none',
          }}
        />

        {/* Right element (eye toggle, etc.) */}
        {rightElement && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">{rightElement}</div>
        )}
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1.5 text-xs pl-1"
          style={{ color: '#EF4444' }}
        >
          {error}
        </motion.p>
      )}
    </div>
  )
}

