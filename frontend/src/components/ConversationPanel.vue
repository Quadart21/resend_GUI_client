<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  thread: { type: Object, default: null },
  mailbox: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['reply'])

const scrollEl = ref(null)
const showQuickReply = ref(false)
const replyBody = ref('')

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
    await nextTick()
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  },
)

function sendQuickReply() {
  const text = replyBody.value.trim()
  if (!text) return
  emit('reply', text)
  showQuickReply.value = false
  replyBody.value = ''
}

/** Показывает разделитель даты между сообщениями */
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
</script>

<template>
  <section class="flex min-w-[320px] flex-1 flex-col overflow-hidden bg-[#09090b]">
    <!-- Пустое состояние -->
    <div
      v-if="!thread && !loading"
      class="flex flex-1 flex-col items-center justify-center gap-2 text-zinc-500"
    >
      <div class="mb-2 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-active text-3xl">
        💬
      </div>
      <h3 class="text-base font-semibold text-zinc-300">Выберите переписку</h3>
      <p class="max-w-xs text-center text-sm">Слева — список цепочек, здесь откроется переписка</p>
    </div>

    <!-- Заголовок + тело -->
    <template v-else-if="thread">
      <header class="shrink-0 border-b border-border bg-surface-elevated/80 px-6 py-4 backdrop-blur-sm">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h2 class="truncate text-lg font-bold tracking-tight text-zinc-50">
              {{ thread.subject || '(без темы)' }}
            </h2>
            <p class="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span>{{ thread.message_count || sortedMessages.length }} сообщ.</span>
              <span v-if="thread.correspondent">· {{ thread.correspondent }}</span>
            </p>
          </div>
          <button
            class="btn-secondary shrink-0"
            :disabled="loading"
            @click="showQuickReply = true"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 00-4-4H4" />
            </svg>
            Ответить
          </button>
        </div>
      </header>

      <!-- Лента сообщений -->
      <div ref="scrollEl" class="relative flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <!-- Загрузка содержимого -->
        <div
          v-if="loading"
          class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-[#09090b]/80 backdrop-blur-[2px]"
        >
          <div class="h-8 w-8 animate-spin rounded-full border-[3px] border-border border-t-accent" />
          <p class="text-sm text-zinc-400">Загрузка переписки...</p>
        </div>

        <div v-if="!sortedMessages.length && !loading" class="py-12 text-center text-sm text-zinc-500">
          В этой цепочке пока нет сообщений
        </div>

        <div class="mx-auto flex max-w-3xl flex-col gap-1">
          <template v-for="(msg, index) in sortedMessages" :key="msg.id">
            <!-- Разделитель даты -->
            <div
              v-if="dateLabel(msg.created_at, index)"
              class="my-4 flex items-center gap-3"
            >
              <div class="h-px flex-1 bg-border" />
              <span class="shrink-0 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                {{ dateLabel(msg.created_at, index) }}
              </span>
              <div class="h-px flex-1 bg-border" />
            </div>

            <!-- Сообщение -->
            <div
              class="mb-3 flex animate-fade-in"
              :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="flex max-w-[85%] gap-3 sm:max-w-[75%]"
                :class="msg.direction === 'outbound' ? 'flex-row-reverse' : 'flex-row'"
              >
                <!-- Аватар -->
                <div
                  class="mt-1 grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-bold text-white shadow-md"
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

                <!-- Пузырь -->
                <div class="min-w-0 flex-1">
                  <div
                    class="mb-1 flex flex-wrap items-baseline gap-2 px-1"
                    :class="msg.direction === 'outbound' ? 'justify-end' : 'justify-start'"
                  >
                    <span class="text-xs font-semibold text-zinc-200">
                      {{ FormatHelper.displaySender(msg, mailbox) }}
                    </span>
                    <span class="text-[11px] text-zinc-500">
                      {{ FormatHelper.formatFullDate(msg.created_at) }}
                    </span>
                  </div>

                  <div
                    class="overflow-hidden rounded-2xl border px-4 py-3 shadow-sm"
                    :class="msg.direction === 'outbound'
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

                  <p
                    v-if="msg.last_event"
                    class="mt-1 px-1 text-[11px] text-zinc-500"
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
      <div v-if="showQuickReply" class="shrink-0 border-t border-border bg-surface-elevated px-6 py-4">
        <textarea
          v-model="replyBody"
          rows="3"
          class="input-field mb-2.5 resize-y"
          placeholder="Напишите ответ..."
        />
        <div class="flex justify-end gap-2">
          <button class="btn-ghost" @click="showQuickReply = false">Отмена</button>
          <button class="btn-primary" :disabled="!replyBody.trim()" @click="sendQuickReply">
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
</style>
