<script setup>
import { ref, watch, computed } from 'vue'
import { api } from '@/services/ApiClient'

const props = defineProps({
  open: { type: Boolean, default: false },
  currentUserId: { type: String, default: null },
})

const emit = defineEmits(['close', 'changed', 'notify'])

const users = ref([])
const mailboxes = ref([])
const loading = ref(false)
const saving = ref(false)
const newUsername = ref('')
const newIsAdmin = ref(false)
const newMailboxIds = ref([])
const credentials = ref(null)

const loginUrl = computed(() => window.location.origin)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) load()
    else credentials.value = null
  },
)

async function load() {
  loading.value = true
  try {
    const [usersData, boxesData] = await Promise.all([
      api.listUsers(),
      api.listMailboxes(),
    ])
    users.value = usersData.users || []
    mailboxes.value = boxesData.mailboxes || []
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    loading.value = false
  }
}

function showCredentials(data) {
  if (!data?.credentials) return
  credentials.value = {
    username: data.credentials.username,
    password: data.credentials.password,
    loginUrl: loginUrl.value,
  }
}

async function copyText(text, label) {
  try {
    await navigator.clipboard.writeText(text)
    emit('notify', `${label} скопирован`)
  } catch {
    emit('notify', 'Не удалось скопировать', 'error')
  }
}

async function copyAllCredentials() {
  if (!credentials.value) return
  const block = [
    `Ссылка: ${credentials.value.loginUrl}`,
    `Логин: ${credentials.value.username}`,
    `Пароль: ${credentials.value.password}`,
  ].join('\n')
  await copyText(block, 'Данные для входа')
}

async function createUser() {
  saving.value = true
  try {
    const data = await api.createUser({
      username: newUsername.value.trim(),
      is_admin: newIsAdmin.value,
      mailbox_ids: newIsAdmin.value ? [] : [...newMailboxIds.value],
    })
    newUsername.value = ''
    newIsAdmin.value = false
    newMailboxIds.value = []
    showCredentials(data)
    await load()
    emit('changed')
    emit('notify', 'Пользователь создан')
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    saving.value = false
  }
}

async function regeneratePassword(user) {
  if (!confirm(`Сгенерировать новый пароль для «${user.username}»? Старый перестанет работать.`)) return
  saving.value = true
  try {
    const data = await api.regenerateUserPassword(user.id)
    showCredentials(data)
    emit('notify', 'Новый пароль сгенерирован')
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    saving.value = false
  }
}

async function toggleActive(user) {
  try {
    await api.updateUser(user.id, { is_active: !user.is_active })
    await load()
    emit('changed')
  } catch (err) {
    emit('notify', err.message, 'error')
  }
}

async function deleteUser(user) {
  if (!confirm(`Удалить пользователя «${user.username}»?`)) return
  try {
    await api.deleteUser(user.id)
    if (credentials.value?.username === user.username) credentials.value = null
    await load()
    emit('changed')
  } catch (err) {
    emit('notify', err.message, 'error')
  }
}

function toggleMailbox(user, mailboxId) {
  const ids = new Set(user.mailbox_ids || [])
  if (ids.has(mailboxId)) ids.delete(mailboxId)
  else ids.add(mailboxId)
  saveMailboxes(user, [...ids])
}

async function saveMailboxes(user, mailboxIds) {
  try {
    await api.updateUser(user.id, { mailbox_ids: mailboxIds })
    await load()
    emit('changed')
  } catch (err) {
    emit('notify', err.message, 'error')
  }
}

function mailboxLabel(id) {
  const box = mailboxes.value.find((b) => b.id === id)
  return box ? (box.name || box.email) : id
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[1000] flex items-end justify-center bg-black/65 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[100dvh] w-full flex-col overflow-hidden border-border bg-surface shadow-2xl sm:max-h-[90vh] sm:max-w-2xl sm:rounded-[14px] sm:border">
        <header class="flex shrink-0 items-center justify-between border-b border-border px-4 py-4 sm:px-6">
          <h2 class="text-[17px] font-bold">Пользователи</h2>
          <button type="button" class="btn-icon" @click="emit('close')">✕</button>
        </header>

        <div class="flex-1 space-y-6 overflow-y-auto p-4 sm:p-6" style="padding-bottom: max(1rem, env(safe-area-inset-bottom));">
          <!-- Данные для входа (показываются один раз после создания/сброса) -->
          <section
            v-if="credentials"
            class="rounded-[10px] border border-amber-500/40 bg-amber-500/10 p-4"
          >
            <div class="mb-3 flex items-start justify-between gap-2">
              <div>
                <h3 class="text-sm font-bold text-amber-200">Данные для входа</h3>
                <p class="mt-1 text-xs text-amber-200/70">
                  Сохраните сейчас — пароль больше не будет показан
                </p>
              </div>
              <button type="button" class="btn-ghost text-xs" @click="credentials = null">✕</button>
            </div>

            <dl class="space-y-2.5 text-sm">
              <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-black/20 px-3 py-2">
                <div>
                  <dt class="text-[10px] uppercase tracking-wide text-zinc-500">Ссылка</dt>
                  <dd class="font-mono text-xs text-zinc-200">{{ credentials.loginUrl }}</dd>
                </div>
                <button type="button" class="btn-secondary px-2 py-1 text-xs" @click="copyText(credentials.loginUrl, 'Ссылка')">
                  Копировать
                </button>
              </div>
              <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-black/20 px-3 py-2">
                <div>
                  <dt class="text-[10px] uppercase tracking-wide text-zinc-500">Логин</dt>
                  <dd class="font-mono text-zinc-100">{{ credentials.username }}</dd>
                </div>
                <button type="button" class="btn-secondary px-2 py-1 text-xs" @click="copyText(credentials.username, 'Логин')">
                  Копировать
                </button>
              </div>
              <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-black/20 px-3 py-2">
                <div>
                  <dt class="text-[10px] uppercase tracking-wide text-zinc-500">Пароль</dt>
                  <dd class="font-mono text-lg font-bold tracking-wide text-zinc-50">{{ credentials.password }}</dd>
                </div>
                <button type="button" class="btn-secondary px-2 py-1 text-xs" @click="copyText(credentials.password, 'Пароль')">
                  Копировать
                </button>
              </div>
            </dl>

            <button type="button" class="btn-primary mt-3 w-full sm:w-auto" @click="copyAllCredentials">
              Копировать всё
            </button>
          </section>

          <div v-if="loading" class="py-8 text-center text-sm text-zinc-500">Загрузка...</div>

          <template v-else>
            <section
              v-for="user in users"
              :key="user.id"
              class="rounded-[10px] border border-border bg-surface-elevated p-4"
            >
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <span class="text-sm font-bold">{{ user.username }}</span>
                <span
                  v-if="user.is_admin"
                  class="rounded bg-accent/20 px-2 py-0.5 text-[10px] font-semibold text-accent-hover"
                >
                  админ
                </span>
                <span
                  class="rounded px-2 py-0.5 text-[10px] font-semibold"
                  :class="user.is_active ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'"
                >
                  {{ user.is_active ? 'активен' : 'отключён' }}
                </span>
                <div class="ml-auto flex flex-wrap gap-2">
                  <button
                    v-if="user.id !== currentUserId"
                    type="button"
                    class="text-xs text-accent-hover hover:underline"
                    @click="regeneratePassword(user)"
                  >
                    Новый пароль
                  </button>
                  <button
                    v-if="user.id !== currentUserId"
                    type="button"
                    class="text-xs text-zinc-400 hover:text-zinc-200"
                    @click="toggleActive(user)"
                  >
                    {{ user.is_active ? 'Отключить' : 'Включить' }}
                  </button>
                  <button
                    v-if="user.id !== currentUserId"
                    type="button"
                    class="text-xs text-red-400 hover:underline"
                    @click="deleteUser(user)"
                  >
                    Удалить
                  </button>
                </div>
              </div>

              <div v-if="!user.is_admin" class="space-y-2">
                <p class="text-xs text-zinc-500">Доступ к ящикам:</p>
                <div v-if="!mailboxes.length" class="text-xs text-amber-400/90">
                  Ящиков нет — добавьте в Настройках → Почтовые ящики
                </div>
                <label
                  v-for="box in mailboxes"
                  :key="box.id"
                  class="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 hover:bg-surface-hover"
                >
                  <input
                    type="checkbox"
                    class="accent-accent"
                    :checked="user.mailbox_ids?.includes(box.id)"
                    @change="toggleMailbox(user, box.id)"
                  />
                  <span class="text-sm">{{ box.name || box.email }}</span>
                  <span class="text-xs text-zinc-500">{{ box.email }}</span>
                </label>
              </div>
              <p v-else class="text-xs text-zinc-500">Администратор имеет доступ ко всем ящикам</p>
            </section>

            <section class="rounded-[10px] border border-dashed border-border-light p-4">
              <h3 class="mb-1 text-sm font-bold">Новый пользователь</h3>
              <p class="mb-3 text-xs text-zinc-500">Пароль сгенерируется автоматически</p>
              <form class="space-y-3" @submit.prevent="createUser">
                <input v-model="newUsername" type="text" class="input-field" placeholder="Логин" required />

                <label class="flex items-center gap-2 text-sm text-zinc-300">
                  <input v-model="newIsAdmin" type="checkbox" class="accent-accent" />
                  Администратор
                </label>

                <div v-if="!newIsAdmin && mailboxes.length" class="space-y-1">
                  <p class="text-xs text-zinc-500">Ящики при создании:</p>
                  <label
                    v-for="box in mailboxes"
                    :key="box.id"
                    class="flex items-center gap-2 text-sm"
                  >
                    <input v-model="newMailboxIds" type="checkbox" class="accent-accent" :value="box.id" />
                    {{ mailboxLabel(box.id) }}
                  </label>
                </div>

                <button type="submit" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Создание...' : 'Создать пользователя' }}
                </button>
              </form>
            </section>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>
