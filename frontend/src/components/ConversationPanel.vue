<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'
import { HtmlHelper } from '@/services/HtmlHelper'
import { AttachmentHelper } from '@/services/AttachmentHelper'
import { api } from '@/services/ApiClient'
import RichTextEditor from '@/components/RichTextEditor.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import UiAvatar from '@/components/ui/UiAvatar.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'

const props = defineProps({
  thread: { type: Object, default: null },
  mailbox: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  listVisible: { type: Boolean, default: true },
})

const emit = defineEmits([
  'reply',
  'back',
  'star-thread',
  'star-message',
  'delete-message',
  'notify',
  'toggle-list',
  'toggle-focus',
])

const scrollEl = ref(null)
const replyBody = ref('')
const replyAttachments = ref([])
const pickingFiles = ref(false)
const replyFileInput = ref(null)
const composerExpanded = ref(false)
const expandedMessages = ref(new Set())

const limits = AttachmentHelper.limits

const sortedMessages = computed(() => {
  if (!props.thread?.messages?.length) return []
  return [...props.thread.messages].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at),
  )
})

function resetExpanded() {
  const msgs = sortedMessages.value
  expandedMessages.value = msgs.length ? new Set([msgs[msgs.length - 1].id]) : new Set()
}

function isExpanded(msgId) {
  return expandedMessages.value.has(msgId)
}

function toggleMessage(msgId) {
  const next = new Set(expandedMessages.value)
  if (next.has(msgId)) next.delete(msgId)
  else next.add(msgId)
  expandedMessages.value = next
}

function expandAll() {
  expandedMessages.value = new Set(sortedMessages.value.map((m) => m.id))
}

watch(
  () => [props.thread?.id, props.loading],
  async () => {
    replyBody.value = ''
    replyAttachments.value = []
    composerExpanded.value = false
    resetExpanded()
    await nextTick()
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  },
)

watch(sortedMessages, () => {
  if (!expandedMessages.value.size && sortedMessages.value.length) {
    resetExpanded()
  }
})

function sendReply() {
  const htmlRaw = replyBody.value
  const text = HtmlHelper.toPlainText(htmlRaw)
  const hasBody = !HtmlHelper.isEmpty(htmlRaw)
  const hasFiles = replyAttachments.value.length > 0
  if (!hasBody && !hasFiles) return
  emit('reply', {
    html: hasBody ? HtmlHelper.sanitize(htmlRaw) : '',
    text,
    attachments: AttachmentHelper.toPayload(replyAttachments.value),
  })
  replyBody.value = ''
  replyAttachments.value = []
  composerExpanded.value = false
}

async function onReplyFilesSelected(event) {
  const input = event.target
  pickingFiles.value = true
  try {
    const items = await AttachmentHelper.readFiles(input.files)
    replyAttachments.value = [...replyAttachments.value, ...items].slice(0, limits.maxFiles)
    composerExpanded.value = true
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    pickingFiles.value = false
    if (input) input.value = ''
  }
}

function removeReplyAttachment(index) {
  replyAttachments.value = replyAttachments.value.filter((_, i) => i !== index)
}

function attachmentHref(emailId, attachmentId) {
  if (!props.mailbox?.id) return '#'
  return api.attachmentUrl(props.mailbox.id, emailId, attachmentId)
}

function dateLabel(iso, index) {
  if (!iso) return null
  const d = new Date(iso)
  const prev = sortedMessages.value[index - 1]
  if (prev) {
    const pd = new Date(prev.created_at)
    if (d.toDateString() === pd.toDateString()) return null
  }
  return d.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
}

function toggleThreadStar() {
  if (!props.thread) return
  emit('star-thread', props.thread.id, !props.thread.is_starred)
}

function previewText(msg) {
  if (msg.text?.trim()) return msg.text.trim().slice(0, 140)
  if (msg.html) return HtmlHelper.toPlainText(msg.html).slice(0, 140)
  return 'Содержимое недоступно'
}
</script>

<template>
  <section class="reading-pane">
    <UiEmptyState
      v-if="!thread && !loading"
      class="hidden flex-1 md:flex"
      title="Выберите переписку"
      description="Откройте письмо из списка — здесь будет полноэкранный просмотр"
      icon="mail"
    />

    <template v-else-if="thread || loading">
      <header class="panel-header sticky top-0 z-10" style="padding-top: max(0.75rem, env(safe-area-inset-top));">
        <div class="mx-auto flex max-w-5xl items-start gap-2 xl:max-w-6xl">
          <button type="button" class="btn-icon btn-icon-ghost md:hidden" aria-label="Назад" @click="emit('back')">
            <AppIcon name="back" />
          </button>

          <button
            type="button"
            class="btn-icon btn-icon-ghost hidden md:inline-flex"
            :title="listVisible ? 'Скрыть список' : 'Показать список'"
            @click="emit('toggle-list')"
          >
            <AppIcon name="menu" />
          </button>

          <div class="min-w-0 flex-1">
            <div class="flex items-start gap-2">
              <h2 class="line-clamp-2 flex-1 text-lg font-bold tracking-tight md:line-clamp-1 md:text-xl">
                {{ thread?.subject || '(без темы)' }}
              </h2>
              <button
                type="button"
                class="btn-icon btn-icon-ghost shrink-0"
                :class="thread?.is_starred ? 'text-warning' : ''"
                :disabled="loading || !thread"
                @click="toggleThreadStar"
              >
                <AppIcon name="star" :filled="thread?.is_starred" />
              </button>
            </div>
            <div v-if="thread" class="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
              <span>{{ thread.message_count || sortedMessages.length }} сообщ.</span>
              <span v-if="thread.correspondent">· {{ thread.correspondent }}</span>
              <UiBadge v-if="thread.is_starred" variant="warning">важное</UiBadge>
              <button
                v-if="sortedMessages.length > 1"
                type="button"
                class="btn-ghost px-2 py-0.5 text-[11px]"
                @click="expandAll"
              >
                Развернуть все
              </button>
            </div>
          </div>

          <button
            type="button"
            class="btn-icon btn-icon-ghost hidden lg:inline-flex"
            title="Режим чтения"
            @click="emit('toggle-focus')"
          >
            <AppIcon name="focus" />
          </button>
        </div>
      </header>

      <div ref="scrollEl" class="relative flex-1 overflow-y-auto overscroll-contain px-4 py-5 sm:px-8 md:px-10">
        <div
          v-if="loading"
          class="absolute inset-0 z-10 flex items-center justify-center bg-canvas/80 backdrop-blur-[2px]"
        >
          <UiSpinner label="Загрузка переписки..." />
        </div>

        <div class="mx-auto flex w-full max-w-5xl flex-col gap-3 xl:max-w-6xl">
          <template v-for="(msg, index) in sortedMessages" :key="msg.id">
            <div v-if="dateLabel(msg.created_at, index)" class="flex items-center gap-3 py-2">
              <div class="h-px flex-1 bg-border" />
              <span class="text-[10px] font-semibold uppercase tracking-wider text-muted">
                {{ dateLabel(msg.created_at, index) }}
              </span>
              <div class="h-px flex-1 bg-border" />
            </div>

            <article
              class="message-block group animate-fade-in"
              :class="isExpanded(msg.id) ? 'message-block-expanded' : 'message-block-collapsed'"
              @click="!isExpanded(msg.id) && toggleMessage(msg.id)"
            >
              <header
                class="flex items-start gap-3 p-4"
                :class="isExpanded(msg.id) ? '' : 'pb-4'"
              >
                <UiAvatar
                  :label="msg.direction === 'outbound'
                    ? FormatHelper.initials(mailbox?.name, mailbox?.email)
                    : FormatHelper.initials(msg.from, msg.from)"
                  :outbound="msg.direction === 'outbound'"
                  size="sm"
                />
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                    <span class="text-sm font-semibold text-zinc-50">
                      {{ FormatHelper.displaySender(msg, mailbox) }}
                    </span>
                    <time class="text-[11px] tabular-nums text-muted">
                      {{ FormatHelper.formatFullDate(msg.created_at) }}
                    </time>
                  </div>
                  <div class="mt-1 flex flex-wrap items-center gap-1.5">
                    <UiBadge v-if="msg.is_unread" variant="accent">новое</UiBadge>
                    <UiBadge v-if="msg.is_starred" variant="warning">★</UiBadge>
                    <UiBadge :variant="msg.direction === 'outbound' ? 'brand' : 'success'">
                      {{ msg.direction === 'outbound' ? 'исходящее' : 'входящее' }}
                    </UiBadge>
                  </div>
                  <p v-if="!isExpanded(msg.id)" class="mt-2 line-clamp-2 text-sm text-muted">
                    {{ previewText(msg) }}
                  </p>
                </div>

                <div class="flex shrink-0 gap-0.5">
                  <button
                    v-if="!isExpanded(msg.id)"
                    type="button"
                    class="btn-icon btn-icon-ghost h-8 w-8 p-1.5"
                    title="Развернуть"
                    @click.stop="toggleMessage(msg.id)"
                  >
                    <AppIcon name="chevronDown" size="sm" />
                  </button>
                  <template v-else>
                    <button
                      type="button"
                      class="btn-icon btn-icon-ghost h-8 w-8 p-1.5 opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                      :class="msg.is_starred ? 'text-warning opacity-100' : ''"
                      @click.stop="emit('star-message', msg.id, !msg.is_starred)"
                    >
                      <AppIcon name="star" size="sm" :filled="msg.is_starred" />
                    </button>
                    <button
                      type="button"
                      class="btn-icon btn-icon-ghost h-8 w-8 p-1.5 text-danger opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                      @click.stop="emit('delete-message', msg.id)"
                    >
                      <AppIcon name="close" size="sm" />
                    </button>
                    <button
                      v-if="sortedMessages.length > 1"
                      type="button"
                      class="btn-icon btn-icon-ghost h-8 w-8 p-1.5"
                      title="Свернуть"
                      @click.stop="toggleMessage(msg.id)"
                    >
                      <AppIcon name="chevronUp" size="sm" />
                    </button>
                  </template>
                </div>
              </header>

              <div v-if="isExpanded(msg.id)" class="border-t border-border/60 px-4 pb-5 pt-4 sm:px-6 sm:pb-6">
                <div v-if="msg.html" class="email-body reading-prose" v-html="msg.html" />
                <pre v-else-if="msg.text" class="reading-prose whitespace-pre-wrap font-sans">{{ msg.text }}</pre>
                <p v-else class="text-sm italic text-muted">Содержимое недоступно</p>

                <div v-if="msg.attachments?.length" class="mt-5 flex flex-wrap gap-2 border-t border-border/60 pt-4">
                  <a
                    v-for="att in msg.attachments"
                    :key="att.id"
                    :href="attachmentHref(msg.id, att.id)"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-xs text-zinc-300 transition hover:border-accent hover:text-accent-hover"
                    @click.stop
                  >
                    <AppIcon name="attach" size="sm" />
                    <span class="max-w-[16rem] truncate">{{ att.filename }}</span>
                    <span v-if="att.size" class="text-[10px] text-muted">{{ AttachmentHelper.formatSize(att.size) }}</span>
                  </a>
                </div>

                <p v-if="msg.last_event" class="mt-3 text-[10px] text-muted">{{ msg.last_event }}</p>
              </div>
            </article>
          </template>
        </div>
      </div>

      <div
        v-if="thread && !loading"
        class="composer-bar px-4 py-3 sm:px-8 md:px-10"
        style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom));"
      >
        <div class="mx-auto max-w-5xl xl:max-w-6xl">
          <div
            v-if="!composerExpanded"
            class="flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2.5 transition hover:border-border-light"
          >
            <AppIcon name="reply" class="text-muted" />
            <button
              type="button"
              class="flex-1 text-left text-sm text-muted"
              @click="composerExpanded = true"
            >
              Ответить {{ thread.correspondent ? `— ${thread.correspondent}` : '' }}...
            </button>
            <button type="button" class="btn-icon btn-icon-ghost" @click="replyFileInput?.click()">
              <AppIcon name="attach" size="sm" />
            </button>
          </div>

          <div v-else class="rounded-2xl border border-border bg-surface p-3 shadow-panel sm:p-4">
            <RichTextEditor v-model="replyBody" placeholder="Напишите ответ..." min-height="140px" />
            <p v-if="mailbox?.signature" class="mt-2 whitespace-pre-wrap text-[11px] text-muted">
              Подпись: <span class="text-zinc-400">{{ mailbox.signature }}</span>
            </p>

            <input ref="replyFileInput" type="file" multiple class="hidden" @change="onReplyFilesSelected" />

            <div class="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                class="btn-secondary text-xs"
                :disabled="pickingFiles || replyAttachments.length >= limits.maxFiles"
                @click="replyFileInput?.click()"
              >
                {{ pickingFiles ? 'Загрузка...' : 'Прикрепить' }}
              </button>
              <span
                v-for="(file, index) in replyAttachments"
                :key="`${file.filename}-${index}`"
                class="inline-flex items-center gap-1 rounded-lg bg-surface-active px-2 py-1 text-xs"
              >
                <span class="max-w-[12rem] truncate">{{ file.filename }}</span>
                <button type="button" class="text-danger" @click="removeReplyAttachment(index)">✕</button>
              </span>
              <div class="ml-auto flex gap-2">
                <button type="button" class="btn-ghost text-xs" @click="composerExpanded = false">Свернуть</button>
                <button
                  type="button"
                  class="btn-primary text-xs"
                  :disabled="HtmlHelper.isEmpty(replyBody) && !replyAttachments.length"
                  @click="sendReply"
                >
                  Отправить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.email-body :deep(a) {
  @apply text-accent-hover underline;
}
.email-body :deep(img) {
  @apply my-3 max-w-full rounded-lg;
}
.email-body :deep(p) {
  @apply mb-3 last:mb-0;
}
.email-body :deep(blockquote) {
  @apply my-3 border-l-2 border-border-light pl-4 text-muted;
}
.email-body :deep(table) {
  @apply my-3 block max-w-full overflow-x-auto;
}
.email-body :deep(h1),
.email-body :deep(h2),
.email-body :deep(h3) {
  @apply mb-2 mt-4 font-semibold text-zinc-50 first:mt-0;
}
.email-body :deep(ul),
.email-body :deep(ol) {
  @apply my-3 list-inside list-disc pl-2;
}
</style>
