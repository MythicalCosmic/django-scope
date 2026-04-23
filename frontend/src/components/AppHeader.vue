<script setup lang="ts">
import { ref } from 'vue'
import { useThemeStore } from '../stores/theme'
import { api } from '../api'
import LiveIndicator from './LiveIndicator.vue'

const theme = useThemeStore()
const recording = ref(true)
const toggling = ref(false)

async function toggleRecording() {
  toggling.value = true
  try {
    const res = await api.toggleRecording()
    recording.value = res.recording
  } finally {
    toggling.value = false
  }
}
</script>

<template>
  <header class="h-14 flex-shrink-0 border-b border-surface-800/60 light:border-surface-200 bg-surface-900/60 light:bg-white/80 backdrop-blur-xl flex items-center justify-between px-6">
    <div class="flex items-center gap-4">
      <LiveIndicator />
    </div>

    <div class="flex items-center gap-2">
      <!-- Recording Toggle -->
      <button
        @click="toggleRecording"
        :disabled="toggling"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
        :class="recording
          ? 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20'
          : 'bg-surface-800 text-surface-400 border border-surface-700 hover:bg-surface-700 light:bg-surface-100 light:border-surface-200'"
      >
        <span class="w-2 h-2 rounded-full" :class="recording ? 'bg-red-400 animate-pulse-dot' : 'bg-surface-500'" />
        {{ recording ? 'Recording' : 'Paused' }}
      </button>

      <!-- Theme Toggle -->
      <button
        @click="theme.toggle()"
        class="p-2 rounded-lg text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 light:hover:text-surface-700 light:hover:bg-surface-100 transition-all duration-200"
        :title="theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <span class="text-base inline-block transition-transform duration-300" :class="theme.isDark ? 'rotate-0' : 'rotate-180'">
          {{ theme.isDark ? '\u263C' : '\u263E' }}
        </span>
      </button>
    </div>
  </header>
</template>
