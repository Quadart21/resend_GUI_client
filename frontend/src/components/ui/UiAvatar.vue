<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '?' },
  color: { type: String, default: '' },
  size: { type: String, default: 'md' },
  outbound: { type: Boolean, default: false },
})

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-8 w-8 text-[10px]'
  if (props.size === 'lg') return 'h-11 w-11 text-sm'
  return 'h-9 w-9 text-xs'
})

const style = computed(() => {
  if (props.color) return { background: props.color }
  return {}
})
</script>

<template>
  <div
    class="grid shrink-0 place-items-center rounded-full font-bold text-white shadow-sm ring-1 ring-white/10"
    :class="[
      sizeClass,
      !color && (outbound ? 'bg-gradient-to-br from-brand-500 to-brand-700' : 'bg-gradient-to-br from-zinc-600 to-zinc-700'),
    ]"
    :style="style"
  >
    {{ label }}
  </div>
</template>
