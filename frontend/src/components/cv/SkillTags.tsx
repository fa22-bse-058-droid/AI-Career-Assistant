import { motion } from 'framer-motion'

interface SkillTagsProps {
  skillsByCategory: Record<string, string[]>
}

const CATEGORY_COLORS: Record<string, string> = {
  programming_languages: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  frameworks: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
  web_frontend: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
  web_backend: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  databases: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  cloud: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  cloud_devops: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  data_science: 'bg-green-500/10 text-green-300 border-green-500/20',
  data_science_ml: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  tools: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
  mobile: 'bg-pink-500/10 text-pink-300 border-pink-500/20',
  security: 'bg-red-500/10 text-red-300 border-red-500/20',
  testing: 'bg-teal-500/10 text-teal-300 border-teal-500/20',
  design: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
  soft_skills: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
}

function formatCategoryLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Displays detected skills grouped by category, each as a coloured pill/tag.
 */
export default function SkillTags({ skillsByCategory }: SkillTagsProps) {
  const entries = Object.entries(skillsByCategory).filter(([, skills]) => skills.length > 0)

  if (entries.length === 0) {
    return <p className="text-slate-500 text-sm">No skills detected.</p>
  }

  return (
    <div className="space-y-4">
      {entries.map(([category, skills]) => {
        const colorClass =
          CATEGORY_COLORS[category] ?? 'bg-slate-500/10 text-slate-300 border-slate-500/20'

        return (
          <div key={category}>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {formatCategoryLabel(category)}
            </p>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <motion.span
                  key={skill}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${colorClass}`}
                >
                  {skill}
                </motion.span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
