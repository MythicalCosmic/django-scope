<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const analyticsItems = [
  { path: '/', label: 'Dashboard', icon: '\u25C9' },
  { path: '/stats', label: 'Stats', icon: '\u2261' },
  { path: '/health', label: 'Health', icon: '\u2665' },
]

const watcherItems = [
  { path: '/requests', label: 'Requests', icon: '\u21C4' },
  { path: '/queries', label: 'Queries', icon: '\u26C1' },
  { path: '/exceptions', label: 'Exceptions', icon: '\u26A0' },
  { path: '/models', label: 'Models', icon: '\u25E7' },
  { path: '/logs', label: 'Logs', icon: '\u2630' },
  { path: '/cache', label: 'Cache', icon: '\u29C9' },
  { path: '/redis', label: 'Redis', icon: '\u25C6' },
  { path: '/mail', label: 'Mail', icon: '\u2709' },
  { path: '/views', label: 'Views', icon: '\u25F1' },
  { path: '/events', label: 'Events', icon: '\u2B21' },
  { path: '/commands', label: 'Commands', icon: '\u2318' },
  { path: '/dumps', label: 'Dumps', icon: '\u229E' },
  { path: '/http-client', label: 'HTTP Client', icon: '\u2197' },
  { path: '/gates', label: 'Gates', icon: '\u2616' },
  { path: '/notifications', label: 'Notifications', icon: '\u266A' },
  { path: '/schedule', label: 'Schedule', icon: '\u23F1' },
  { path: '/batches', label: 'Batches', icon: '\u25A6' },
  { path: '/transactions', label: 'Transactions', icon: '\u21CC' },
  { path: '/storage', label: 'Storage', icon: '\u2750' },
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
        <span class="text-xl text-primary-400 transition-transform duration-300 group-hover:scale-110">&#x25CE;</span>
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
