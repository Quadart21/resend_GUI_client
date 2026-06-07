<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'
import LoginView from '@/components/LoginView.vue'
import MailboxSidebar from '@/components/MailboxSidebar.vue'
import ThreadPanel from '@/components/ThreadPanel.vue'
import ConversationPanel from '@/components/ConversationPanel.vue'
import ComposeModal from '@/components/ComposeModal.vue'
import SettingsModal from '@/components/SettingsModal.vue'
import UsersModal from '@/components/UsersModal.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const toastRef = ref(null)
const user = ref(null)
const authLoading = ref(true)
const mailboxes = ref([])
const activeMailboxId = ref(null)
const threads = ref([])
const activeThread = ref(null)
const activeThreadId = ref(null)
const loadingThreads = ref(false)
const loadingThread = ref(false)
const composeOpen = ref(false)
const settingsOpen = ref(false)
const usersOpen = ref(false)
const sidebarOpen = ref(false)

const isAdmin = computed(() => Boolean(user.value?.is_admin))

const activeMailbox = computed(() =>
  mailboxes.value.find((b) => b.id === activeMailboxId.value) || null,
)

const threadCounts = computed(() => {
  const counts = {}
  if (activeMailboxId.value && threads.value.length) {
    counts[activeMailboxId.value] = threads.value.length
  }
  return counts
})

const showConversationMobile = computed(
  () => Boolean(activeThreadId.value || loadingThread.value),
)

function notify(msg, type = 'success') {
  toastRef.value?.show(msg, type)
}

async function bootstrapApp() {
  await loadConfig()
  await loadThreads()
}

async function loadConfig() {
  const cfg = await api.getConfig()
  mailboxes.value = cfg.mailboxes || []
  if (!activeMailboxId.value && mailboxes.value.length) {
    activeMailboxId.value = mailboxes.value[0].id
  }
  if (activeMailboxId.value && !mailboxes.value.find((b) => b.id === activeMailboxId.value)) {
    activeMailboxId.value = mailboxes.value[0]?.id || null
  }
}

async function loadThreads() {
  if (!activeMailboxId.value) {
    threads.value = []
    return
  }
  loadingThreads.value = true
  try {
    const data = await api.listThreads(activeMailboxId.value)
    threads.value = data.threads || []
  } catch (err) {
    notify(err.message, 'error')
    threads.value = []
  } finally {
    loadingThreads.value = false
  }
}

async function selectMailbox(id) {
  activeMailboxId.value = id
  activeThreadId.value = null
  activeThread.value = null
  sidebarOpen.value = false
  await loadThreads()
}

async function openThread(threadId) {
  if (!activeMailboxId.value) return

  activeThreadId.value = threadId
  loadingThread.value = true

  const preview = threads.value.find((t) => t.id === threadId)
  activeThread.value = preview ? { ...preview, messages: [] } : null

  try {
    activeThread.value = await api.getThread(activeMailboxId.value, threadId)
  } catch (err) {
    notify(err.message, 'error')
    activeThread.value = null
    activeThreadId.value = null
  } finally {
    loadingThread.value = false
  }
}

function closeConversation() {
  activeThreadId.value = null
  activeThread.value = null
  loadingThread.value = false
}

function openCompose() {
  if (!mailboxes.value.length) {
    notify(isAdmin.value ? 'Сначала добавьте почтовый ящик в настройках' : 'Нет доступных ящиков', 'error')
    if (isAdmin.value) settingsOpen.value = true
    return
  }
  composeOpen.value = true
}

async function handleSend(payload) {
  try {
    await api.sendEmail(payload)
    notify('Письмо отправлено')
    composeOpen.value = false
    await loadThreads()
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function handleReply(body) {
  if (!activeMailboxId.value || !activeThreadId.value) return
  try {
    await api.replyThread(activeMailboxId.value, activeThreadId.value, {
      mailbox_id: activeMailboxId.value,
      html: `<p>${FormatHelper.escapeHtml(body).replace(/\n/g, '<br>')}</p>`,
      text: body,
    })
    notify('Ответ отправлен')
    await openThread(activeThreadId.value)
    await loadThreads()
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function onSettingsChanged() {
  notify('Настройки сохранены')
  await loadConfig()
  await loadThreads()
}

async function onLogin(loggedInUser) {
  user.value = loggedInUser
  await bootstrapApp()
}

async function logout() {
  try {
    await api.logout()
  } catch {
    /* cookie всё равно сбросится на клиенте */
  }
  user.value = null
  mailboxes.value = []
  threads.value = []
  activeMailboxId.value = null
  activeThreadId.value = null
  activeThread.value = null
}

function openAdminPanel() {
  if (isAdmin.value) settingsOpen.value = true
}

function openUsersPanel() {
  if (isAdmin.value) usersOpen.value = true
}

onMounted(async () => {
  try {
    const data = await api.me()
    user.value = data.user
    await bootstrapApp()
  } catch {
    user.value = null
  } finally {
    authLoading.value = false
  }
})
</script>

<template>
  <div v-if="authLoading" class="grid h-[100dvh] place-items-center bg-[#09090b] text-zinc-500">
    <div class="h-8 w-8 animate-spin rounded-full border-[3px] border-border border-t-accent" />
  </div>

  <LoginView v-else-if="!user" @login="onLogin" />

  <template v-else>
    <div class="flex h-[100dvh] overflow-hidden">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-40 bg-black/60 md:hidden"
        aria-hidden="true"
        @click="sidebarOpen = false"
      />

      <MailboxSidebar
        class="fixed inset-y-0 left-0 z-50 w-[min(18rem,88vw)] transition-transform duration-200 ease-out md:static md:z-auto md:w-60 md:translate-x-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
        :mailboxes="mailboxes"
        :active-id="activeMailboxId"
        :thread-counts="threadCounts"
        :is-admin="isAdmin"
        :username="user.username"
        @select="selectMailbox"
        @compose="openCompose"
        @add="settingsOpen = true"
        @settings="openAdminPanel"
        @users="openUsersPanel"
        @logout="logout"
        @close="sidebarOpen = false"
      />

      <ThreadPanel
        class="panel w-full shrink-0 md:w-[340px]"
        :class="showConversationMobile ? 'hidden md:flex' : 'flex'"
        :threads="threads"
        :active-mailbox="activeMailbox"
        :active-thread-id="activeThreadId"
        :loading="loadingThreads"
        :is-admin="isAdmin"
        @select="openThread"
        @refresh="loadThreads"
        @menu="sidebarOpen = true"
        @compose="openCompose"
        @settings="openAdminPanel"
        @logout="logout"
      />

      <ConversationPanel
        class="min-w-0 flex-1 flex-col overflow-hidden"
        :class="showConversationMobile ? 'fixed inset-0 z-30 flex md:static md:z-auto' : 'hidden md:flex'"
        :thread="activeThread"
        :mailbox="activeMailbox"
        :loading="loadingThread"
        @reply="handleReply"
        @back="closeConversation"
      />

      <button
        v-if="!showConversationMobile && mailboxes.length"
        type="button"
        class="fixed bottom-5 right-5 z-20 grid h-14 w-14 place-items-center rounded-full bg-accent text-white shadow-lg shadow-accent/30 transition active:scale-95 md:hidden"
        style="margin-bottom: env(safe-area-inset-bottom); margin-right: env(safe-area-inset-right);"
        title="Написать"
        @click="openCompose"
      >
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </div>

    <ComposeModal
      :open="composeOpen"
      :mailboxes="mailboxes"
      :active-mailbox-id="activeMailboxId"
      @close="composeOpen = false"
      @send="handleSend"
    />

    <SettingsModal
      v-if="isAdmin"
      :open="settingsOpen"
      @close="settingsOpen = false"
      @changed="onSettingsChanged"
      @open-users="usersOpen = true"
    />

    <UsersModal
      v-if="isAdmin"
      :open="usersOpen"
      :mailboxes="mailboxes"
      :current-user-id="user.id"
      @close="usersOpen = false"
      @changed="onSettingsChanged"
    />
  </template>

  <ToastContainer ref="toastRef" />
</template>
