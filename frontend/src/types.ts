export interface TelescopeEntry {
  uuid: string
  batch_id: string | null
  type: number
  type_label: string
  type_slug: string
  summary: string
  content: Record<string, any>
  tags: string[]
  created_at: string
}

export interface EntryListResponse {
  entries: TelescopeEntry[]
  has_more: boolean
  type?: {
    value: number
    label: string
    slug: string
  }
}

export interface EntryDetailResponse {
  entry: TelescopeEntry
}

export interface StatusResponse {
  enabled: boolean
  recording: boolean
  total_entries: number
  types: Record<string, { label: string; count: number }>
}

export interface BatchResponse {
  entries: TelescopeEntry[]
  batch_id: string
}

export interface StatsResponse {
  range: string
  requests: {
    total: number
    percentiles: { p50: number; p75: number; p95: number; p99: number }
    apdex: number
    apdex_threshold: number
    error_count: number
    error_rate: number
    throughput_per_minute: number
  }
  queries: {
    total: number
    slow_patterns: { family_hash: string; count: number; avg_duration: number; sample_sql: string | null }[]
    n_plus_one_patterns: number
  }
  cache: {
    total: number
    hits: number
    hit_rate: number
  }
}

export interface HealthResponse {
  summary: {
    healthy: number
    failed: number
    disabled: number
    total: number
  }
  watchers: Record<string, {
    status: 'healthy' | 'failed' | 'disabled' | 'unknown'
    error?: string | null
    dependency?: string | null
  }>
}

export type EntryTypeSlug =
  | 'request' | 'query' | 'exception' | 'model' | 'log'
  | 'cache' | 'redis' | 'mail' | 'view' | 'event'
  | 'command' | 'dump' | 'client-request' | 'gate'
  | 'notification' | 'schedule' | 'batch'
  | 'transaction' | 'storage'

export interface NavItem {
  slug: EntryTypeSlug
  label: string
  icon: string
}
