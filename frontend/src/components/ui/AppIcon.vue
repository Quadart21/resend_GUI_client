<script setup>
import { computed } from 'vue'
import { ICONS } from './icons'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: String, default: 'md' },
  filled: { type: Boolean, default: false },
})

const path = computed(() => ICONS[props.name] || '')

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-4 w-4'
  if (props.size === 'lg') return 'h-6 w-6'
  return 'h-[18px] w-[18px]'
})
</script>

<template>
  <svg
    :class="sizeClass"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-if="filled && name === 'star'" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2" fill="currentColor" stroke="none" />
    <path v-else :d="path" />
  </svg>
</template>
