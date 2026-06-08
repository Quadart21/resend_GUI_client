<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'
import { HtmlHelper } from '@/services/HtmlHelper'
import { AttachmentHelper } from '@/services/AttachmentHelper'
import { api } from '@/services/ApiClient'
import RichTextEditor from '@/components/RichTextEditor.vue'

const props = defineProps({
  thread: { type: Object, default: null },
  mailbox: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['reply', 'back', 'star-thread', 'star-message', 'delete-message', 'notify'])

const scrollEl = ref(null)
const showQuickReply = ref(false)
const replyBody = ref('')
const replyAttachments = ref([])
const pickingFiles = ref(false)
const replyFileInput = ref(null)

const limits = AttachmentHelper.limits

const sortedMessages = computed(() => {
  if (!props.thread?.messages?.length) return []
  return [...props.thread.messages].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at),
  )
})

watch(
  () => [props.thread, props.loading],
  async () => {
    showQuickReply.value = false
    replyBody.value = ''
    replyAttachments.value = []
    await nextTick()
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  },
)

function sendQuickReply() {
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
  showQuickReply.value = false
  replyBody.value = ''
  replyAttachments.value = []
}

async function onReplyFilesSelected(event) {
  const input = event.target
  pickingFiles.value = true
  try {
    const items = await AttachmentHelper.readFiles(input.files)
    replyAttachments.value = [...replyAttachments.value, ...items].slice(0, limits.maxFiles)
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
</script>

<template>
  <section class="flex min-w-0 flex-1 flex-col overflow-hidden bg-[#09090b]">
    <!-- Пустое состояние (десктоп) -->
    <div
      v-if="!thread && !loading"
      class="hidden flex-1 flex-col items-center justify-center gap-2 text-zinc-500 md:flex"
    >
      <div class="mb-2 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-active text-3xl">
        💬
      </div>
      <h3 class="text-base font-semibold text-zinc-300">Выберите переписку</h3>
      <p class="max-w-xs text-center text-sm">Слева — список цепочек, здесь откроется переписка</p>
    </div>

    <!-- Заголовок + тело -->
    <template v-else-if="thread || loading">
      <header
        class="shrink-0 border-b border-border bg-surface-elevated/95 px-3 py-3 backdrop-blur-sm md:px-6 md:py-4"
        style="padding-top: max(0.75rem, env(safe-area-inset-top));"
      >
        <div class="flex items-start gap-2 md:gap-4">
          <button
            type="button"
            class="btn-icon mt-0.5 shrink-0 md:hidden"
            aria-label="Назад к списку"
            @click="emit('back')"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>

          <div class="min-w-0 flex-1">
            <div class="flex items-start gap-2">
              <h2 class="line-clamp-2 flex-1 text-base font-bold tracking-tight text-zinc-50 md:truncate md:text-lg">
                {{ thread?.subject || '(без темы)' }}
              </h2>
              <button
                type="button"
                class="btn-icon shrink-0"
                :class="thread?.is_starred ? 'text-amber-400' : 'text-zinc-500'"
                :title="thread?.is_starred ? 'Убрать из важных' : 'Пометить как важное'"
                :disabled="loading || !thread"
                @click="toggleThreadStar"
              >
                <svg class="h-5 w-5" viewBox="0 0 24 24" :fill="thread?.is_starred ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </button>
            </div>
            <p v-if="thread" class="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span>{{ thread.message_count || sortedMessages.length }} сообщ.</span>
              <span v-if="thread.correspondent">· {{ thread.correspondent }}</span>
              <span
                v-if="thread.is_starred"
                class="rounded bg-amber-500/15 px-1.5 py-0.5 font-semibold text-amber-400"
              >
                важное
              </span>
            </p>
          </div>

          <button
            type="button"
            class="btn-secondary shrink-0 px-3 py-2.5 md:px-4"
            :disabled="loading || !thread"
            @click="showQuickReply = true"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 00-4-4H4" />
            </svg>
            <span class="hidden sm:inline">Ответить</span>
          </button>
        </div>
      </header>

      <!-- Лента сообщений -->
      <div ref="scrollEl" class="relative flex-1 overflow-y-auto overscroll-contain px-3 py-4 sm:px-6 md:px-8 md:py-6">
        <div
          v-if="loading"
          class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-[#09090b]/80 backdrop-blur-[2px]"
        >
          <div class="h-8 w-8 animate-spin rounded-full border-[3px] border-border border-t-accent" />
          <p class="text-sm text-zinc-400">Загрузка переписки...</p>
        </div>

        <div v-if="thread && !sortedMessages.length && !loading" class="py-12 text-center text-sm text-zinc-500">
          В этой цепочке пока нет сообщений
        </div>

        <div class="mx-auto flex max-w-3xl flex-col gap-1">
          <template v-for="(msg, index) in sortedMessages" :key="msg.id">
            <div
              v-if="dateLabel(msg.created_at, index)"
              class="my-3 flex items-center gap-3 md:my-4"
            >
              <div class="h-px flex-1 bg-border" />
              <span class="shrink-0 text-[10px] font-medium uppercase tracking-wide text-zinc-500 md:text-[11px]">
                {{ dateLabel(msg.created_at, index) }}
              </span>
              <div class="h-px flex-1 bg-border" />
            </div>

            <div
              class="group mb-2 flex animate-fade-in md:mb-3"
              :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="flex max-w-[92%] gap-2 sm:max-w-[85%] sm:gap-3 md:max-w-[75%]"
                :class="msg.direction === 'outbound' ? 'flex-row-reverse' : 'flex-row'"
              >
                <div
                  class="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full text-[10px] font-bold text-white shadow-md sm:h-9 sm:w-9 sm:text-xs"
                  :class="msg.direction === 'outbound'
                    ? 'bg-gradient-to-br from-indigo-500 to-violet-600'
                    : 'bg-gradient-to-br from-zinc-600 to-zinc-700'"
                >
                  {{
                    msg.direction === 'outbound'
                      ? FormatHelper.initials(mailbox?.name, mailbox?.email)
                      : FormatHelper.initials(msg.from, msg.from)
                  }}
                </div>

                <div class="min-w-0 flex-1">
                  <div
                    class="mb-1 flex flex-wrap items-baseline gap-1.5 px-0.5 sm:gap-2 sm:px-1"
                    :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
                  >
                    <span class="text-xs font-semibold text-zinc-200">
                      {{ FormatHelper.displaySender(msg, mailbox) }}
                    </span>
                    <span
                      v-if="msg.is_unread"
                      class="rounded bg-accent/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-accent-hover"
                    >
                      новое
                    </span>
                    <span
                      v-if="msg.is_starred"
                      class="rounded bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-bold text-amber-400"
                    >
                      ★
                    </span>
                    <span class="text-[10px] text-zinc-500 sm:text-[11px]">
                      {{ FormatHelper.formatFullDate(msg.created_at) }}
                    </span>
                  </div>

                  <div
                    class="overflow-hidden rounded-2xl border px-3 py-2.5 shadow-sm sm:px-4 sm:py-3"
                    :class="msg.is_unread
                      ? 'rounded-tl-md border-accent/50 bg-accent/10 ring-1 ring-accent/20'
                      : msg.is_starred
                        ? 'rounded-tl-md border-amber-500/30 bg-amber-500/5'
                        : msg.direction === 'outbound'
                          ? 'rounded-tr-md border-indigo-800/60 bg-indigo-950/80'
                          : 'rounded-tl-md border-border bg-surface-active'"
                  >
                    <div
                      v-if="msg.html"
                      class="email-body text-sm leading-relaxed text-zinc-200"
                      v-html="msg.html"
                    />
                    <pre
                      v-else-if="msg.text"
                      class="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-200"
                    >{{ msg.text }}</pre>
                    <p v-else class="text-sm italic text-zinc-500">Содержимое недоступно</p>
                  </div>

                  <div
                    v-if="msg.attachments?.length"
                    class="mt-2 flex flex-wrap gap-2 px-0.5 sm:px-1"
                    :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
                  >
                    <a
                      v-for="att in msg.attachments"
                      :key="att.id"
                      :href="attachmentHref(msg.id, att.id)"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-elevated px-2.5 py-1.5 text-xs text-zinc-300 transition hover:border-accent hover:text-accent-hover"
                    >
                      <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                      </svg>
                      <span class="max-w-[12rem] truncate">{{ att.filename }}</span>
                      <span v-if="att.size" class="text-[10px] text-zinc-500">{{ AttachmentHelper.formatSize(att.size) }}</span>
                    </a>
                  </div>

                  <div
                    class="mt-1 flex items-center gap-1 px-0.5 sm:px-1"
                    :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
                  >
                    <button
                      type="button"
                      class="rounded-lg px-2 py-1 text-[10px] text-zinc-500 opacity-100 transition hover:bg-surface-hover hover:text-amber-400 sm:opacity-0 sm:group-hover:opacity-100"
                      :class="msg.is_starred ? 'text-amber-400 opacity-100' : ''"
                      :title="msg.is_starred ? 'Убрать из важных' : 'Пометить как важное'"
                      @click="emit('star-message', msg.id, !msg.is_starred)"
                    >
                      {{ msg.is_starred ? '★ Важное' : '☆ Важное' }}
                    </button>
                    <button
                      type="button"
                      class="rounded-lg px-2 py-1 text-[10px] text-zinc-500 opacity-100 transition hover:bg-surface-hover hover:text-red-400 sm:opacity-0 sm:group-hover:opacity-100"
                      title="Удалить сообщение"
                      @click="emit('delete-message', msg.id)"
                    >
                      Удалить
                    </button>
                  </div>

                  <p
                    v-if="msg.last_event"
                    class="mt-1 px-0.5 text-[10px] text-zinc-500 sm:px-1 sm:text-[11px]"
                    :class="msg.direction === 'outbound' ? 'text-right' : 'text-left'"
                  >
                    {{ msg.last_event }}
                  </p>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Быстрый ответ -->
      <div
        v-if="showQuickReply"
        class="shrink-0 border-t border-border bg-surface-elevated px-3 py-3 sm:px-6 sm:py-4"
        style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom));"
      >
        <RichTextEditor
          v-model="replyBody"
          class="mb-2.5"
          placeholder="Напишите ответ..."
          min-height="120px"
        />
        <p
          v-if="mailbox?.signature"
          class="mb-2.5 whitespace-pre-wrap text-[11px] leading-relaxed text-zinc-500"
        >
          Подпись будет добавлена автоматически:<br>
          <span class="text-zinc-400">{{ mailbox.signature }}</span>
        </p>

        <input
          ref="replyFileInput"
          type="file"
          multiple
          class="hidden"
          @change="onReplyFilesSelected"
        />

        <div class="mb-2.5 flex flex-wrap items-center gap-2">
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
            class="inline-flex items-center gap-1 rounded-lg bg-surface-active px-2 py-1 text-xs text-zinc-300"
          >
            <span class="max-w-[10rem] truncate">{{ file.filename }}</span>
            <button type="button" class="text-red-400" @click="removeReplyAttachment(index)">✕</button>
          </span>
        </div>

        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost px-4 py-2.5" @click="showQuickReply = false">Отмена</button>
          <button
            type="button"
            class="btn-primary px-4 py-2.5"
            :disabled="HtmlHelper.isEmpty(replyBody) && !replyAttachments.length"
            @click="sendQuickReply"
          >
            Отправить
          </button>
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
  @apply my-2 max-w-full rounded-lg;
}
.email-body :deep(p) {
  @apply mb-2 last:mb-0;
}
.email-body :deep(blockquote) {
  @apply border-l-2 border-zinc-600 pl-3 text-zinc-400;
}
.email-body :deep(table) {
  @apply block max-w-full overflow-x-auto;
}
</style>
