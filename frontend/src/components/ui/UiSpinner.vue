<script setup>
defineProps({
  label: { type: String, default: '' },
  size: { type: String, default: 'md' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 text-muted">
    <div
      class="animate-spin rounded-full border-2 border-border border-t-accent"
      :class="size === 'sm' ? 'h-5 w-5' : 'h-8 w-8'"
    />
    <p v-if="label" class="text-sm">{{ label }}</p>
  </div>
</template>
