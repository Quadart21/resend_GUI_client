<script setup>
import { ref, watch } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'changed', 'open-users', 'notify'])

const apiKey = ref('')
const apiKeyHint = ref('')
const webhookSecret = ref('')
const webhookSecretHint = ref('')
const mailboxes = ref([])
const newName = ref('')
const newEmail = ref('')
const saving = ref(false)
const editingId = ref(null)
const editName = ref('')
const editEmail = ref('')

watch(
  () => props.open,
  (isOpen) => { if (isOpen) load() },
)

async function loadMailboxes() {
  const data = await api.listMailboxes()
  mailboxes.value = data.mailboxes || []
}

async function load() {
  const cfg = await api.getConfig()
  apiKeyHint.value = cfg.has_api_key
    ? `Текущий: ${cfg.api_key_preview} (оставьте пустым, чтобы не менять)`
    : 'Ключ ещё не задан'
  webhookSecretHint.value = cfg.has_webhook_secret
    ? `Текущий: ${cfg.webhook_secret_preview} (оставьте пустым, чтобы не менять)`
    : 'Signing secret ещё не задан — webhook без проверки подписи'
  await loadMailboxes()
}

function toast(msg, type = 'success') {
  emit('notify', msg, type)
}

async function saveSettings() {
  saving.value = true
  try {
    await api.saveConfig({
      api_key: apiKey.value,
      webhook_secret: webhookSecret.value,
    })
    apiKey.value = ''
    webhookSecret.value = ''
    await load()
    toast('Настройки сохранены')
    emit('changed')
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

async function addMailbox() {
  saving.value = true
  try {
    await api.createMailbox(newName.value.trim(), newEmail.value.trim())
    newName.value = ''
    newEmail.value = ''
    await loadMailboxes()
    toast('Ящик добавлен')
    emit('changed')
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

function startEdit(box) {
  editingId.value = box.id
  editName.value = box.name || ''
  editEmail.value = box.email || ''
}

function cancelEdit() {
  editingId.value = null
  editName.value = ''
  editEmail.value = ''
}

async function saveEdit(id) {
  saving.value = true
  try {
    await api.updateMailbox(id, editName.value.trim(), editEmail.value.trim())
    cancelEdit()
    await loadMailboxes()
    toast('Ящик обновлён')
    emit('changed')
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

async function deleteMailbox(id, label) {
  if (!confirm(`Удалить ящик «${label}»?`)) return
  saving.value = true
  try {
    await api.deleteMailbox(id)
    if (editingId.value === id) cancelEdit()
    await loadMailboxes()
    toast('Ящик удалён')
    emit('changed')
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    saving.value = false
  }
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
          <section>
            <h3 class="mb-1.5 text-sm font-bold">API-ключ Resend</h3>
            <p class="mb-3.5 text-xs leading-relaxed text-zinc-500">
              Получите ключ в
              <a href="https://resend.com/api-keys" target="_blank" class="text-accent-hover hover:underline">Resend Dashboard</a>
            </p>
            <form class="space-y-2.5" @submit.prevent="saveSettings">
              <input v-model="apiKey" type="password" class="input-field" placeholder="re_xxxxxxxx" autocomplete="off" />
              <small class="block text-[11px] text-zinc-500">{{ apiKeyHint }}</small>
              <button type="submit" class="btn-primary" :disabled="saving">Сохранить ключ</button>
            </form>
          </section>

          <section>
            <h3 class="mb-1.5 text-sm font-bold">Webhook signing secret</h3>
            <p class="mb-3.5 text-xs leading-relaxed text-zinc-500">
              Ключ из
              <a href="https://resend.com/webhooks" target="_blank" class="text-accent-hover hover:underline">Resend → Webhooks</a>
              (<code class="text-zinc-400">whsec_...</code>)
            </p>
            <form class="space-y-2.5" @submit.prevent="saveSettings">
              <input
                v-model="webhookSecret"
                type="password"
                class="input-field"
                placeholder="whsec_xxxxxxxx"
                autocomplete="off"
              />
              <small class="block text-[11px] text-zinc-500">{{ webhookSecretHint }}</small>
              <button type="submit" class="btn-primary" :disabled="saving">Сохранить secret</button>
            </form>
          </section>

          <section>
            <h3 class="mb-1.5 text-sm font-bold">Почтовые ящики</h3>
            <p class="mb-3.5 text-xs leading-relaxed text-zinc-500">
              Управление адресами на домене. Входящие фильтруются по полю «Кому».
            </p>

            <div v-if="!mailboxes.length" class="mb-3 rounded-[10px] border border-dashed border-border px-3 py-4 text-center text-xs text-zinc-500">
              Ящиков пока нет — добавьте ниже
            </div>

            <div v-else class="mb-3 space-y-2">
              <div
                v-for="box in mailboxes"
                :key="box.id"
                class="rounded-[10px] border border-border bg-surface-elevated p-3"
              >
                <template v-if="editingId === box.id">
                  <form class="space-y-2" @submit.prevent="saveEdit(box.id)">
                    <input v-model="editName" type="text" class="input-field" placeholder="Имя" required />
                    <input v-model="editEmail" type="email" class="input-field" placeholder="email@domain.com" required />
                    <div class="flex justify-end gap-2">
                      <button type="button" class="btn-ghost text-xs" @click="cancelEdit">Отмена</button>
                      <button type="submit" class="btn-primary text-xs" :disabled="saving">Сохранить</button>
                    </div>
                  </form>
                </template>

                <template v-else>
                  <div class="flex items-center gap-2.5">
                    <div
                      class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[11px] font-bold text-white"
                      :style="{ background: box.color }"
                    >
                      {{ FormatHelper.initials(box.name, box.email) }}
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-[13px] font-semibold">{{ box.name || box.email }}</div>
                      <div class="truncate text-[11px] text-zinc-500">{{ box.email }}</div>
                    </div>
                    <div class="flex shrink-0 gap-1">
                      <button type="button" class="btn-icon h-8 w-8" title="Редактировать" @click="startEdit(box)">
                        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                          <path d="M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        class="btn-icon h-8 w-8 text-red-400 hover:text-red-300"
                        title="Удалить"
                        @click="deleteMailbox(box.id, box.name || box.email)"
                      >
                        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <form class="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_auto]" @submit.prevent="addMailbox">
              <input v-model="newName" type="text" class="input-field" placeholder="Имя (Поддержка)" required />
              <input v-model="newEmail" type="email" class="input-field" placeholder="support@domain.com" required />
              <button type="submit" class="btn-secondary whitespace-nowrap" :disabled="saving">+ Добавить</button>
            </form>
          </section>

          <section>
            <h3 class="mb-1.5 text-sm font-bold">Пользователи и права</h3>
            <p class="mb-3 text-xs leading-relaxed text-zinc-500">
              Назначайте пользователям доступ к ящикам.
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
