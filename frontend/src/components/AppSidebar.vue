<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const analyticsItems = [
  { path: '/', label: 'Dashboard', icon: '◉' },
  { path: '/stats', label: 'Stats', icon: '📊' },
  { path: '/health', label: 'Health', icon: '💚' },
]

const watcherItems = [
  { path: '/requests', label: 'Requests', icon: '⇄' },
  { path: '/queries', label: 'Queries', icon: '⛁' },
  { path: '/exceptions', label: 'Exceptions', icon: '⚠' },
  { path: '/models', label: 'Models', icon: '◧' },
  { path: '/logs', label: 'Logs', icon: '☰' },
  { path: '/cache', label: 'Cache', icon: '⧉' },
  { path: '/redis', label: 'Redis', icon: '◆' },
  { path: '/mail', label: 'Mail', icon: '✉' },
  { path: '/views', label: 'Views', icon: '◱' },
  { path: '/events', label: 'Events', icon: '⚡' },
  { path: '/commands', label: 'Commands', icon: '⌘' },
  { path: '/dumps', label: 'Dumps', icon: '⊞' },
  { path: '/http-client', label: 'HTTP Client', icon: '↗' },
  { path: '/gates', label: 'Gates', icon: '🔒' },
  { path: '/notifications', label: 'Notifications', icon: '🔔' },
  { path: '/schedule', label: 'Schedule', icon: '⏱' },
  { path: '/batches', label: 'Batches', icon: '▦' },
  { path: '/transactions', label: 'Transactions', icon: '⇌' },
  { path: '/storage', label: 'Storage', icon: '📁' },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside class="w-56 flex-shrink-0 bg-surface-900/80 light:bg-white/90 backdrop-blur-xl border-r border-surface-800/60 light:border-surface-200 flex flex-col overflow-y-auto">
    <!-- Brand -->
    <div class="p-4 pb-3">
      <router-link to="/" class="flex items-center gap-2.5 group">
        <span class="text-2xl transition-transform duration-300 group-hover:scale-110">🔭</span>
        <span class="text-lg font-bold bg-gradient-to-r from-primary-400 to-primary-300 bg-clip-text text-transparent">
          Telescope
        </span>
      </router-link>
    </div>

    <!-- Analytics Section -->
    <div class="px-3 pt-2">
      <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold px-2 mb-1.5">Analytics</div>
      <nav class="space-y-0.5">
        <router-link
          v-for="item in analyticsItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          :class="isActive(item.path)
            ? 'bg-primary-600/15 text-primary-400 border-l-[3px] border-primary-500 shadow-[inset_0_0_12px_-4px_rgba(99,102,241,0.15)] light:bg-primary-50 light:text-primary-700 light:border-primary-500'
            : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 hover:translate-x-0.5 border-l-[3px] border-transparent light:text-surface-600 light:hover:text-surface-800 light:hover:bg-surface-100'"
        >
          <span class="text-base w-5 text-center">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </div>

    <!-- Watchers Section -->
    <div class="px-3 pt-4 flex-1">
      <div class="text-[10px] uppercase tracking-widest text-surface-500 font-semibold px-2 mb-1.5">Watchers</div>
      <nav class="space-y-0.5">
        <router-link
          v-for="item in watcherItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-200"
          :class="isActive(item.path)
            ? 'bg-primary-600/15 text-primary-400 border-l-[3px] border-primary-500 shadow-[inset_0_0_12px_-4px_rgba(99,102,241,0.15)] light:bg-primary-50 light:text-primary-700 light:border-primary-500'
            : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 hover:translate-x-0.5 border-l-[3px] border-transparent light:text-surface-600 light:hover:text-surface-800 light:hover:bg-surface-100'"
        >
          <span class="text-sm w-5 text-center opacity-70">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </div>
  </aside>
</template>
