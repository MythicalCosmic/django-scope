<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import type { HealthResponse } from '../types'

const health = ref<HealthResponse | null>(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    health.value = await api.health()
  } finally {
    loading.value = false
  }
}

onMounted(load)

function statusColor(status: string): string {
  switch (status) {
    case 'healthy': return 'border-emerald-500/30 bg-emerald-500/5'
    case 'failed': return 'border-red-500/30 bg-red-500/5'
    case 'disabled': return 'border-surface-600/30 bg-surface-800/30'
    default: return 'border-surface-600/30 bg-surface-800/30'
  }
}

function statusDot(status: string): string {
  switch (status) {
    case 'healthy': return 'status-dot-healthy'
    case 'failed': return 'status-dot-failed'
    case 'disabled': return 'status-dot-disabled'
    default: return 'status-dot-disabled'
  }
}

function formatWatcherName(name: string): string {
  return name.replace('Watcher', '').replace(/([A-Z])/g, ' $1').trim()
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-surface-100 light:text-surface-900 mb-6 animate-fade-in">Watcher Health</h1>

    <div v-if="health">
      <!-- Summary Bar -->
      <div class="glass-card flex items-center gap-6 mb-6 animate-slide-up stagger-1">
        <div class="flex items-center gap-2">
          <span class="status-dot status-dot-healthy"></span>
          <span class="text-sm text-surface-300 light:text-surface-700">{{ health.summary.healthy }} healthy</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="status-dot status-dot-failed"></span>
          <span class="text-sm text-surface-300 light:text-surface-700">{{ health.summary.failed }} failed</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="status-dot status-dot-disabled"></span>
          <span class="text-sm text-surface-300 light:text-surface-700">{{ health.summary.disabled }} disabled</span>
        </div>
        <div class="ml-auto text-sm text-surface-500">{{ health.summary.total }} total</div>
      </div>

      <!-- Watcher Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="(info, name, idx) in health.watchers"
          :key="name"
          class="glass-card !p-4 border-l-[3px] animate-slide-up"
          :class="[statusColor(info.status), `stagger-${Math.min((idx as number) + 1, 10)}`]"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="status-dot" :class="statusDot(info.status)"></span>
              <span class="text-sm font-semibold text-surface-200 light:text-surface-800">{{ formatWatcherName(name as string) }}</span>
            </div>
            <span
              class="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded-md"
              :class="{
                'text-emerald-400 bg-emerald-500/10': info.status === 'healthy',
                'text-red-400 bg-red-500/10': info.status === 'failed',
                'text-surface-500 bg-surface-700/30': info.status === 'disabled',
              }"
            >
              {{ info.status }}
            </span>
          </div>

          <div v-if="info.dependency" class="text-xs text-surface-500 mb-1">
            Requires: <span class="text-surface-400 font-mono">{{ info.dependency }}</span>
          </div>

          <div v-if="info.error" class="mt-2 p-2 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-400 font-mono truncate">
            {{ info.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-else class="space-y-4">
      <div class="glass-card">
        <div class="skeleton h-5 w-48"></div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="i in 9" :key="i" class="glass-card !p-4">
          <div class="skeleton h-4 w-32 mb-2"></div>
          <div class="skeleton h-3 w-20"></div>
        </div>
      </div>
    </div>
  </div>
</template>
