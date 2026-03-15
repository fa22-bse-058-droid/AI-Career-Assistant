import { motion } from 'framer-motion'

interface SkillGap {
  missing_required?: string[]
  missing_preferred?: string[]
  matched_required?: number
  total_required?: number
  match_percentage?: number
}

interface SkillGapChartProps {
  /** Map of role name → gap data returned by the backend */
  skillGaps: Record<string, SkillGap>
}

/**
 * Visualises skill gaps for every role in two columns:
 *  - Missing Required  (red)
 *  - Missing Preferred (amber)
 * and shows an overall match percentage bar.
 */
export default function SkillGapChart({ skillGaps }: SkillGapChartProps) {
  const roles = Object.entries(skillGaps)

  if (roles.length === 0) {
    return (
      <p className="text-slate-500 text-sm">
        No skill gap data available. Upload a CV first.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {roles.map(([role, gaps]) => {
        const missingRequired = gaps.missing_required ?? []
        const missingPreferred = gaps.missing_preferred ?? []

        // Use accurate match percentage provided by the backend (matched / total_required).
        const matchPct = gaps.match_percentage ?? 0

        return (
          <div
            key={role}
            className="p-4 rounded-lg bg-white/3 border border-white/5 space-y-3"
          >
            {/* Role header + match bar */}
            <div className="flex items-center justify-between">
              <p className="text-white font-medium">{role}</p>
              <span className="text-xs text-slate-400">{matchPct}% match</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-accent-blue to-accent-purple rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${matchPct}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>

            {/* Missing required */}
            {missingRequired.length > 0 && (
              <div>
                <p className="text-xs text-red-400 mb-1.5">Missing Required</p>
                <div className="flex flex-wrap gap-1.5">
                  {missingRequired.map((s) => (
                    <span
                      key={s}
                      className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing preferred */}
            {missingPreferred.length > 0 && (
              <div>
                <p className="text-xs text-amber-400 mb-1.5">Missing Preferred</p>
                <div className="flex flex-wrap gap-1.5">
                  {missingPreferred.map((s) => (
                    <span
                      key={s}
                      className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
