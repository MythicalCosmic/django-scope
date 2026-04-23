import type { EntryListResponse, EntryDetailResponse, StatusResponse, BatchResponse, StatsResponse, HealthResponse } from './types'

const config = window.__TELESCOPE_CONFIG__ || { basePath: '/telescope/' }
const BASE = `/${config.basePath.replace(/^\/|\/$/g, '')}/api`

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

export const api = {
  entries(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<EntryListResponse>(`/entries${qs}`)
  },

  entriesByType(typeSlug: string, params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<EntryListResponse>(`/entries/${typeSlug}${qs}`)
  },

  entryDetail(uuid: string) {
    return request<EntryDetailResponse>(`/entry/${uuid}`)
  },

  batch(batchId: string) {
    return request<BatchResponse>(`/batch/${batchId}`)
  },

  status() {
    return request<StatusResponse>('/status')
  },

  stats(range?: string) {
    const qs = range ? `?range=${range}` : ''
    return request<StatsResponse>(`/stats${qs}`)
  },

  health() {
    return request<HealthResponse>('/health')
  },

  clear(typeSlug?: string) {
    const qs = typeSlug ? `?type=${typeSlug}` : ''
    return request<{ deleted: number }>(`/clear${qs}`, { method: 'DELETE' })
  },

  toggleRecording(recording?: boolean) {
    return request<{ recording: boolean }>('/toggle-recording', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recording !== undefined ? { recording } : {}),
    })
  },

  deleteEntry(uuid: string) {
    return request<{ message: string }>(`/entry/${uuid}/delete`, { method: 'DELETE' })
  },
}
