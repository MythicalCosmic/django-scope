<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { getWebSocket } from '../websocket'

const ws = getWebSocket()

onMounted(() => { ws.connect() })
onUnmounted(() => { /* keep connection alive */ })
</script>

<template>
  <div class="flex items-center gap-2.5 text-sm">
    <span class="relative flex items-center justify-center w-3 h-3">
      <!-- Ripple ring when connected -->
      <span
        v-if="ws.status.value === 'connected'"
        class="absolute w-3 h-3 rounded-full bg-emerald-400/40"
        style="animation: pulse-ring 2s cubic-bezier(0, 0, 0.2, 1) infinite;"
      />
      <span
        class="relative inline-block w-2 h-2 rounded-full transition-colors duration-300"
        :class="{
          'bg-emerald-400': ws.status.value === 'connected',
          'bg-amber-400 animate-pulse': ws.status.value === 'connecting',
          'bg-red-400': ws.status.value === 'disconnected',
        }"
      />
    </span>
    <span class="text-surface-500 light:text-surface-400 text-[11px] uppercase tracking-widest font-semibold">
      {{ ws.status.value === 'connected' ? 'Live' : ws.status.value === 'connecting' ? 'Connecting' : 'Offline' }}
    </span>
  </div>
</template>
