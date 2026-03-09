import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react'
import api from '@/api/axios'

function ScoreGauge({ score, grade }: { score: number; grade: string }) {
  const gradeColors: Record<string, string> = {
    poor: '#EF4444',
    average: '#F59E0B',
    good: '#3B82F6',
    excellent: '#10B981',
  }
  const color = gradeColors[grade] || '#3B82F6'
  const circumference = 2 * Math.PI * 45
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <svg width="120" height="120" className="-rotate-90">
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
      <div className="-mt-[70px] text-center">
        <motion.p
          className="text-3xl font-bold text-white"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {score.toFixed(0)}
        </motion.p>
        <p className="text-xs text-slate-400 capitalize mt-1">{grade}</p>
      </div>
    </div>
  )
}

function LaserScanAnimation() {
  return (
    <div className="relative w-48 h-64 mx-auto my-8">
      {/* Document outline */}
      <div className="absolute inset-0 border-2 border-accent-blue/30 rounded-lg bg-white/2">
        {/* Page lines */}
        {[20, 35, 50, 65, 80, 95, 110, 125, 140, 155].map((y) => (
          <div
            key={y}
            className="absolute left-4 right-4 h-px bg-white/5"
            style={{ top: y }}
          />
        ))}
      </div>
      {/* Laser beam */}
      <motion.div
        className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-accent-blue to-transparent"
        style={{ boxShadow: '0 0 8px rgba(59, 130, 246, 0.8)' }}
        animate={{ top: ['5%', '95%', '5%'] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      />
      {/* Corner brackets */}
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

export default function CVAnalyzerPage() {
  const [uploadedCvId, setUploadedCvId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/cv/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return res.data
    },
    onSuccess: (data) => {
      setUploadedCvId(data.id)
    },
  })

  const { data: cvStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['cv-status', uploadedCvId],
    queryFn: () => api.get(`/cv/${uploadedCvId}/status/`).then((r) => r.data),
    enabled: !!uploadedCvId,
    refetchInterval: (data) =>
      data?.status === 'processing' || data?.status === 'pending' ? 2000 : false,
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
          <p className="text-red-400 text-sm">Upload failed. Please try again.</p>
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
        {isProcessing && (
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
              Analyzing your CV with AI...
            </motion.p>
            <p className="text-slate-400 text-sm mt-2">Extracting skills, scoring, detecting gaps</p>
          </motion.div>
        )}
      </AnimatePresence>

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

            {/* Skill Gaps */}
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
