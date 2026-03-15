import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, User, GraduationCap, Building2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import api from '@/api/axios'

const CURRENT_YEAR = new Date().getFullYear()
const GRAD_YEARS = Array.from({ length: 10 }, (_, i) => CURRENT_YEAR + i)

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Full name must be at least 2 characters'),
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/\d/, 'Password must contain at least one number'),
    password_confirm: z.string(),
    role: z.enum(['student', 'employer']),
    university: z.string().optional(),
    graduation_year: z.preprocess(
      (val) => {
        if (val === '' || val === undefined || val === null) return undefined
        const n = Number(val)
        return isNaN(n) ? undefined : n
      },
      z.number().int().optional()
    ),
    terms: z.literal(true, { errorMap: () => ({ message: 'You must accept the terms' }) }),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: 'Passwords do not match',
    path: ['password_confirm'],
  })

type RegisterForm = z.infer<typeof registerSchema>

function getPasswordStrength(password: string): { score: number; label: string; color: string } {
  if (!password) return { score: 0, label: '', color: '' }
  let score = 0
  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++
  if (password.length >= 12) score++

  if (score <= 2) return { score, label: 'Weak', color: '#EF4444' }
  if (score <= 3) return { score, label: 'Medium', color: '#F59E0B' }
  return { score, label: 'Strong', color: '#10B981' }
}

// Floating particle data (same style as login)
const PARTICLES = Array.from({ length: 16 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 4 + 2,
  duration: Math.random() * 8 + 6,
  delay: Math.random() * 4,
}))

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    setError,
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'student' },
  })

  const role = watch('role')
  const password = watch('password', '')
  const strength = getPasswordStrength(password)

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      const { terms: _terms, ...payload } = data
      const response = await api.post('/auth/register/', payload)
      const { user, access } = response.data
      setAuth(user, access)
      navigate('/dashboard')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: Record<string, string | string[]> } }
      console.error('Register error:', axiosErr?.response?.status, axiosErr?.response?.data, err)
      const data = axiosErr.response?.data
      const firstMsg = data
        ? Object.values(data).flat()[0] ?? 'Registration failed'
        : 'Registration failed'
      setError('root', { message: String(firstMsg) })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex overflow-hidden" style={{ background: '#0A0F1E' }}>
      {/* Left Panel */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
        className="hidden lg:flex flex-1 relative items-center justify-center overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #0A0F1E 0%, #0d0626 40%, #1a0533 100%)',
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              'linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

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
            animate={{ y: [0, -20, 0], opacity: [0.3, 0.7, 0.3] }}
            transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: 'easeInOut' }}
          />
        ))}

        <div
          className="absolute top-1/3 left-1/3 w-64 h-64 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)' }}
        />

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
            <h1
              className="text-4xl font-black mb-2"
              style={{
                background: 'linear-gradient(135deg, #ffffff, #94a3b8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 20px rgba(59,130,246,0.4))',
              }}
            >
              CareerAI
            </h1>
            <p className="text-slate-400 text-lg mb-10">Join thousands of professionals</p>
          </motion.div>

          <motion.div
            className="space-y-5 text-left"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: 0.12, delayChildren: 0.5 } },
            }}
          >
            {[
              { emoji: '🎓', title: 'For Students', desc: 'AI CV scoring, skill gap analysis, job matching' },
              { emoji: '🏢', title: 'For Employers', desc: 'Post jobs, find top talent with AI ranking' },
              { emoji: '🚀', title: 'Free Forever', desc: 'Core features always free for students' },
            ].map(({ emoji, title, desc }) => (
              <motion.div
                key={title}
                className="flex items-start gap-4"
                variants={{ hidden: { opacity: 0, x: -20 }, visible: { opacity: 1, x: 0 } }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 text-lg"
                  style={{ background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)' }}
                >
                  {emoji}
                </div>
                <div>
                  <p className="text-white text-sm font-semibold">{title}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Right Panel */}
      <div
        className="flex-1 flex items-center justify-center px-6 py-10 overflow-y-auto"
        style={{ background: '#0A0F1E' }}
      >
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-6">
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
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
          >
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-white mb-1">Create account</h1>
              <p className="text-sm" style={{ color: 'rgba(232,234,240,0.6)' }}>
                Start your AI-powered career journey
              </p>
            </div>

            {/* Error banner */}
            <AnimatePresence>
              {errors.root && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="mb-5 p-4 rounded-xl text-sm"
                  style={{
                    background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)',
                    color: '#EF4444',
                  }}
                >
                  {errors.root.message}
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Role toggle */}
              <div>
                <p className="text-xs font-medium mb-2" style={{ color: 'rgba(232,234,240,0.6)' }}>
                  I am a…
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {(['student', 'employer'] as const).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setValue('role', r)}
                      className="py-2.5 rounded-xl text-sm font-semibold capitalize transition-all"
                      style={{
                        background:
                          role === r
                            ? 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(139,92,246,0.3))'
                            : 'rgba(255,255,255,0.05)',
                        border: role === r ? '1px solid rgba(59,130,246,0.5)' : '1px solid rgba(255,255,255,0.1)',
                        color: role === r ? '#ffffff' : 'rgba(232,234,240,0.5)',
                      }}
                    >
                      {r === 'student' ? '🎓 ' : '🏢 '}
                      {r.charAt(0).toUpperCase() + r.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Full name */}
              <InputField
                id="full_name"
                type="text"
                label="Full Name"
                icon={<User size={15} />}
                registration={register('full_name')}
                error={errors.full_name?.message}
              />

              {/* Email */}
              <InputField
                id="email"
                type="email"
                label="Email Address"
                icon={<Mail size={15} />}
                registration={register('email')}
                error={errors.email?.message}
              />

              {/* Student-only fields */}
              <AnimatePresence>
                {role === 'student' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 overflow-hidden"
                  >
                    <InputField
                      id="university"
                      type="text"
                      label="University (optional)"
                      icon={<Building2 size={15} />}
                      registration={register('university')}
                      error={errors.university?.message}
                    />

                    <div>
                      <div
                        className="relative flex items-center rounded-xl px-4 py-3"
                        style={{
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.1)',
                        }}
                      >
                        <GraduationCap
                          size={15}
                          className="mr-3 flex-shrink-0"
                          style={{ color: 'rgba(232,234,240,0.4)' }}
                        />
                        <select
                          {...register('graduation_year', { valueAsNumber: true })}
                          className="flex-1 bg-transparent text-sm outline-none"
                          style={{ color: 'rgba(232,234,240,0.8)' }}
                          defaultValue=""
                        >
                          <option value="" disabled style={{ background: '#0A0F1E' }}>
                            Graduation year (optional)
                          </option>
                          {GRAD_YEARS.map((y) => (
                            <option key={y} value={y} style={{ background: '#0A0F1E' }}>
                              {y}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Password */}
              <PasswordField
                id="password"
                label="Password"
                showPassword={showPassword}
                onToggle={() => setShowPassword((v) => !v)}
                registration={register('password')}
                error={errors.password?.message}
              />

              {/* Password strength bar */}
              {password && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-1.5"
                >
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className="h-1 flex-1 rounded-full transition-all duration-300"
                        style={{
                          background: i <= strength.score ? strength.color : 'rgba(255,255,255,0.1)',
                        }}
                      />
                    ))}
                  </div>
                  <p className="text-xs" style={{ color: strength.color }}>
                    {strength.label}
                  </p>
                </motion.div>
              )}

              {/* Confirm password */}
              <InputField
                id="password_confirm"
                type="password"
                label="Confirm Password"
                icon={<Lock size={15} />}
                registration={register('password_confirm')}
                error={errors.password_confirm?.message}
              />

              {/* Terms */}
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  {...register('terms')}
                  type="checkbox"
                  className="mt-0.5 rounded accent-blue-500"
                />
                <span className="text-xs" style={{ color: 'rgba(232,234,240,0.5)' }}>
                  I agree to the{' '}
                  <span className="underline" style={{ color: '#3B82F6' }}>
                    Terms of Service
                  </span>{' '}
                  and{' '}
                  <span className="underline" style={{ color: '#3B82F6' }}>
                    Privacy Policy
                  </span>
                </span>
              </label>
              {errors.terms && (
                <p className="text-xs" style={{ color: '#EF4444' }}>
                  {errors.terms.message}
                </p>
              )}

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={isLoading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-3 rounded-xl font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)' }}
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
                    Creating account…
                  </span>
                ) : (
                  'Create Account'
                )}
              </motion.button>
            </form>

            <p className="mt-5 text-center text-sm" style={{ color: 'rgba(232,234,240,0.5)' }}>
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-semibold"
                style={{ color: '#3B82F6' }}
                onMouseEnter={(e) => ((e.target as HTMLAnchorElement).style.color = '#8B5CF6')}
                onMouseLeave={(e) => ((e.target as HTMLAnchorElement).style.color = '#3B82F6')}
              >
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// ─── Reusable components ──────────────────────────────────────────────────────

interface InputFieldProps {
  id: string
  type: string
  label: string
  icon: React.ReactNode
  registration: ReturnType<ReturnType<typeof useForm>['register']>
  error?: string
}

function InputField({ id, type, label, icon, registration, error }: InputFieldProps) {
  return (
    <div>
      <div
        className="flex items-center rounded-xl px-4 py-3 transition-all"
        style={{
          background: 'rgba(255,255,255,0.05)',
          border: error ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div className="mr-3 flex-shrink-0" style={{ color: 'rgba(232,234,240,0.4)' }}>
          {icon}
        </div>
        <input
          id={id}
          type={type}
          {...registration}
          placeholder={label}
          className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
        />
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-xs pl-1"
          style={{ color: '#EF4444' }}
        >
          {error}
        </motion.p>
      )}
    </div>
  )
}

interface PasswordFieldProps {
  id: string
  label: string
  showPassword: boolean
  onToggle: () => void
  registration: ReturnType<ReturnType<typeof useForm>['register']>
  error?: string
}

function PasswordField({ id, label, showPassword, onToggle, registration, error }: PasswordFieldProps) {
  return (
    <div>
      <div
        className="flex items-center rounded-xl px-4 py-3 transition-all"
        style={{
          background: 'rgba(255,255,255,0.05)',
          border: error ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div className="mr-3 flex-shrink-0" style={{ color: 'rgba(232,234,240,0.4)' }}>
          <Lock size={15} />
        </div>
        <input
          id={id}
          type={showPassword ? 'text' : 'password'}
          {...registration}
          placeholder={label}
          className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
        />
        <button
          type="button"
          onClick={onToggle}
          className="ml-2"
          style={{ color: 'rgba(232,234,240,0.4)' }}
        >
          {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-xs pl-1"
          style={{ color: '#EF4444' }}
        >
          {error}
        </motion.p>
      )}
    </div>
  )
}
