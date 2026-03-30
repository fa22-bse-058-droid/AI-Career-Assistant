import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Upload, XCircle, RefreshCw, AlertTriangle, CheckCircle, TrendingUp, User, BarChart2 } from 'lucide-react'
import { uploadCV, getCVStatus, getCompanyMatch, CompanyMatch } from '@/api/cvApi'

function ScoreGauge({ score, grade }: { score: number; grade: string }) {
  const gradeColors: Record<string, string> = {
    Poor: '#EF4444',
    Average: '#F59E0B',
    Good: '#3B82F6',
    Excellent: '#10B981',
  }
  const color = gradeColors[grade] ?? gradeColors[grade.charAt(0).toUpperCase() + grade.slice(1).toLowerCase()] ?? '#3B82F6'
  const circumference = 2 * Math.PI * 45
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="relative flex items-center justify-center" style={{ width: 120, height: 120 }}>
      <svg width="120" height="120" className="-rotate-90 absolute inset-0">
        <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
        <motion.circle
          cx="60"
          cy="60"
          r="45"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.p
          className="text-3xl font-bold text-white leading-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {score.toFixed(0)}
        </motion.p>
        <p className="text-xs text-slate-400 capitalize mt-1.5">{grade}</p>
      </div>
    </div>
  )
}

function LaserScanAnimation() {
  return (
    <div className="relative w-48 h-64 mx-auto my-8">
      <div className="absolute inset-0 border-2 border-accent-blue/30 rounded-lg bg-white/2">
        {[20, 35, 50, 65, 80, 95, 110, 125, 140, 155].map((y) => (
          <div
            key={y}
            className="absolute left-4 right-4 h-px bg-white/5"
            style={{ top: y }}
          />
        ))}
      </div>
      <motion.div
        className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-accent-blue to-transparent"
        style={{ boxShadow: '0 0 8px rgba(59, 130, 246, 0.8)' }}
        animate={{ top: ['5%', '95%', '5%'] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      />
      <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-accent-blue" />
      <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-accent-blue" />
      <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-accent-blue" />
      <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-accent-blue" />
    </div>
  )
}

function SkillTag({ skill, category }: { skill: string; category: string }) {
  const categoryColors: Record<string, string> = {
    programming_languages: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
    web_frontend: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
    web_backend: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
    databases: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    cloud_devops: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
    data_science_ml: 'bg-green-500/10 text-green-300 border-green-500/20',
  }
  const colorClass = categoryColors[category] || 'bg-slate-500/10 text-slate-300 border-slate-500/20'

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${colorClass}`}
    >
      {skill}
    </motion.span>
  )
}

function ScoreCard({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div className="p-4 rounded-xl bg-white/3 border border-white/5 space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-sm font-semibold text-white">{score.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

function DeepAnalysisSection({ deep }: { deep: any }) {
  const scoreCards = [
    { label: 'ATS Compatibility', score: deep.ats_score ?? 0, color: '#3B82F6' },
    { label: 'Keyword Coverage', score: deep.keyword_score ?? 0, color: '#8B5CF6' },
    { label: 'Technical Depth', score: deep.technical_depth_score ?? 0, color: '#06B6D4' },
    { label: 'Impact Language', score: deep.impact_score ?? 0, color: '#10B981' },
    { label: 'Readability', score: deep.readability_score ?? 0, color: '#F59E0B' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="space-y-6"
    >
      {/* ATS Score Gauge + 5 score cards */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
          <BarChart2 size={18} className="text-accent-blue" />
          Deep ATS Analysis
        </h2>
        <div className="flex flex-col md:flex-row items-center gap-8">
          <div className="flex flex-col items-center gap-2">
            <p className="text-xs text-slate-400 uppercase tracking-wider">Overall</p>
            <ScoreGauge score={deep.overall_score ?? 0} grade={deep.grade ?? 'poor'} />
          </div>
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {scoreCards.map((card) => (
              <ScoreCard key={card.label} {...card} />
            ))}
          </div>
        </div>
      </div>

      {/* ATS Issues */}
      {(deep.ats_issues?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-400" />
            ATS Issues
          </h2>
          <ul className="space-y-2">
            {(deep.ats_issues as string[]).map((issue, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                {issue}
              </motion.li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Keywords chips */}
      {(deep.missing_keywords?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Missing Keywords</h2>
          <div className="flex flex-wrap gap-2">
            {(deep.missing_keywords as string[]).map((kw, i) => (
              <motion.span
                key={kw}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.04 }}
                className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-300 border border-red-500/20"
              >
                {kw}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Skill Gaps list */}
      {(deep.skill_gaps?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Skill Gaps</h2>
          <div className="flex flex-wrap gap-2">
            {(deep.skill_gaps as string[]).map((gap, i) => (
              <motion.span
                key={gap}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.04 }}
                className="px-2.5 py-1 rounded-full text-xs font-medium bg-orange-500/10 text-orange-300 border border-orange-500/20"
              >
                {gap}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Strong Points */}
      {(deep.strong_points?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle size={18} className="text-green-400" />
            Strong Points
          </h2>
          <ul className="space-y-2">
            {(deep.strong_points as string[]).map((point, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                {point}
              </motion.li>
            ))}
          </ul>
        </div>
      )}

      {/* Improvement Action Plan */}
      {(deep.improvements?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-accent-blue" />
            Improvement Action Plan
          </h2>
          <ol className="space-y-3">
            {(deep.improvements as string[]).map((item, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="flex items-start gap-3 text-sm text-slate-300"
              >
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-accent-blue/20 border border-accent-blue/30 text-accent-blue text-xs font-bold flex items-center justify-center">
                  {i + 1}
                </span>
                {item}
              </motion.li>
            ))}
          </ol>
        </div>
      )}

      {/* Project Feedback */}
      {(deep.project_feedback?.length ?? 0) > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Project Feedback</h2>
          <ul className="space-y-2">
            {(deep.project_feedback as string[]).map((fb, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0" />
                {fb}
              </motion.li>
            ))}
          </ul>
        </div>
      )}

      {/* Recruiter Verdict card */}
      {deep.recruiter_verdict && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <User size={18} className="text-accent-purple" />
            Recruiter Verdict
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">{deep.recruiter_verdict}</p>
        </div>
      )}

      {/* Industry Benchmark */}
      {deep.benchmark && (
        <div className="glass-card p-6 border border-accent-blue/20">
          <h2 className="text-lg font-semibold text-white mb-3">Industry Benchmark</h2>
          <p className="text-sm text-slate-300 leading-relaxed">{deep.benchmark}</p>
        </div>
      )}
    </motion.div>
  )
}

const STRONG_MATCH_THRESHOLD = 70
const MODERATE_MATCH_THRESHOLD = 40
const MATCH_COLOR_GREEN = '#10B981'
const MATCH_COLOR_YELLOW = '#F59E0B'
const MATCH_COLOR_RED = '#EF4444'

function CompanyMatchSection({ companies }: { companies: CompanyMatch[] }) {
  const barColor = (pct: number) => {
    if (pct >= STRONG_MATCH_THRESHOLD) return MATCH_COLOR_GREEN
    if (pct >= MODERATE_MATCH_THRESHOLD) return MATCH_COLOR_YELLOW
    return MATCH_COLOR_RED
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
        <TrendingUp size={18} className="text-accent-blue" />
        Company Match Analysis
      </h2>
      <div className="space-y-4">
        {companies.map((company, idx) => (
          <motion.div
            key={company.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.08 }}
            className="p-4 rounded-xl bg-white/3 border border-white/5 space-y-3"
          >
            {/* Company header */}
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                style={{ backgroundColor: `${company.color}30`, border: `1px solid ${company.color}50` }}
              >
                <span style={{ color: company.color }}>{company.logo_initial}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium text-sm">{company.name}</p>
                <p className="text-xs text-slate-400 truncate">{company.verdict}</p>
              </div>
              <span
                className="text-lg font-bold flex-shrink-0"
                style={{ color: barColor(company.match_percentage) }}
              >
                {company.match_percentage}%
              </span>
            </div>

            {/* Progress bar */}
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: barColor(company.match_percentage) }}
                initial={{ width: 0 }}
                animate={{ width: `${company.match_percentage}%` }}
                transition={{ duration: 1, ease: 'easeOut', delay: idx * 0.08 + 0.2 }}
              />
            </div>

            {/* Missing skills */}
            {company.missing_skills.length > 0 && (
              <div>
                <p className="text-xs text-red-400 mb-1.5">Missing Skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {company.missing_skills.map((skill) => (
                    <span
                      key={skill}
                      className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Improvements */}
            {company.improvements.length > 0 && (
              <div>
                <p className="text-xs text-accent-blue mb-1.5">To reach 90%+</p>
                <ul className="space-y-1">
                  {company.improvements.map((tip, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                      <span className="mt-1 w-1 h-1 rounded-full bg-accent-blue flex-shrink-0" />
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

/** Returns true only when the backend has produced a complete deep-analysis result. */
function isValidDeepAnalysis(value: Record<string, unknown> | null | undefined): boolean {
  return !!value && typeof value === 'object' && 'overall_score' in value
}

export default function CVAnalyzerPage() {
  const [uploadedCvId, setUploadedCvId] = useState<string | null>(null)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadCV(file),
    onSuccess: (data) => {
      setUploadedCvId(data.id)
    },
  })

  const { data: cvStatus } = useQuery({
    queryKey: ['cv-status', uploadedCvId],
    queryFn: () => getCVStatus(uploadedCvId!),
    enabled: !!uploadedCvId,
    refetchInterval: (query) => {
      const d = query.state.data as any
      return d?.status === 'processing' || d?.status === 'pending' ? 2000 : false
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      uploadMutation.mutate(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 5 * 1024 * 1024,
    maxFiles: 1,
  })

  const analysis = cvStatus?.analysis
  const isProcessing = cvStatus?.status === 'processing' || cvStatus?.status === 'pending'
  const deepAnalysis = isValidDeepAnalysis(analysis?.deep_analysis) ? analysis!.deep_analysis : null

  const { data: companyMatchData } = useQuery({
    queryKey: ['cv-company-match', uploadedCvId],
    queryFn: () => getCompanyMatch(uploadedCvId!),
    enabled: !!uploadedCvId && cvStatus?.status === 'completed',
  })

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-white mb-2">CV Analyzer</h1>
        <p className="text-slate-400">Upload your CV and get an AI-powered analysis with skill gap detection</p>
      </motion.div>

      {/* Upload Area */}
      {!uploadedCvId && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          {...(getRootProps() as any)}
          className={`
            relative border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all
            ${isDragActive
              ? 'border-accent-blue bg-accent-blue/5 shadow-glow'
              : 'border-white/10 hover:border-accent-blue/40 hover:bg-white/2'}
          `}
        >
          <input {...getInputProps()} />
          <motion.div
            animate={{ y: isDragActive ? -5 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="w-16 h-16 rounded-2xl bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center mx-auto mb-4">
              <Upload size={28} className="text-accent-blue" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {isDragActive ? 'Drop your CV here' : 'Upload your CV'}
            </h3>
            <p className="text-slate-400 text-sm">PDF or DOCX, max 5 MB</p>
          </motion.div>

          {isDragActive && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 rounded-2xl bg-accent-blue/5 border-2 border-accent-blue"
            />
          )}
        </motion.div>
      )}

      {/* Upload Error */}
      {uploadMutation.isError && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
          <XCircle size={18} className="text-red-400" />
          <p className="text-red-400 text-sm">
            {(uploadMutation.error as any)?.response?.data?.detail ?? 'Upload failed. Please try again.'}
          </p>
          <button
            onClick={() => { setUploadedCvId(null); uploadMutation.reset() }}
            className="ml-auto text-slate-400 hover:text-white"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      )}

      {/* Processing Animation */}
      <AnimatePresence>
        {(isProcessing || uploadMutation.isPending) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="glass-card p-8 text-center"
          >
            <LaserScanAnimation />
            <motion.p
              className="text-white font-semibold mt-4"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              {uploadMutation.isPending ? 'Uploading your CV...' : 'Analyzing your CV with AI...'}
            </motion.p>
            <p className="text-slate-400 text-sm mt-2">Extracting skills, scoring, detecting gaps</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* CV Analysis Failed */}
      {cvStatus?.status === 'failed' && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
          <XCircle size={18} className="text-red-400" />
          <p className="text-red-400 text-sm">
            {cvStatus.error_message || 'CV analysis failed. Please try uploading again.'}
          </p>
          <button
            onClick={() => { setUploadedCvId(null); uploadMutation.reset() }}
            className="ml-auto text-slate-400 hover:text-white"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {analysis && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Score Overview */}
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold text-white mb-6">Overall Score</h2>
              <div className="flex flex-col md:flex-row items-center gap-8">
                <ScoreGauge score={analysis.overall_score} grade={analysis.grade} />
                <div className="flex-1 grid grid-cols-2 gap-4">
                  {[
                    { label: 'Keyword Relevance', value: analysis.keyword_relevance_score, weight: '30%' },
                    { label: 'Completeness', value: analysis.completeness_score, weight: '25%' },
                    { label: 'Skill Density', value: analysis.skill_density_score, weight: '25%' },
                    { label: 'Formatting', value: analysis.formatting_score, weight: '20%' },
                  ].map((item) => (
                    <div key={item.label} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400">{item.label}</span>
                        <span className="text-slate-500">{item.weight}</span>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-accent-blue to-accent-purple rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${item.value}%` }}
                          transition={{ duration: 1, ease: 'easeOut' }}
                        />
                      </div>
                      <span className="text-white text-xs font-medium">{item.value.toFixed(0)}/100</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Skills by Category */}
            {Object.keys(analysis.skills_by_category).length > 0 && (
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Detected Skills</h2>
                <div className="space-y-4">
                  {Object.entries(analysis.skills_by_category).map(([category, skills]) => (
                    <div key={category}>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                        {category.replace(/_/g, ' ')}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(skills as string[]).map((skill) => (
                          <SkillTag key={skill} skill={skill} category={category} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skill Gaps (existing rule-based) */}
            {Object.keys(analysis.skill_gaps).length > 0 && (
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Skill Gap Analysis</h2>
                <div className="space-y-4">
                  {Object.entries(analysis.skill_gaps).map(([role, gaps]: [string, any]) => (
                    <div key={role} className="p-4 rounded-lg bg-white/3 border border-white/5">
                      <p className="text-white font-medium mb-3">{role}</p>
                      {gaps.missing_required?.length > 0 && (
                        <div className="mb-2">
                          <p className="text-xs text-red-400 mb-1.5">Missing Required</p>
                          <div className="flex flex-wrap gap-1.5">
                            {gaps.missing_required.map((s: string) => (
                              <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {gaps.missing_preferred?.length > 0 && (
                        <div>
                          <p className="text-xs text-amber-400 mb-1.5">Missing Preferred</p>
                          <div className="flex flex-wrap gap-1.5">
                            {gaps.missing_preferred.map((s: string) => (
                              <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deep ATS Analysis Section */}
            {deepAnalysis && <DeepAnalysisSection deep={deepAnalysis} />}

            {/* Company Match Analysis */}
            {companyMatchData && companyMatchData.companies.length > 0 && (
              <CompanyMatchSection companies={companyMatchData.companies} />
            )}

            {/* Upload another */}
            <button
              onClick={() => { setUploadedCvId(null); uploadMutation.reset() }}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw size={14} />
              Upload a new CV
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
