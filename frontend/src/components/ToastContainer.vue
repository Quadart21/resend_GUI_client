<script setup>
/** Composable: toast-уведомления */
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
  timer = setTimeout(() => { visible.value = false }, 4000)
}

defineExpose({ show })
</script>

<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
        v-if="visible"
        class="fixed bottom-6 right-6 z-[2000] max-w-sm animate-slide-up rounded-[10px] border bg-surface px-5 py-3.5 text-sm shadow-2xl"
        :class="type === 'error' ? 'border-red-500' : 'border-green-500'"
      >
        {{ message }}
      </div>
    </Transition>
  </Teleport>
</template>
