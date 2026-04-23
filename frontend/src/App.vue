<script setup lang="ts">
import MainLayout from './layouts/MainLayout.vue'
</script>

<template>
  <MainLayout>
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </MainLayout>
</template>

<style>
.page-enter-active {
  transition: opacity 0.2s cubic-bezier(0.21, 1.02, 0.73, 1), transform 0.2s cubic-bezier(0.21, 1.02, 0.73, 1);
}
.page-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
