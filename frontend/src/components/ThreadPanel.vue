<script setup>
import { ref, watch } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  threads: { type: Array, default: () => [] },
  activeMailbox: { type: Object, default: null },
  activeThreadId: { type: String, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'refresh'])

const search = ref('')
const filtered = ref([])

watch(
  () => [props.threads, search.value],
  () => {
    const q = search.value.toLowerCase()
    filtered.value = q
      ? props.threads.filter((t) =>
          [t.subject, t.correspondent, t.preview, ...(t.participants || [])]
            .join(' ')
            .toLowerCase()
            .includes(q),
        )
      : props.threads
  },
  { immediate: true, deep: true },
)
</script>

<template>
  <section class="panel w-[340px] shrink-0 border-r border-border">
    <!-- Заголовок -->
    <header class="flex items-center justify-between border-b border-border px-4 py-4">
      <div class="flex flex-col gap-1.5">
        <div v-if="activeMailbox" class="flex items-center gap-1.5 text-xs text-zinc-500">
          <span class="h-2 w-2 shrink-0 rounded-full" :style="{ background: activeMailbox.color }" />
          {{ activeMailbox.email }}
        </div>
        <h2 class="text-base font-bold tracking-tight">Переписки</h2>
      </div>
      <button class="btn-icon" title="Обновить" @click="emit('refresh')">
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6" />
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
        </svg>
      </button>
    </header>

    <!-- Поиск -->
    <div class="relative border-b border-border px-3 py-2.5">
      <svg class="pointer-events-none absolute left-6 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
      </svg>
      <input
        v-model="search"
        type="search"
        class="input-field pl-9"
        placeholder="Поиск по теме или собеседнику..."
      />
    </div>

    <!-- Список -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="flex flex-col items-center gap-3 py-12 text-zinc-500">
        <div class="h-7 w-7 animate-spin rounded-full border-[3px] border-border border-t-accent" />
        <p class="text-sm">Загрузка...</p>
      </div>

      <div v-else-if="!filtered.length" class="px-4 py-12 text-center text-sm text-zinc-500">
        <p>Нет переписок</p>
        <p class="mt-1.5 text-xs">Напишите первое письмо или дождитесь входящего</p>
      </div>

      <button
        v-for="thread in filtered"
        :key="thread.id"
        class="relative w-full border-b border-border px-4 py-3.5 text-left transition hover:bg-surface-hover"
        :class="thread.id === activeThreadId ? 'bg-surface-active' : ''"
        @click="emit('select', thread.id)"
      >
        <div
          v-if="thread.id === activeThreadId"
          class="absolute bottom-0 left-0 top-0 w-[3px] rounded-r bg-accent"
        />
        <div class="mb-1 flex items-baseline justify-between gap-2">
          <span class="truncate text-[13px] font-semibold">{{ thread.correspondent }}</span>
          <span class="shrink-0 text-[11px] text-zinc-500">{{ FormatHelper.formatDate(thread.last_message_at) }}</span>
        </div>
        <div class="truncate text-[13px] text-zinc-400">{{ thread.subject }}</div>
        <div class="truncate text-xs text-zinc-500">{{ thread.preview }}</div>
        <div class="mt-1.5 flex items-center gap-1.5">
          <span class="rounded bg-surface-active px-1.5 py-0.5 text-[10px] font-semibold text-zinc-500">
            {{ thread.message_count }} сообщ.
          </span>
          <span
            class="rounded px-1.5 py-0.5 text-[10px] font-medium"
            :class="thread.last_direction === 'outbound'
              ? 'bg-indigo-500/15 text-indigo-300'
              : 'bg-green-500/15 text-green-400'"
          >
            {{ thread.last_direction === 'outbound' ? 'исх.' : 'вх.' }}
          </span>
        </div>
      </button>
    </div>
  </section>
</template>
