<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'
import { HtmlHelper } from '@/services/HtmlHelper'
import { NotificationWatcher } from '@/services/NotificationWatcher'
import LoginView from '@/components/LoginView.vue'
import MailboxSidebar from '@/components/MailboxSidebar.vue'
import ThreadPanel from '@/components/ThreadPanel.vue'
import ConversationPanel from '@/components/ConversationPanel.vue'
import ComposeModal from '@/components/ComposeModal.vue'
import SettingsModal from '@/components/SettingsModal.vue'
import ProfileModal from '@/components/ProfileModal.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const toastRef = ref(null)
const user = ref(null)
const authLoading = ref(true)
const mailboxes = ref([])
const activeMailboxId = ref(null)
const threads = ref([])
const unreadTotal = ref(0)
const unreadCounts = ref({})
const emailLimit = ref(500)
const hasMoreThreads = ref(false)
const activeThread = ref(null)
const activeThreadId = ref(null)
const loadingThreads = ref(false)
const loadingThread = ref(false)
const composeOpen = ref(false)
const settingsOpen = ref(false)
const profileOpen = ref(false)
const settingsInitialTab = ref('integration')
const sidebarOpen = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const notificationsOn = ref(localStorage.getItem('resend_notifications_enabled') === '1')

let notificationWatcher = null
let refreshTimer = null
let searchTimer = null
const REFRESH_DB_MS = 15_000
const REFRESH_SYNC_MS = 60_000

const isAdmin = computed(() => Boolean(user.value?.is_admin))

const activeMailbox = computed(() =>
  mailboxes.value.find((b) => b.id === activeMailboxId.value) || null,
)

const threadCounts = computed(() => unreadCounts.value)

const showConversationMobile = computed(
  () => Boolean(activeThreadId.value || loadingThread.value),
)

const isGlobalSearch = computed(() => searchQuery.value.trim().length >= 2)

const displayedThreads = computed(() =>
  isGlobalSearch.value ? searchResults.value : threads.value,
)

watch(searchQuery, (value) => {
  clearTimeout(searchTimer)
  const q = value.trim()
  if (q.length < 2) {
    searchResults.value = []
    searching.value = false
    return
  }
  searchTimer = setTimeout(async () => {
    searching.value = true
    try {
      const data = await api.searchThreads(q)
      searchResults.value = data.threads || []
    } catch (err) {
      searchResults.value = []
      if (!loadingThreads.value) notify(err.message, 'error')
    } finally {
      searching.value = false
    }
  }, 300)
})

function notify(msg, type = 'success') {
  toastRef.value?.show(msg, type)
}

async function bootstrapApp() {
  await loadConfig()
  await Promise.all([loadThreads(), loadUnreadCounts()])
}

function clearUnreadLocally(threadId = null) {
  if (threadId) {
    threads.value = threads.value.map((t) =>
      t.id === threadId ? { ...t, is_unread: false, unread_count: 0 } : t,
    )
    unreadTotal.value = threads.value.filter((t) => t.is_unread).length
  } else {
    threads.value = threads.value.map((t) => ({ ...t, is_unread: false, unread_count: 0 }))
    unreadTotal.value = 0
  }
  if (activeMailboxId.value) {
    unreadCounts.value = {
      ...unreadCounts.value,
      [activeMailboxId.value]: unreadTotal.value,
    }
  }
}

async function markThreadRead(threadId) {
  if (!activeMailboxId.value || !threadId) return
  try {
    await api.markThreadRead(activeMailboxId.value, threadId)
    clearUnreadLocally(threadId)
    await loadUnreadCounts()
  } catch {
    /* не мешаем просмотру */
  }
}

async function markAllRead() {
  if (!activeMailboxId.value || !unreadTotal.value) return
  try {
    await api.markAllThreadsRead(activeMailboxId.value)
    clearUnreadLocally()
    await loadUnreadCounts()
    notify('Все переписки прочитаны')
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function loadConfig() {
  const cfg = await api.getConfig()
  if (isAdmin.value) {
    try {
      const boxes = await api.listMailboxes()
      mailboxes.value = boxes.mailboxes || []
    } catch {
      mailboxes.value = cfg.mailboxes || []
    }
  } else {
    mailboxes.value = cfg.mailboxes || []
  }
  if (!activeMailboxId.value && mailboxes.value.length) {
    activeMailboxId.value = mailboxes.value[0].id
  }
  if (activeMailboxId.value && !mailboxes.value.find((b) => b.id === activeMailboxId.value)) {
    activeMailboxId.value = mailboxes.value[0]?.id || null
  }
}

async function loadUnreadCounts() {
  try {
    const data = await api.unreadCounts()
    unreadCounts.value = data.counts || {}
  } catch {
    /* не блокируем UI */
  }
}

async function loadThreads(sync = false, silent = false, resetLimit = false) {
  if (!activeMailboxId.value) {
    threads.value = []
    unreadTotal.value = 0
    hasMoreThreads.value = false
    return
  }
  if (resetLimit) emailLimit.value = 500
  if (!silent) loadingThreads.value = true
  try {
    const data = await api.listThreads(activeMailboxId.value, sync, emailLimit.value)
    threads.value = data.threads || []
    unreadTotal.value = data.unread_total ?? threads.value.filter((t) => t.is_unread).length
    hasMoreThreads.value = Boolean(data.has_more)
    if (data.email_limit) emailLimit.value = data.email_limit
    if (activeMailboxId.value) {
      unreadCounts.value = {
        ...unreadCounts.value,
        [activeMailboxId.value]: unreadTotal.value,
      }
    }
    if (silent && activeThreadId.value) {
      const current = threads.value.find((t) => t.id === activeThreadId.value)
      if (current?.is_unread) {
        markThreadRead(activeThreadId.value)
      }
    }
  } catch (err) {
    if (!silent) notify(err.message, 'error')
    threads.value = []
    unreadTotal.value = 0
  } finally {
    if (!silent) loadingThreads.value = false
  }
}

async function refreshThreads() {
  await loadThreads(true, false, false)
}

async function loadMoreThreads() {
  if (!hasMoreThreads.value || loadingThreads.value) return
  emailLimit.value = Math.min(emailLimit.value + 500, 5000)
  await loadThreads(false, false, false)
}

async function selectMailbox(id) {
  activeMailboxId.value = id
  activeThreadId.value = null
  activeThread.value = null
  sidebarOpen.value = false
  await loadThreads(false, false, true)
}

async function openThread(threadId, mailboxId = null) {
  const targetMailbox = mailboxId || activeMailboxId.value
  if (!targetMailbox) return

  if (targetMailbox !== activeMailboxId.value) {
    activeMailboxId.value = targetMailbox
    await loadThreads(false, true, false)
  }

  activeThreadId.value = threadId
  loadingThread.value = true

  const sourceList = isGlobalSearch.value ? searchResults.value : threads.value
  const preview = sourceList.find((t) => t.id === threadId)
  activeThread.value = preview ? { ...preview, messages: [] } : null

  try {
    activeThread.value = await api.getThread(targetMailbox, threadId)
    await markThreadRead(threadId)
    if (activeThread.value?.messages) {
      activeThread.value = {
        ...activeThread.value,
        is_unread: false,
        unread_count: 0,
        messages: activeThread.value.messages.map((m) => ({ ...m, is_unread: false })),
      }
    }
    const patchUnread = (list) =>
      list.map((t) => (t.id === threadId ? { ...t, is_unread: false, unread_count: 0 } : t))
    threads.value = patchUnread(threads.value)
    searchResults.value = patchUnread(searchResults.value)
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

function openProfile() {
  profileOpen.value = true
  sidebarOpen.value = false
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

async function handleReply(payload) {
  if (!activeMailboxId.value || !activeThreadId.value) return
  const text = typeof payload === 'string' ? payload : (payload.text || '')
  const htmlRaw = typeof payload === 'object' ? (payload.html || '') : ''
  const attachments = typeof payload === 'object' ? (payload.attachments || []) : []
  const hasHtml = htmlRaw && !HtmlHelper.isEmpty(htmlRaw)
  const hasText = text.trim().length > 0
  if (!hasHtml && !hasText && !attachments.length) return

  const html = hasHtml
    ? HtmlHelper.sanitize(htmlRaw)
    : (hasText ? `<p>${FormatHelper.escapeHtml(text).replace(/\n/g, '<br>')}</p>` : '<p></p>')

  try {
    await api.replyThread(activeMailboxId.value, activeThreadId.value, {
      mailbox_id: activeMailboxId.value,
      html,
      text: hasText ? text : HtmlHelper.toPlainText(html),
      attachments,
    })
    notify('Ответ отправлен')
    await openThread(activeThreadId.value)
    await loadThreads()
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function toggleThreadStar(threadId, starred, mailboxId = null) {
  const targetMailbox = mailboxId || activeMailboxId.value
  if (!targetMailbox) return
  try {
    await api.starThread(targetMailbox, threadId, starred)
    const patch = (list) =>
      list.map((t) => (t.id === threadId ? { ...t, is_starred: starred } : t))
    threads.value = patch(threads.value)
    searchResults.value = patch(searchResults.value)
    if (activeThread.value?.id === threadId) {
      activeThread.value = { ...activeThread.value, is_starred: starred }
    }
    if (!isGlobalSearch.value && targetMailbox === activeMailboxId.value) {
      await loadThreads(false, true)
    }
    notify(starred ? 'Переписка в важных' : 'Убрано из важных')
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function toggleMessageStar(emailId, starred) {
  if (!activeMailboxId.value) return
  try {
    await api.starEmail(activeMailboxId.value, emailId, starred)
    if (activeThread.value?.messages) {
      activeThread.value = {
        ...activeThread.value,
        messages: activeThread.value.messages.map((m) =>
          m.id === emailId ? { ...m, is_starred: starred } : m,
        ),
      }
    }
    await loadThreads(false, true)
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function deleteMessage(emailId) {
  if (!activeMailboxId.value) return
  if (!confirm('Удалить это сообщение? Оно скроется только у вас.')) return
  try {
    await api.deleteEmail(activeMailboxId.value, emailId)
    if (activeThread.value?.messages) {
      const remaining = activeThread.value.messages.filter((m) => m.id !== emailId)
      if (!remaining.length) {
        closeConversation()
      } else {
        activeThread.value = {
          ...activeThread.value,
          messages: remaining,
          message_count: remaining.length,
        }
      }
    }
    await loadThreads(false, true)
    notify('Сообщение удалено')
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
  initNotifications()
  startAutoRefresh()
}

function startAutoRefresh() {
  stopAutoRefresh()
  let syncCounter = 0
  refreshTimer = setInterval(async () => {
    if (!user.value || !activeMailboxId.value) return
    syncCounter += REFRESH_DB_MS
    const withSync = syncCounter >= REFRESH_SYNC_MS
    if (withSync) syncCounter = 0
    await loadThreads(withSync, true)
  }, REFRESH_DB_MS)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function initNotifications() {
  if (!NotificationWatcher.isSupported()) return

  notificationWatcher = new NotificationWatcher(api, {
    onNewMail: () => loadThreads(false),
    onError: () => {},
  })

  notificationsOn.value = notificationWatcher.isEnabled()
  if (notificationsOn.value) {
    notificationWatcher.start()
  }
}

async function toggleNotifications() {
  if (!notificationWatcher) {
    initNotifications()
  }
  if (!notificationWatcher) {
    notify('Браузер не поддерживает уведомления', 'error')
    return
  }

  if (notificationsOn.value) {
    notificationWatcher.disable()
    notificationsOn.value = false
    notify('Уведомления отключены')
    return
  }

  try {
    await notificationWatcher.enable()
    notificationsOn.value = true
    notify('Уведомления включены')
  } catch (err) {
    notify(err.message, 'error')
  }
}

async function logout() {
  notificationWatcher?.stop()
  stopAutoRefresh()
  notificationsOn.value = false
  try {
    await api.logout()
  } catch {
    /* cookie всё равно сбросится на клиенте */
  }
  user.value = null
  mailboxes.value = []
  threads.value = []
  unreadCounts.value = {}
  unreadTotal.value = 0
  activeMailboxId.value = null
  activeThreadId.value = null
  activeThread.value = null
}

function openAdminPanel() {
  if (!isAdmin.value) return
  settingsInitialTab.value = 'integration'
  settingsOpen.value = true
}

function openUsersPanel() {
  if (!isAdmin.value) return
  settingsInitialTab.value = 'users'
  settingsOpen.value = true
}

onMounted(async () => {
  try {
    const data = await api.me()
    user.value = data.user
    await bootstrapApp()
    initNotifications()
    startAutoRefresh()
  } catch {
    user.value = null
  } finally {
    authLoading.value = false
  }
})

onUnmounted(() => {
  notificationWatcher?.stop()
  stopAutoRefresh()
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
        :notifications-on="notificationsOn"
        @select="selectMailbox"
        @compose="openCompose"
        @add="settingsOpen = true"
        @settings="openAdminPanel"
        @users="openUsersPanel"
        @profile="openProfile"
        @logout="logout"
        @toggle-notifications="toggleNotifications"
        @close="sidebarOpen = false"
      />

      <ThreadPanel
        class="panel w-full shrink-0 md:w-[340px]"
        :class="showConversationMobile ? 'hidden md:flex' : 'flex'"
        v-model:search-query="searchQuery"
        :threads="displayedThreads"
        :active-mailbox="activeMailbox"
        :active-thread-id="activeThreadId"
        :loading="loadingThreads"
        :searching="searching"
        :show-mailbox="isGlobalSearch"
        :unread-total="unreadTotal"
        :has-more="hasMoreThreads"
        :loading-more="loadingThreads && emailLimit > 500"
        :is-admin="isAdmin"
        :notifications-on="notificationsOn"
        @select="openThread"
        @refresh="refreshThreads"
        @load-more="loadMoreThreads"
        @mark-all-read="markAllRead"
        @star-thread="toggleThreadStar"
        @menu="sidebarOpen = true"
        @compose="openCompose"
        @settings="openAdminPanel"
        @profile="openProfile"
        @logout="logout"
        @toggle-notifications="toggleNotifications"
      />

      <ConversationPanel
        class="min-w-0 flex-1 flex-col overflow-hidden"
        :class="showConversationMobile ? 'fixed inset-0 z-30 flex md:static md:z-auto' : 'hidden md:flex'"
        :thread="activeThread"
        :mailbox="activeMailbox"
        :loading="loadingThread"
        @reply="handleReply"
        @back="closeConversation"
        @star-thread="toggleThreadStar"
        @star-message="toggleMessageStar"
        @delete-message="deleteMessage"
        @notify="notify"
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
      @notify="notify"
    />

    <ProfileModal
      :open="profileOpen"
      @close="profileOpen = false"
      @notify="notify"
    />

    <SettingsModal
      v-if="isAdmin"
      :open="settingsOpen"
      :initial-tab="settingsInitialTab"
      :current-user-id="user.id"
      @close="settingsOpen = false"
      @changed="onSettingsChanged"
      @notify="notify"
    />
  </template>

  <ToastContainer ref="toastRef" />
</template>
