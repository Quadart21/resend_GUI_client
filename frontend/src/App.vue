<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/ApiClient'
import { FormatHelper } from '@/services/FormatHelper'
import MailboxSidebar from '@/components/MailboxSidebar.vue'
import ThreadPanel from '@/components/ThreadPanel.vue'
import ConversationPanel from '@/components/ConversationPanel.vue'
import ComposeModal from '@/components/ComposeModal.vue'
import SettingsModal from '@/components/SettingsModal.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const toastRef = ref(null)
const mailboxes = ref([])
const activeMailboxId = ref(null)
const threads = ref([])
const activeThread = ref(null)
const activeThreadId = ref(null)
const loadingThreads = ref(false)
const loadingThread = ref(false)
const composeOpen = ref(false)
const settingsOpen = ref(false)

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

function notify(msg, type = 'success') {
  toastRef.value?.show(msg, type)
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
  await loadThreads()
}

async function openThread(threadId) {
  if (!activeMailboxId.value) return

  activeThreadId.value = threadId
  loadingThread.value = true

  // Сразу показываем заголовок из списка, пока грузится тело
  const preview = threads.value.find((t) => t.id === threadId)
  activeThread.value = preview
    ? { ...preview, messages: [] }
    : null

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

function openCompose() {
  if (!mailboxes.value.length) {
    notify('Сначала добавьте почтовый ящик в настройках', 'error')
    settingsOpen.value = true
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

onMounted(async () => {
  try {
    await loadConfig()
    await loadThreads()
  } catch (err) {
    notify(err.message, 'error')
  }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <MailboxSidebar
      :mailboxes="mailboxes"
      :active-id="activeMailboxId"
      :thread-counts="threadCounts"
      @select="selectMailbox"
      @compose="openCompose"
      @add="settingsOpen = true"
      @settings="settingsOpen = true"
    />

    <ThreadPanel
      :threads="threads"
      :active-mailbox="activeMailbox"
      :active-thread-id="activeThreadId"
      :loading="loadingThreads"
      @select="openThread"
      @refresh="loadThreads"
    />

    <ConversationPanel
      :thread="activeThread"
      :mailbox="activeMailbox"
      :loading="loadingThread"
      @reply="handleReply"
    />
  </div>

  <ComposeModal
    :open="composeOpen"
    :mailboxes="mailboxes"
    :active-mailbox-id="activeMailboxId"
    @close="composeOpen = false"
    @send="handleSend"
  />

  <SettingsModal
    :open="settingsOpen"
    @close="settingsOpen = false"
    @changed="onSettingsChanged"
  />

  <ToastContainer ref="toastRef" />
</template>
