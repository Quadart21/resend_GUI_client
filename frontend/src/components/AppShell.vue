<script setup>
defineProps({
  sidebarOpen: { type: Boolean, default: false },
})

defineEmits(['close-sidebar'])
</script>

<template>
  <div class="flex h-[100dvh] flex-col overflow-hidden bg-canvas">
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-black/60 backdrop-blur-[2px] md:hidden"
      aria-hidden="true"
      @click="$emit('close-sidebar')"
    />

    <slot name="topbar" />

    <slot name="sidebar" />

    <div class="flex min-h-0 flex-1 overflow-hidden">
      <slot name="list" />
      <slot name="main" />
    </div>
  </div>
</template>
