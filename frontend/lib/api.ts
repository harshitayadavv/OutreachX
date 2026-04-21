/**
 * OutreachX API Client
 * Connects Next.js frontend to FastAPI backend
 * File: outreachx/frontend/lib/api.ts
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Lead {
  company_name: string
  website?: string
  country?: string
  industry?: string
  description?: string
  founded_year?: number
  batch?: string
  source?: string
  ceo_name?: string
  ceo_email?: string
  ceo_linkedin?: string
  ceo_email_source?: string
  ceo_email_confidence?: number
  cto_name?: string
  cto_email?: string
  cto_linkedin?: string
  hr_name?: string
  hr_email?: string
  hr_linkedin?: string
  tech_stack?: string[]
  personalization_hook?: string
  _email?: Email
}

export interface Email {
  lead_company: string
  to_name?: string
  to_email: string
  subject: string
  body: string
  personalization_score: number
  status: 'draft' | 'approved' | 'needs_review' | 'skipped_no_email' | 'sent' | 'opened' | 'replied'
}

export interface Campaign {
  id: string
  name: string
  status: string
  target_role: string
  total_leads: number
  emails_sent: number
  emails_opened: number
  emails_replied: number
  open_rate: number
  reply_rate: number
  created_at: string
}

export interface PipelineResult {
  leads: Lead[]
  emails: Email[]
  total: number
  approved: number
  skipped: number
  current_step: string
  entry_mode: string
  errors: string[]
  pipeline: {
    discovered: number
    enriched: number
    emails_approved: number
  }
  sender: {
    name: string
    value_prop: string
    background: string
  }
}

export interface CampaignStats {
  total: number
  sent: number
  opened: number
  clicked: number
  replied: number
  open_rate: number
  click_rate: number
  reply_rate: number
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `API error ${res.status}`)
  }
  return res.json()
}

// ── Health ─────────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5000) })
    return res.ok
  } catch {
    return false
  }
}

// ── Run AI pipeline (main endpoint) ───────────────────────────────────────────

export async function runPipeline(params: {
  query?: string
  leadsFile?: File
  resumeFile?: File
  targetRole?: string
  senderName?: string
  senderValueProp?: string
}): Promise<PipelineResult> {
  const form = new FormData()

  if (params.query)          form.append('query', params.query)
  if (params.leadsFile)      form.append('leads_file', params.leadsFile)
  if (params.resumeFile)     form.append('resume_file', params.resumeFile)
  if (params.targetRole)     form.append('target_role', params.targetRole)
  if (params.senderName)     form.append('sender_name', params.senderName)
  if (params.senderValueProp) form.append('sender_value_prop', params.senderValueProp)

  return fetchAPI<PipelineResult>('/agents/run', { method: 'POST', body: form })
}

// ── Campaigns ─────────────────────────────────────────────────────────────────

export async function getCampaigns(): Promise<Campaign[]> {
  return fetchAPI<Campaign[]>('/campaigns')
}

export async function getCampaign(id: string) {
  return fetchAPI<{ campaign: Campaign; leads: Lead[]; emails: Email[] }>(`/campaigns/${id}`)
}

export async function createCampaign(params: {
  name: string
  query?: string
  leadsFile?: File
  targetRole?: string
  senderName?: string
  senderEmail?: string
  senderValueProp?: string
  resumeFile?: File
}) {
  const form = new FormData()
  form.append('name', params.name)
  if (params.query)          form.append('query', params.query)
  if (params.leadsFile)      form.append('leads_file', params.leadsFile)
  if (params.targetRole)     form.append('target_role', params.targetRole || 'ceo')
  if (params.senderName)     form.append('sender_name', params.senderName)
  if (params.senderEmail)    form.append('sender_email', params.senderEmail)
  if (params.senderValueProp) form.append('sender_value_prop', params.senderValueProp)
  if (params.resumeFile)     form.append('resume_file', params.resumeFile)

  return fetchAPI('/campaigns', { method: 'POST', body: form })
}

export async function getCampaignStats(id: string): Promise<CampaignStats> {
  return fetchAPI<CampaignStats>(`/campaigns/${id}/stats`)
}

export async function sendCampaignEmails(id: string, dryRun = false) {
  const form = new FormData()
  form.append('dry_run', String(dryRun))
  return fetchAPI(`/campaigns/${id}/send`, { method: 'POST', body: form })
}

export async function updateEmail(
  campaignId: string,
  emailId: string,
  action: 'approve' | 'skip' | 'edit',
  subject?: string,
  body?: string
) {
  const form = new FormData()
  form.append('action', action)
  if (subject) form.append('subject', subject)
  if (body)    form.append('body', body)
  return fetchAPI(`/campaigns/${campaignId}/email/${emailId}`, { method: 'PATCH', body: form })
}

// ── Email stats ───────────────────────────────────────────────────────────────

export async function getEmailStats(campaignId?: string): Promise<CampaignStats> {
  const qs = campaignId ? `?campaign_id=${campaignId}` : ''
  return fetchAPI<CampaignStats>(`/emails/stats${qs}`)
}

// ── Resume parser ─────────────────────────────────────────────────────────────

export async function parseResume(file: File) {
  const form = new FormData()
  form.append('file', file)
  return fetchAPI<{
    name: string
    current_role: string
    company: string
    skills: string[]
    background_summary: string
    value_prop: string
  }>('/resume/parse', { method: 'POST', body: form })
}

// ── Follow-ups ────────────────────────────────────────────────────────────────

export async function getFollowupQueue() {
  return fetchAPI('/followups/queue')
}