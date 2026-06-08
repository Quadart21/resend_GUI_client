<script setup>
import { ref } from 'vue'

const message = ref('')
const type = ref('success')
const visible = ref(false)
let timer = null

function show(msg, msgType = 'success') {
  message.value = msg
  type.value = msgType
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { visible.value = false }, 4200)
}

defineExpose({ show })
</script>

<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
        v-if="visible"
        class="toast"
        :class="type === 'error' ? 'toast-error' : 'toast-success'"
        style="bottom: max(1.25rem, env(safe-area-inset-bottom)); right: max(1.25rem, env(safe-area-inset-right));"
      >
        <span class="toast-dot" />
        {{ message }}
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.toast {
  @apply fixed z-[2000] flex max-w-[calc(100vw-2rem)] items-center gap-2.5 rounded-xl border bg-surface-elevated px-4 py-3 text-sm shadow-float;
}
.toast-success {
  @apply border-success/40 text-zinc-100;
}
.toast-error {
  @apply border-danger/40 text-zinc-100;
}
.toast-dot {
  @apply h-2 w-2 shrink-0 rounded-full;
}
.toast-success .toast-dot {
  @apply bg-success;
}
.toast-error .toast-dot {
  @apply bg-danger;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
