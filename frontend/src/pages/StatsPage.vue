<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import type { StatsResponse } from '../types'

const stats = ref<StatsResponse | null>(null)
const loading = ref(true)
const selectedRange = ref('24h')
const ranges = ['1h', '6h', '24h', '7d']

async function load(range: string) {
  loading.value = true
  selectedRange.value = range
  try {
    stats.value = await api.stats(range)
  } finally {
    loading.value = false
  }
}

function apdexColor(score: number): string {
  if (score >= 0.9) return 'text-emerald-400'
  if (score >= 0.7) return 'text-amber-400'
  return 'text-red-400'
}

function apdexBg(score: number): string {
  if (score >= 0.9) return 'bg-emerald-500'
  if (score >= 0.7) return 'bg-amber-500'
  return 'bg-red-500'
}

function percentileWidth(value: number, max: number): string {
  if (!max) return '0%'
  return Math.min((value / max) * 100, 100) + '%'
}

onMounted(() => load('24h'))
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-surface-100 light:text-surface-900 animate-fade-in">Stats</h1>
      <div class="flex items-center gap-1 glass !rounded-lg !p-1">
        <button
          v-for="r in ranges"
          :key="r"
          @click="load(r)"
          class="px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-200"
          :class="selectedRange === r
            ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/20'
            : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 light:hover:bg-surface-100'"
        >
          {{ r }}
        </button>
      </div>
    </div>

    <div v-if="stats">
      <!-- Top Metrics -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="glass-card glow-blue animate-slide-up stagger-1">
          <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Throughput</div>
          <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.requests.throughput_per_minute }}</div>
          <div class="text-xs text-surface-500 mt-1">requests/min</div>
        </div>

        <div class="glass-card animate-slide-up stagger-2">
          <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Apdex</div>
          <div class="text-3xl font-bold" :class="apdexColor(stats.requests.apdex)">{{ stats.requests.apdex.toFixed(3) }}</div>
          <div class="mt-2 w-full bg-surface-800 light:bg-surface-200 rounded-full h-1.5">
            <div class="h-1.5 rounded-full animate-bar-fill transition-all" :class="apdexBg(stats.requests.apdex)" :style="{ width: (stats.requests.apdex * 100) + '%' }"></div>
          </div>
        </div>

        <div class="glass-card glow-red animate-slide-up stagger-3">
          <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Errors</div>
          <div class="text-3xl font-bold" :class="stats.requests.error_rate > 5 ? 'text-red-400' : 'text-emerald-400'">{{ stats.requests.error_rate }}%</div>
          <div class="text-xs text-surface-500 mt-1">{{ stats.requests.error_count }} of {{ stats.requests.total }}</div>
        </div>

        <div class="glass-card glow-amber animate-slide-up stagger-4">
          <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-2">Cache Hit Rate</div>
          <div class="text-3xl font-bold text-surface-100 light:text-surface-800">{{ stats.cache.hit_rate }}%</div>
          <div class="text-xs text-surface-500 mt-1">{{ stats.cache.hits }}/{{ stats.cache.total }} hits</div>
        </div>
      </div>

      <!-- Percentiles -->
      <div class="glass-card mb-6 animate-slide-up stagger-5">
        <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-4">Response Time Percentiles</div>
        <div class="space-y-3">
          <div v-for="p in [
            { key: 'p50' as const, label: 'P50 (median)', color: 'bg-gradient-to-r from-emerald-500 to-primary-500' },
            { key: 'p75' as const, label: 'P75', color: 'bg-gradient-to-r from-emerald-500 to-primary-500' },
            { key: 'p95' as const, label: 'P95', color: 'bg-gradient-to-r from-primary-500 to-amber-500' },
            { key: 'p99' as const, label: 'P99', color: 'bg-gradient-to-r from-amber-500 to-red-500' },
          ]" :key="p.key">
            <div class="flex justify-between text-xs mb-1">
              <span class="text-surface-400 font-medium">{{ p.label }}</span>
              <span class="text-surface-200 light:text-surface-700 font-semibold font-mono">{{ stats.requests.percentiles[p.key] }}ms</span>
            </div>
            <div class="w-full bg-surface-800 light:bg-surface-200 rounded-full h-2">
              <div
                class="h-2 rounded-full animate-bar-fill"
                :class="p.color"
                :style="{ width: percentileWidth(stats.requests.percentiles[p.key], stats.requests.percentiles.p99 * 1.2) }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Slow Queries & N+1 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="glass-card animate-slide-up stagger-6">
          <div class="flex items-center justify-between mb-4">
            <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold">Slow Query Patterns</div>
            <span class="text-xs text-surface-500">Top 10</span>
          </div>
          <div v-if="stats.queries.slow_patterns.length" class="space-y-2">
            <div
              v-for="(pattern, idx) in stats.queries.slow_patterns"
              :key="pattern.family_hash"
              class="p-3 rounded-lg bg-surface-800/40 light:bg-surface-100 animate-slide-up"
              :class="`stagger-${Math.min(idx + 1, 10)}`"
            >
              <div class="font-mono text-xs text-surface-300 light:text-surface-700 truncate mb-1">{{ pattern.sample_sql }}</div>
              <div class="flex gap-4 text-xs text-surface-500">
                <span><strong class="text-surface-300 light:text-surface-700">{{ pattern.count }}</strong> calls</span>
                <span>avg <strong class="text-amber-400">{{ pattern.avg_duration }}ms</strong></span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-surface-500 text-sm">No slow patterns</div>
        </div>

        <div class="glass-card animate-slide-up stagger-7">
          <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold mb-4">Query Health Summary</div>
          <div class="space-y-4">
            <div class="flex items-center justify-between p-3 rounded-lg bg-surface-800/40 light:bg-surface-100">
              <span class="text-sm text-surface-400">Total Queries</span>
              <span class="text-lg font-bold text-surface-100 light:text-surface-800">{{ stats.queries.total.toLocaleString() }}</span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg" :class="stats.queries.n_plus_one_patterns > 0 ? 'bg-red-500/10 border border-red-500/20' : 'bg-emerald-500/10 border border-emerald-500/20'">
              <span class="text-sm" :class="stats.queries.n_plus_one_patterns > 0 ? 'text-red-400' : 'text-emerald-400'">N+1 Patterns</span>
              <span class="text-lg font-bold" :class="stats.queries.n_plus_one_patterns > 0 ? 'text-red-400' : 'text-emerald-400'">{{ stats.queries.n_plus_one_patterns }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="space-y-4">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="glass-card">
          <div class="skeleton h-3 w-20 mb-3"></div>
          <div class="skeleton h-9 w-24"></div>
        </div>
      </div>
      <div class="glass-card">
        <div class="skeleton h-3 w-40 mb-4"></div>
        <div v-for="i in 4" :key="i" class="mb-3">
          <div class="skeleton h-2 w-full"></div>
        </div>
      </div>
    </div>
  </div>
</template>
