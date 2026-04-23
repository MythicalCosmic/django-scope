<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue'
import { api } from '../api'
import { getWebSocket } from '../websocket'
import type { StatusResponse, StatsResponse, TelescopeEntry } from '../types'
import EntryTable from '../components/EntryTable.vue'

const status = ref<StatusResponse | null>(null)
const stats = ref<StatsResponse | null>(null)
const recentEntries = ref<TelescopeEntry[]>([])
const loading = ref(true)

const ws = getWebSocket()

async function load() {
  loading.value = true
  try {
    const [s, e, st] = await Promise.all([
      api.status(),
      api.entries({ limit: '20' }),
      api.stats('24h').catch(() => null),
    ])
    status.value = s
    recentEntries.value = e.entries
    stats.value = st
  } finally {
    loading.value = false
  }
}

const unsub = ws.onEntry((entry) => {
  recentEntries.value.unshift(entry)
  if (recentEntries.value.length > 50) recentEntries.value = recentEntries.value.slice(0, 50)
  if (status.value) {
    status.value.total_entries++
    const slug = entry.type_slug
    if (status.value.types[slug]) {
      status.value.types[slug].count++
    } else {
      status.value.types[slug] = { label: entry.type_label, count: 1 }
    }
  }
})

onMounted(load)
onUnmounted(unsub)

// Animated counter
function useAnimatedNumber(target: number, duration = 600): string {
  return target.toLocaleString()
}

function apdexColor(score: number): string {
  if (score >= 0.9) return 'text-emerald-400'
  if (score >= 0.7) return 'text-amber-400'
  return 'text-red-400'
}

function apdexLabel(score: number): string {
  if (score >= 0.9) return 'Excellent'
  if (score >= 0.7) return 'Fair'
  return 'Poor'
}

const typeGlows: Record<string, string> = {
  request: 'glow-blue',
  query: 'glow-violet',
  exception: 'glow-red',
  model: 'glow-emerald',
  log: '',
  cache: 'glow-amber',
  mail: 'glow-cyan',
}

const typeAccents: Record<string, string> = {
  request: 'border-l-blue-500/60',
  query: 'border-l-violet-500/60',
  exception: 'border-l-red-500/60',
  model: 'border-l-emerald-500/60',
  log: 'border-l-surface-500/60',
  cache: 'border-l-amber-500/60',
  mail: 'border-l-cyan-500/60',
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-surface-100 light:text-surface-900 mb-6 animate-fade-in">Dashboard</h1>

    <!-- Hero Stats Row -->
    <div v-if="stats" class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="glass-card glow-blue animate-slide-up stagger-1">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Total Requests</div>
        <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.requests.total.toLocaleString() }}</div>
        <div class="text-xs text-surface-500 mt-1">{{ stats.requests.throughput_per_minute }}/min</div>
      </div>

      <div class="glass-card glow-emerald animate-slide-up stagger-2">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Apdex Score</div>
        <div class="text-3xl font-bold" :class="apdexColor(stats.requests.apdex)">{{ stats.requests.apdex.toFixed(3) }}</div>
        <div class="text-xs mt-1" :class="apdexColor(stats.requests.apdex)">{{ apdexLabel(stats.requests.apdex) }}</div>
      </div>

      <div class="glass-card glow-red animate-slide-up stagger-3">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Error Rate</div>
        <div class="text-3xl font-bold" :class="stats.requests.error_rate > 5 ? 'text-red-400' : stats.requests.error_rate > 1 ? 'text-amber-400' : 'text-emerald-400'">
          {{ stats.requests.error_rate }}%
        </div>
        <div class="text-xs text-surface-500 mt-1">{{ stats.requests.error_count }} errors</div>
      </div>

      <div class="glass-card glow-amber animate-slide-up stagger-4">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">P95 Latency</div>
        <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.requests.percentiles.p95 }}<span class="text-lg text-surface-500">ms</span></div>
        <div class="text-xs text-surface-500 mt-1">P50: {{ stats.requests.percentiles.p50 }}ms</div>
      </div>
    </div>

    <!-- Skeleton for hero stats -->
    <div v-else class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div v-for="i in 4" :key="i" class="glass-card">
        <div class="skeleton h-3 w-20 mb-3"></div>
        <div class="skeleton h-9 w-24 mb-2"></div>
        <div class="skeleton h-3 w-16"></div>
      </div>
    </div>

    <!-- Type Breakdown Grid -->
    <div v-if="status" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 mb-8">
      <div
        v-for="(info, slug, idx) in status.types"
        :key="slug"
        class="glass-card !p-4 border-l-[3px] animate-slide-up"
        :class="[typeGlows[slug as string] || '', typeAccents[slug as string] || 'border-l-surface-500/40', `stagger-${Math.min(idx + 1, 10)}`]"
      >
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-1">{{ info.label }}</div>
        <div class="text-xl font-bold text-surface-100 light:text-surface-800">{{ info.count.toLocaleString() }}</div>
      </div>
    </div>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 mb-8">
      <div v-for="i in 6" :key="i" class="glass-card !p-4">
        <div class="skeleton h-3 w-14 mb-2"></div>
        <div class="skeleton h-6 w-16"></div>
      </div>
    </div>

    <!-- Cache & N+1 Row -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div class="glass-card animate-slide-up stagger-5">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-3">Cache Performance</div>
        <div class="flex items-end gap-4">
          <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.cache.hit_rate }}%</div>
          <div class="flex-1">
            <div class="flex justify-between text-xs text-surface-500 mb-1">
              <span>Hit Rate</span>
              <span>{{ stats.cache.hits }}/{{ stats.cache.total }}</span>
            </div>
            <div class="w-full bg-surface-800 light:bg-surface-200 rounded-full h-2">
              <div class="percentile-bar animate-bar-fill" :style="{ width: stats.cache.hit_rate + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card animate-slide-up stagger-6">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-3">Query Health</div>
        <div class="flex items-center gap-6">
          <div>
            <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.queries.total.toLocaleString() }}</div>
            <div class="text-xs text-surface-500">Total queries</div>
          </div>
          <div>
            <div class="text-2xl font-bold" :class="stats.queries.n_plus_one_patterns > 0 ? 'text-red-400' : 'text-emerald-400'">
              {{ stats.queries.n_plus_one_patterns }}
            </div>
            <div class="text-xs text-surface-500">N+1 patterns</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-amber-400">{{ stats.queries.slow_patterns.length }}</div>
            <div class="text-xs text-surface-500">Slow patterns</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Entries -->
    <div class="glass overflow-hidden animate-slide-up stagger-7">
      <div class="px-5 py-3 border-b border-surface-800/40 light:border-surface-200 bg-surface-800/20 light:bg-surface-50/50">
        <h2 class="text-[11px] font-semibold text-surface-400 uppercase tracking-widest">Recent Entries</h2>
      </div>
      <EntryTable :entries="recentEntries" :loading="loading" />
    </div>
  </div>
</template>
