<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['close'])

const sizeClass = {
  sm: 'sm:max-w-md',
  md: 'sm:max-w-lg',
  lg: 'sm:max-w-2xl',
  xl: 'sm:max-w-4xl',
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="modal-overlay"
        @click.self="emit('close')"
      >
        <div
          class="modal-panel"
          :class="sizeClass[size] || sizeClass.md"
          role="dialog"
          aria-modal="true"
        >
          <header v-if="title || $slots.header" class="modal-header">
            <slot name="header">
              <h2 class="text-lg font-bold tracking-tight">{{ title }}</h2>
            </slot>
            <button type="button" class="btn-icon btn-icon-ghost" aria-label="Закрыть" @click="emit('close')">
              <AppIcon name="close" />
            </button>
          </header>

          <div class="modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-panel,
.modal-leave-to .modal-panel {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}
</style>
