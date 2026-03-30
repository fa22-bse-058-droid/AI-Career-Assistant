/**
 * CV Analyzer API helpers.
 * All paths are relative to the axios baseURL ('/api') — do NOT include '/api/' prefix.
 */
import { useEffect, useRef, useState } from 'react'
import api from './axios'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CVUploadResponse {
  id: string
  original_filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  task_id: string
  uploaded_at: string
  processed_at: string | null
  error_message: string
  analysis: CVAnalysis | null
}

export interface CVAnalysis {
  id: number
  overall_score: number
  grade: 'poor' | 'average' | 'good' | 'excellent'
  keyword_relevance_score: number
  completeness_score: number
  skill_density_score: number
  formatting_score: number
  extracted_skills: string[]
  skills_by_category: Record<string, string[]>
  skill_gaps: Record<string, { missing_required?: string[]; missing_preferred?: string[] }>
  education: unknown[]
  experience: unknown[]
  contact_info: Record<string, string>
  deep_analysis: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CompanyMatch {
  name: string
  match_percentage: number
  missing_skills: string[]
  improvements: string[]
  verdict: string
  color: string
  logo_initial: string
}

export interface CompanyMatchResponse {
  companies: CompanyMatch[]
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Upload a CV file, reporting progress via onProgress callback.
 * Returns the CVUploadResponse (status='pending').
 */
export async function uploadCV(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<CVUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post<CVUploadResponse>('/cv/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded * 100) / event.total))
      }
    },
  })
  return data
}

/**
 * Poll the status of a previously uploaded CV.
 */
export async function getCVStatus(cvId: string): Promise<CVUploadResponse> {
  const { data } = await api.get<CVUploadResponse>(`/cv/${cvId}/status/`)
  return data
}

/**
 * Retrieve full analysis results for a completed CV.
 */
export async function getCVResults(cvId: string): Promise<CVUploadResponse> {
  const { data } = await api.get<CVUploadResponse>(`/cv/${cvId}/analysis/`)
  return data
}

/**
 * List all CVs uploaded by the current user (paginated, newest first).
 */
export async function getCVHistory(): Promise<CVUploadResponse[]> {
  const { data } = await api.get<CVUploadResponse[]>('/cv/list/')
  return data
}

/**
 * Retrieve company acceptance-chance analysis for a completed CV.
 */
export async function getCompanyMatch(cvId: string): Promise<CompanyMatchResponse> {
  const { data } = await api.get<CompanyMatchResponse>(`/cv/${cvId}/company-match/`)
  return data
}

// ---------------------------------------------------------------------------
// Custom hook: poll CV status every 2 s until completed/failed
// ---------------------------------------------------------------------------

const POLLING_STATUSES = new Set<CVUploadResponse['status']>(['pending', 'processing'])

interface PollingState {
  data: CVUploadResponse | null
  isPolling: boolean
  error: string | null
}

/**
 * useCVPolling — polls getCVStatus every 2 s while status is pending/processing.
 * Stops automatically when status becomes 'completed' or 'failed'.
 */
export function useCVPolling(cvId: string | null): PollingState {
  const [state, setState] = useState<PollingState>({
    data: null,
    isPolling: false,
    error: null,
  })
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!cvId) return

    setState((prev) => ({ ...prev, isPolling: true, error: null }))

    const poll = async () => {
      try {
        const result = await getCVStatus(cvId)
        setState({ data: result, isPolling: POLLING_STATUSES.has(result.status), error: null })

        if (!POLLING_STATUSES.has(result.status)) {
          if (intervalRef.current) clearInterval(intervalRef.current)
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Polling error'
        setState({ data: null, isPolling: false, error: msg })
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [cvId])

  return state
}
