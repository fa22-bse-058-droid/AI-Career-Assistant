import { motion } from 'framer-motion'

interface ScoreGaugeProps {
  score: number
  grade: string
  animated?: boolean
}

const GRADE_COLORS: Record<string, string> = {
  poor: '#EF4444',
  average: '#F59E0B',
  good: '#3B82F6',
  excellent: '#10B981',
}

/**
 * Animated SVG circular progress gauge for CV scores (0-100).
 * Color changes based on grade: poor → average → good → excellent.
 */
export default function ScoreGauge({ score, grade, animated = true }: ScoreGaugeProps) {
  const color = GRADE_COLORS[grade] ?? '#3B82F6'
  const radius = 45
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <svg width="120" height="120" className="-rotate-90">
        {/* Track */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="8"
        />
        {/* Progress arc */}
        <motion.circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: animated ? dashOffset : dashOffset }}
          transition={animated ? { duration: 1.5, ease: 'easeOut' } : { duration: 0 }}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>

      {/* Score label (centred over SVG) */}
      <div className="-mt-[70px] text-center">
        <motion.p
          className="text-3xl font-bold text-white"
          initial={animated ? { opacity: 0 } : false}
          animate={{ opacity: 1 }}
          transition={{ delay: animated ? 0.5 : 0 }}
        >
          {score.toFixed(0)}
        </motion.p>
        <p className="text-xs text-slate-400 capitalize mt-1">{grade}</p>
      </div>
    </div>
  )
}
