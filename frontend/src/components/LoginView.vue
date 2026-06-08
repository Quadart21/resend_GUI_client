<script setup>
import { ref } from 'vue'
import { api } from '@/services/ApiClient'
import AppIcon from '@/components/ui/AppIcon.vue'

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
    class="grid min-h-[100dvh] lg:grid-cols-2"
    style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom);"
  >
    <div class="relative hidden overflow-hidden bg-surface-elevated lg:flex lg:flex-col lg:justify-between lg:p-12">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(99,102,241,0.18),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(67,56,202,0.12),transparent_50%)]" />
      <div class="relative">
        <div class="brand-mark mb-8 h-12 w-12">
          <AppIcon name="mail" />
        </div>
        <h1 class="max-w-md text-3xl font-bold leading-tight tracking-tight">
          Почта команды на вашем домене
        </h1>
        <p class="mt-4 max-w-sm text-base leading-relaxed text-muted">
          Kubex Mail — быстрый веб-клиент для Resend: переписки, вложения, уведомления и совместная работа.
        </p>
      </div>
      <p class="relative text-xs text-muted">webmail.kubex.me</p>
    </div>

    <div class="flex items-center justify-center px-4 py-10 lg:px-12">
      <div class="w-full max-w-sm">
        <div class="mb-8 lg:hidden">
          <div class="brand-mark mb-4">
            <AppIcon name="mail" size="sm" />
          </div>
          <h1 class="text-xl font-bold">Kubex Mail</h1>
          <p class="text-sm text-muted">Вход в почтовый клиент</p>
        </div>

        <div class="rounded-2xl border border-border bg-surface p-6 shadow-panel lg:border-0 lg:bg-transparent lg:p-0 lg:shadow-none">
          <h2 class="mb-1 hidden text-xl font-bold lg:block">Вход</h2>
          <p class="mb-6 hidden text-sm text-muted lg:block">Введите логин и пароль</p>

          <form class="space-y-4" @submit.prevent="submit">
            <label class="block">
              <span class="mb-1.5 block text-xs font-semibold text-muted">Логин</span>
              <input v-model="username" type="text" class="input-field" autocomplete="username" required autofocus />
            </label>
            <label class="block">
              <span class="mb-1.5 block text-xs font-semibold text-muted">Пароль</span>
              <input v-model="password" type="password" class="input-field" autocomplete="current-password" required />
            </label>
            <p v-if="error" class="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{{ error }}</p>
            <button type="submit" class="btn-primary w-full" :disabled="loading">
              {{ loading ? 'Вход...' : 'Войти' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
