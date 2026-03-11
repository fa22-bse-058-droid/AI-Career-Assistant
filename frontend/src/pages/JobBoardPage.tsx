import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Briefcase, MapPin, Building2, Clock, ExternalLink, Bookmark, BookmarkCheck, Star } from 'lucide-react'
import api from '@/api/axios'

function MatchRing({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 80 ? '#10B981' : pct >= 60 ? '#3B82F6' : '#F59E0B'
  const c = 2 * Math.PI * 18
  return (
    <div className="relative w-12 h-12">
      <svg width="48" height="48" className="-rotate-90">
        <circle cx="24" cy="24" r="18" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
        <circle
          cx="24" cy="24" r="18" fill="none"
          stroke={color} strokeWidth="3" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c - (pct / 100) * c}
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-bold text-white">{pct}%</span>
      </div>
    </div>
  )
}

export default function JobBoardPage() {
  const [filters, setFilters] = useState({ job_type: '', experience_level: '', search: '' })
  const [viewMode, setViewMode] = useState<'all' | 'matches'>('all')

  const { data: jobs } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () =>
      api.get('/jobs/', {
        params: { ...filters, search: filters.search || undefined },
      }).then((r) => r.data),
  })

  const { data: matches } = useQuery({
    queryKey: ['job-matches'],
    queryFn: () => api.get('/jobs/matches/').then((r) => r.data),
  })

  const displayData = viewMode === 'matches'
    ? (matches?.results || [])
    : (jobs?.results || [])

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white mb-2">Job Board</h1>
        <p className="text-slate-400">Discover opportunities matched to your skills</p>
      </motion.div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex rounded-lg overflow-hidden border border-white/10">
          {['all', 'matches'].map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode as any)}
              className={`px-4 py-2 text-sm font-medium capitalize transition-all ${
                viewMode === mode
                  ? 'bg-accent-blue text-white'
                  : 'bg-white/5 text-slate-400 hover:text-white'
              }`}
            >
              {mode === 'matches' ? '⚡ Matched' : 'All Jobs'}
            </button>
          ))}
        </div>

        <input
          value={filters.search}
          onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          placeholder="Search jobs..."
          className="flex-1 min-w-48 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-accent-blue/50"
        />

        <select
          value={filters.job_type}
          onChange={(e) => setFilters((f) => ({ ...f, job_type: e.target.value }))}
          className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-slate-300 focus:outline-none"
        >
          <option value="">All Types</option>
          <option value="full_time">Full Time</option>
          <option value="part_time">Part Time</option>
          <option value="internship">Internship</option>
          <option value="remote">Remote</option>
        </select>
      </div>

      {/* Job Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnimatePresence>
          {displayData.map((item: any, i: number) => {
            const job = viewMode === 'matches' ? item.job : item
            const matchScore = viewMode === 'matches' ? item.match_score : null

            return (
              <motion.div
                key={job?.id || i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.05 }}
                whileHover={{ y: -2 }}
                className="glass-card p-5 group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-white font-semibold truncate group-hover:text-accent-blue transition-colors">
                      {job?.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Building2 size={13} className="text-slate-500" />
                      <span className="text-slate-400 text-sm">{job?.company}</span>
                    </div>
                  </div>
                  {matchScore !== null && <MatchRing score={matchScore} />}
                </div>

                <div className="flex flex-wrap gap-2 mb-3">
                  {job?.location && (
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <MapPin size={11} /> {job.location}
                    </span>
                  )}
                  <span className="text-xs px-2 py-0.5 rounded-full bg-accent-blue/10 text-accent-blue border border-accent-blue/20 capitalize">
                    {job?.job_type?.replace('_', ' ')}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-slate-400 border border-white/10 capitalize">
                    {job?.source}
                  </span>
                </div>

                <p className="text-slate-400 text-sm line-clamp-2 mb-4">
                  {job?.description?.slice(0, 150) || 'No description available.'}
                </p>

                <div className="flex items-center gap-2">
                  <a
                    href={job?.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-accent-blue hover:text-accent-purple transition-colors"
                  >
                    <ExternalLink size={13} /> View Job
                  </a>
                  <div className="flex items-center gap-1 ml-auto text-xs text-slate-500">
                    <Clock size={11} />
                    {job?.scraped_at ? new Date(job.scraped_at).toLocaleDateString() : ''}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      {displayData.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <Briefcase size={48} className="mx-auto mb-4 opacity-30" />
          <p>No jobs found. Try uploading your CV to get matches!</p>
        </div>
      )}
    </div>
  )
}
