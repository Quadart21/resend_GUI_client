<script setup>
import { ref, watch, nextTick } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  thread: { type: Object, default: null },
  mailbox: { type: Object, default: null },
})

const emit = defineEmits(['reply'])

const scrollEl = ref(null)
const showQuickReply = ref(false)
const replyBody = ref('')

watch(
  () => props.thread,
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
</script>

<template>
  <section class="flex min-w-0 flex-1 flex-col overflow-hidden bg-[#09090b]">
    <!-- Пустое состояние -->
    <div v-if="!thread" class="flex flex-1 flex-col items-center justify-center gap-2 text-zinc-500">
      <div class="mb-2 text-5xl opacity-60">💬</div>
      <h3 class="text-base font-semibold text-zinc-400">Выберите переписку</h3>
      <p class="text-sm">Сообщения отображаются в хронологическом порядке</p>
    </div>

    <!-- Переписка -->
    <template v-else>
      <header class="flex items-start justify-between gap-4 border-b border-border bg-surface-elevated px-6 py-5">
        <div>
          <h2 class="text-lg font-bold leading-snug tracking-tight">{{ thread.subject || '(без темы)' }}</h2>
          <p class="mt-1 text-xs text-zinc-500">
            {{ thread.message_count }} сообщений
            <span v-if="thread.participants?.length"> · {{ thread.participants.join(', ') }}</span>
          </p>
        </div>
        <button class="btn-secondary shrink-0" @click="showQuickReply = true">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 00-4-4H4" />
          </svg>
          Ответить
        </button>
      </header>

      <!-- Сообщения -->
      <div ref="scrollEl" class="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-5">
        <div
          v-for="msg in thread.messages"
          :key="msg.id"
          class="max-w-[78%] animate-fade-in rounded-[14px] border px-4 py-3.5"
          :class="msg.direction === 'outbound'
            ? 'ml-auto border-indigo-700 bg-indigo-950'
            : 'mr-auto border-border bg-surface-active'"
        >
          <div class="mb-2 flex flex-wrap items-center gap-2 text-xs">
            <span class="font-semibold text-zinc-100">
              {{ FormatHelper.displaySender(msg, mailbox) }}
            </span>
            <span class="text-zinc-500">{{ FormatHelper.formatFullDate(msg.created_at) }}</span>
            <span
              class="rounded px-1.5 py-0.5 text-[10px] font-medium"
              :class="msg.direction === 'outbound' ? 'text-indigo-300' : 'text-green-400'"
            >
              {{ msg.direction === 'outbound' ? '→ отправлено' : '← получено' }}
            </span>
          </div>
          <div
            v-if="msg.html"
            class="prose prose-invert max-w-none text-sm leading-relaxed [&_img]:max-w-full [&_img]:rounded-md"
            v-html="msg.html"
          />
          <pre v-else-if="msg.text" class="whitespace-pre-wrap font-sans text-sm leading-relaxed">{{ msg.text }}</pre>
          <p v-else class="text-sm text-zinc-500">Содержимое недоступно</p>
          <p v-if="msg.last_event" class="mt-2 text-[11px] text-zinc-500">Статус: {{ msg.last_event }}</p>
        </div>
      </div>

      <!-- Быстрый ответ -->
      <div v-if="showQuickReply" class="border-t border-border bg-surface-elevated px-6 py-4">
        <textarea
          v-model="replyBody"
          rows="3"
          class="input-field mb-2.5 resize-y"
          placeholder="Быстрый ответ..."
          autofocus
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
