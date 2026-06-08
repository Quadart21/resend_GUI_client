<script setup>
import { ref, watch } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'
import UsersPanel from '@/components/UsersPanel.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  initialTab: { type: String, default: 'integration' },
  currentUserId: { type: String, default: null },
})

const emit = defineEmits(['close', 'changed', 'notify'])

const tabs = [
  { id: 'integration', label: 'Resend' },
  { id: 'mailboxes', label: 'Ящики' },
  { id: 'users', label: 'Пользователи' },
]

const activeTab = ref('integration')

const hasApiKey = ref(false)
const apiKeyPreview = ref('')
const hasWebhookSecret = ref(false)
const webhookSecretPreview = ref('')
const editingApiKey = ref(false)
const editingWebhookSecret = ref(false)

const apiKey = ref('')
const webhookSecret = ref('')
const mailboxes = ref([])
const newName = ref('')
const newEmail = ref('')
const saving = ref(false)
const editingId = ref(null)
const editName = ref('')
const editEmail = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      activeTab.value = props.initialTab || 'integration'
      load()
    }
  },
)

async function loadMailboxes() {
  const data = await api.listMailboxes()
  mailboxes.value = data.mailboxes || []
}

async function load() {
  const cfg = await api.getConfig()
  hasApiKey.value = Boolean(cfg.has_api_key)
  apiKeyPreview.value = cfg.api_key_preview || ''
  hasWebhookSecret.value = Boolean(cfg.has_webhook_secret)
  webhookSecretPreview.value = cfg.webhook_secret_preview || ''

  if (hasApiKey.value) {
    editingApiKey.value = false
    apiKey.value = ''
  } else {
    editingApiKey.value = true
  }

  if (hasWebhookSecret.value) {
    editingWebhookSecret.value = false
    webhookSecret.value = ''
  } else {
    editingWebhookSecret.value = true
  }

  await loadMailboxes()
}

function toast(msg, type = 'success') {
  emit('notify', msg, type)
}

async function saveApiKey() {
  if (!apiKey.value.trim()) {
    toast('Введите API-ключ', 'error')
    return
  }
  saving.value = true
  try {
    await api.saveConfig({ api_key: apiKey.value, webhook_secret: '' })
    apiKey.value = ''
    await load()
    toast('API-ключ сохранён')
    emit('changed')
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    saving.value = false
  }
}

async function saveWebhookSecret() {
  if (!webhookSecret.value.trim()) {
    toast('Введите signing secret', 'error')
    return
  }
  saving.value = true
  try {
    await api.saveConfig({ api_key: '', webhook_secret: webhookSecret.value })
    webhookSecret.value = ''
    await load()
    toast('Webhook secret сохранён')
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
        <header class="shrink-0 border-b border-border px-4 py-4 sm:px-6 sm:py-5">
          <div class="flex items-center justify-between">
            <h2 class="text-[17px] font-bold">Настройки</h2>
            <button type="button" class="btn-icon" @click="emit('close')">✕</button>
          </div>

          <nav class="mt-4 flex gap-1 rounded-[10px] bg-surface-elevated p-1">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              class="flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition sm:text-sm"
              :class="activeTab === tab.id
                ? 'bg-accent text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>
        </header>

        <div class="flex-1 overflow-y-auto p-4 sm:p-6" style="padding-bottom: max(1rem, env(safe-area-inset-bottom));">
          <!-- Resend: API + Webhook -->
          <div v-show="activeTab === 'integration'" class="space-y-6">
            <section class="rounded-[10px] border border-border bg-surface-elevated p-4">
              <h3 class="mb-1 text-sm font-bold">API-ключ Resend</h3>
              <p class="mb-3 text-xs leading-relaxed text-zinc-500">
                Ключ для отправки и получения писем.
                <a href="https://resend.com/api-keys" target="_blank" class="text-accent-hover hover:underline">Resend Dashboard →</a>
              </p>

              <div
                v-if="hasApiKey && !editingApiKey"
                class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-3"
              >
                <div>
                  <p class="text-xs font-medium text-green-400">Настроено</p>
                  <p class="font-mono text-sm text-zinc-200">{{ apiKeyPreview }}</p>
                </div>
                <button type="button" class="btn-secondary text-xs" @click="editingApiKey = true">
                  Изменить
                </button>
              </div>

              <form v-else class="space-y-2.5" @submit.prevent="saveApiKey">
                <input
                  v-model="apiKey"
                  type="password"
                  class="input-field"
                  placeholder="re_xxxxxxxx"
                  autocomplete="off"
                  autofocus
                />
                <div class="flex gap-2">
                  <button type="submit" class="btn-primary" :disabled="saving">Сохранить</button>
                  <button
                    v-if="hasApiKey"
                    type="button"
                    class="btn-ghost"
                    @click="editingApiKey = false; apiKey = ''"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            </section>

            <section class="rounded-[10px] border border-border bg-surface-elevated p-4">
              <h3 class="mb-1 text-sm font-bold">Webhook signing secret</h3>
              <p class="mb-3 text-xs leading-relaxed text-zinc-500">
                Подпись входящих webhook от Resend (<code class="text-zinc-400">whsec_...</code>).
                <a href="https://resend.com/webhooks" target="_blank" class="text-accent-hover hover:underline">Webhooks →</a>
              </p>

              <div
                v-if="hasWebhookSecret && !editingWebhookSecret"
                class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-3"
              >
                <div>
                  <p class="text-xs font-medium text-green-400">Настроено</p>
                  <p class="font-mono text-sm text-zinc-200">{{ webhookSecretPreview }}</p>
                </div>
                <button type="button" class="btn-secondary text-xs" @click="editingWebhookSecret = true">
                  Изменить
                </button>
              </div>

              <form v-else class="space-y-2.5" @submit.prevent="saveWebhookSecret">
                <input
                  v-model="webhookSecret"
                  type="password"
                  class="input-field"
                  placeholder="whsec_xxxxxxxx"
                  autocomplete="off"
                />
                <div class="flex gap-2">
                  <button type="submit" class="btn-primary" :disabled="saving">Сохранить</button>
                  <button
                    v-if="hasWebhookSecret"
                    type="button"
                    class="btn-ghost"
                    @click="editingWebhookSecret = false; webhookSecret = ''"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            </section>
          </div>

          <!-- Ящики -->
          <div v-show="activeTab === 'mailboxes'" class="space-y-4">
            <p class="text-xs leading-relaxed text-zinc-500">
              Адреса на домене. Входящие фильтруются по полю «Кому».
            </p>

            <div v-if="!mailboxes.length" class="rounded-[10px] border border-dashed border-border px-3 py-8 text-center text-xs text-zinc-500">
              Ящиков пока нет — добавьте ниже
            </div>

            <div v-else class="space-y-2">
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

            <form class="grid grid-cols-1 gap-2 border-t border-border pt-4 sm:grid-cols-[1fr_1fr_auto]" @submit.prevent="addMailbox">
              <input v-model="newName" type="text" class="input-field" placeholder="Имя (Поддержка)" required />
              <input v-model="newEmail" type="email" class="input-field" placeholder="support@domain.com" required />
              <button type="submit" class="btn-secondary whitespace-nowrap" :disabled="saving">+ Добавить</button>
            </form>
          </div>

          <!-- Пользователи -->
          <div v-show="activeTab === 'users'">
            <UsersPanel
              :active="open && activeTab === 'users'"
              :current-user-id="currentUserId"
              @changed="emit('changed')"
              @notify="toast"
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
