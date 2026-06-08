<script setup>
defineProps({
  variant: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'accent', 'success', 'warning', 'danger', 'brand'].includes(v),
  },
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold leading-none"
    :class="{
      'bg-surface-active text-muted': variant === 'neutral',
      'bg-accent/15 text-accent-hover': variant === 'accent',
      'bg-success/15 text-success': variant === 'success',
      'bg-warning/15 text-warning': variant === 'warning',
      'bg-danger/15 text-danger': variant === 'danger',
      'bg-brand/15 text-brand-300': variant === 'brand',
    }"
  >
    <slot />
  </span>
</template>
