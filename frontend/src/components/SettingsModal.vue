<script setup>
import { ref, watch } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'changed', 'open-users'])

const apiKey = ref('')
const apiKeyHint = ref('')
const mailboxes = ref([])
const newName = ref('')
const newEmail = ref('')
const saving = ref(false)

watch(
  () => props.open,
  (isOpen) => { if (isOpen) load() },
)

async function load() {
  const cfg = await api.getConfig()
  apiKeyHint.value = cfg.has_api_key
    ? `Текущий: ${cfg.api_key_preview} (оставьте пустым, чтобы не менять)`
    : 'Ключ ещё не задан'
  mailboxes.value = cfg.mailboxes || []
}

async function saveApiKey() {
  saving.value = true
  try {
    await api.saveApiKey(apiKey.value)
    apiKey.value = ''
    await load()
    emit('changed')
  } finally {
    saving.value = false
  }
}

async function addMailbox() {
  saving.value = true
  try {
    await api.createMailbox(newName.value, newEmail.value)
    newName.value = ''
    newEmail.value = ''
    await load()
    emit('changed')
  } finally {
    saving.value = false
  }
}

async function deleteMailbox(id) {
  if (!confirm('Удалить этот ящик?')) return
  await api.deleteMailbox(id)
  await load()
  emit('changed')
}

defineExpose({ load })
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[1000] flex items-end justify-center bg-black/65 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[100dvh] w-full animate-slide-up flex-col overflow-hidden border-border bg-surface shadow-2xl sm:max-h-[90vh] sm:max-w-xl sm:rounded-[14px] sm:border">
        <header class="flex shrink-0 items-center justify-between border-b border-border px-4 py-4 sm:px-6 sm:py-5">
          <h2 class="text-[17px] font-bold">Настройки</h2>
          <button type="button" class="btn-icon" @click="emit('close')">✕</button>
        </header>

        <div class="flex-1 space-y-7 overflow-y-auto p-4 sm:p-6" style="padding-bottom: max(1rem, env(safe-area-inset-bottom));">
          <!-- API-ключ -->
          <section>
            <h3 class="mb-1.5 text-sm font-bold">API-ключ Resend</h3>
            <p class="mb-3.5 text-xs leading-relaxed text-zinc-500">
              Получите ключ в
              <a href="https://resend.com/api-keys" target="_blank" class="text-accent-hover hover:underline">Resend Dashboard</a>
            </p>
            <form class="space-y-2.5" @submit.prevent="saveApiKey">
              <input v-model="apiKey" type="password" class="input-field" placeholder="re_xxxxxxxx" autocomplete="off" />
              <small class="block text-[11px] text-zinc-500">{{ apiKeyHint }}</small>
              <button type="submit" class="btn-primary" :disabled="saving">Сохранить ключ</button>
            </form>
          </section>

          <!-- Ящики -->
          <section>
            <h3 class="mb-1.5 text-sm font-bold">Почтовые ящики</h3>
            <p class="mb-3.5 text-xs leading-relaxed text-zinc-500">
              Каждый ящик — отдельный адрес на домене. Входящие фильтруются по полю «Кому».
            </p>

            <div v-if="!mailboxes.length" class="mb-3 text-xs text-zinc-500">Ящиков пока нет</div>

            <div
              v-for="box in mailboxes"
              :key="box.id"
              class="mb-2 flex items-center gap-2.5 rounded-[10px] border border-border bg-surface-elevated px-3 py-2.5"
            >
              <div
                class="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-[11px] font-bold text-white"
                :style="{ background: box.color }"
              >
                {{ FormatHelper.initials(box.name, box.email) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-[13px] font-semibold">{{ box.name || box.email }}</div>
                <div class="truncate text-[11px] text-zinc-500">{{ box.email }}</div>
              </div>
              <button type="button" class="text-xs text-red-400 hover:underline" @click="deleteMailbox(box.id)">
                Удалить
              </button>
            </div>

            <form class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_auto]" @submit.prevent="addMailbox">
              <input v-model="newName" type="text" class="input-field" placeholder="Имя (Поддержка)" required />
              <input v-model="newEmail" type="email" class="input-field" placeholder="support@domain.com" required />
              <button type="submit" class="btn-secondary whitespace-nowrap" :disabled="saving">Добавить</button>
            </form>
          </section>

          <section>
            <h3 class="mb-1.5 text-sm font-bold">Пользователи и права</h3>
            <p class="mb-3 text-xs leading-relaxed text-zinc-500">
              Создавайте учётные записи и назначайте доступ к одному или нескольким ящикам.
            </p>
            <button type="button" class="btn-secondary" @click="emit('open-users')">
              Управление пользователями
            </button>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>
