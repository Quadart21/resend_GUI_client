<script setup>
import { ref, watch } from 'vue'
import { api } from '@/services/ApiClient'
import UiModal from '@/components/ui/UiModal.vue'

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
  <UiModal :open="open" title="Смена пароля" size="sm" @close="emit('close')">
    <form id="profile-form" class="space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="field-label">Текущий пароль</span>
        <input v-model="currentPassword" type="password" class="input-field" required autocomplete="current-password" />
      </label>
      <label class="block">
        <span class="field-label">Новый пароль</span>
        <input v-model="newPassword" type="password" class="input-field" required minlength="4" autocomplete="new-password" />
      </label>
      <label class="block">
        <span class="field-label">Подтверждение</span>
        <input v-model="confirmPassword" type="password" class="input-field" required minlength="4" autocomplete="new-password" />
      </label>
    </form>
    <template #footer>
      <button type="button" class="btn-secondary" @click="emit('close')">Отмена</button>
      <button type="submit" form="profile-form" class="btn-primary" :disabled="saving">
        {{ saving ? 'Сохранение...' : 'Сохранить' }}
      </button>
    </template>
  </UiModal>
</template>

<style scoped>
.field-label {
  @apply mb-1.5 block text-xs font-semibold text-muted;
}
</style>
