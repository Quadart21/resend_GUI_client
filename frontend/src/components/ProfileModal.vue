<script setup>
import { ref, watch } from 'vue'
import { api } from '@/services/ApiClient'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'notify'])

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    }
  },
)

async function submit() {
  if (newPassword.value !== confirmPassword.value) {
    emit('notify', 'Новый пароль и подтверждение не совпадают', 'error')
    return
  }
  saving.value = true
  try {
    await api.changePassword(currentPassword.value, newPassword.value)
    emit('notify', 'Пароль изменён')
    emit('close')
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[1000] flex items-end justify-center bg-black/65 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[100dvh] w-full animate-slide-up flex-col overflow-hidden border-border bg-surface shadow-2xl sm:max-h-[90vh] sm:max-w-md sm:rounded-[14px] sm:border">
        <header class="flex shrink-0 items-center justify-between border-b border-border px-4 py-4 sm:px-6 sm:py-5">
          <h2 class="text-[17px] font-bold">Смена пароля</h2>
          <button type="button" class="btn-icon" @click="emit('close')">✕</button>
        </header>

        <form
          class="space-y-3.5 overflow-y-auto p-4 sm:p-6"
          style="padding-bottom: max(1rem, env(safe-area-inset-bottom));"
          @submit.prevent="submit"
        >
          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Текущий пароль</span>
            <input
              v-model="currentPassword"
              type="password"
              class="input-field"
              required
              autocomplete="current-password"
            />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Новый пароль</span>
            <input
              v-model="newPassword"
              type="password"
              class="input-field"
              required
              minlength="4"
              autocomplete="new-password"
            />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Подтверждение</span>
            <input
              v-model="confirmPassword"
              type="password"
              class="input-field"
              required
              minlength="4"
              autocomplete="new-password"
            />
          </label>

          <div class="flex justify-end gap-2.5 pt-2">
            <button type="button" class="btn-secondary" @click="emit('close')">Отмена</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
