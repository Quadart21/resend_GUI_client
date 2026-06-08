<script setup>
defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array, required: true },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="segmented" role="tablist">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      class="segmented-item"
      :class="{ 'segmented-item-active': modelValue === opt.value, 'segmented-item-warn': opt.warn && modelValue === opt.value }"
      :aria-selected="modelValue === opt.value"
      @click="emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
      <span v-if="opt.count" class="ml-1 opacity-70">{{ opt.count }}</span>
    </button>
  </div>
</template>
