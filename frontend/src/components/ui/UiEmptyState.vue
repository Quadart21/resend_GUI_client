<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  icon: { type: String, default: 'inbox' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center px-6 py-16 text-center">
    <div class="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-surface-active text-2xl ring-1 ring-border">
      <slot name="icon">
        <span class="text-muted">{{ icon === 'mail' ? '✉️' : icon === 'search' ? '🔍' : '📭' }}</span>
      </slot>
    </div>
    <h3 class="text-base font-semibold text-zinc-200">{{ title }}</h3>
    <p v-if="description" class="mt-1.5 max-w-xs text-sm text-muted">{{ description }}</p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>
