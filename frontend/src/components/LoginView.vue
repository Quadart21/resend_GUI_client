<script setup>
import { ref } from 'vue'
import { api } from '@/services/ApiClient'

const emit = defineEmits(['login'])

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const data = await api.login(username.value.trim(), password.value)
    emit('login', data.user)
  } catch (err) {
    error.value = err.message || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="flex min-h-[100dvh] items-center justify-center bg-[#09090b] px-4"
    style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom);"
  >
    <div class="w-full max-w-sm rounded-[14px] border border-border bg-surface p-6 shadow-2xl">
      <div class="mb-6 flex items-center gap-3">
        <div class="grid h-11 w-11 place-items-center rounded-[11px] bg-gradient-to-br from-accent to-purple-500 text-white">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
        </div>
        <div>
          <h1 class="text-lg font-bold leading-snug">Почтовый клиент Kubex.me</h1>
          <p class="text-xs text-zinc-500">Вход в почту</p>
        </div>
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <label class="block">
          <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Логин</span>
          <input
            v-model="username"
            type="text"
            class="input-field"
            autocomplete="username"
            required
            autofocus
          />
        </label>

        <label class="block">
          <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Пароль</span>
          <input
            v-model="password"
            type="password"
            class="input-field"
            autocomplete="current-password"
            required
          />
        </label>

        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>
    </div>
  </div>
</template>
