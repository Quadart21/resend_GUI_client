<script setup>
import { ref, watch, computed } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  threads: { type: Array, default: () => [] },
  activeMailbox: { type: Object, default: null },
  activeThreadId: { type: String, default: null },
  loading: { type: Boolean, default: false },
  unreadTotal: { type: Number, default: 0 },
  hasMore: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  notificationsOn: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  searching: { type: Boolean, default: false },
  showMailbox: { type: Boolean, default: false },
})

const emit = defineEmits([
  'select',
  'refresh',
  'load-more',
  'mark-all-read',
  'star-thread',
  'menu',
  'compose',
  'settings',
  'profile',
  'logout',
  'toggle-notifications',
  'update:searchQuery',
])

const listFilter = ref('all')

const isGlobalSearch = computed(() => props.searchQuery.trim().length >= 2)

const filtered = computed(() => {
  let items = props.threads
  if (listFilter.value === 'unread') {
    items = items.filter((t) => t.is_unread)
  } else if (listFilter.value === 'starred') {
    items = items.filter((t) => t.is_starred)
  }
  return items
})

watch(
  () => props.searchQuery,
  (value) => {
    if (value.trim().length >= 2) {
      listFilter.value = 'all'
    }
  },
)
</script>

<template>
  <section class="panel border-r border-border">
    <!-- Мобильная шапка -->
    <header class="flex items-center gap-2 border-b border-border px-3 py-3 md:hidden">
      <button type="button" class="btn-icon shrink-0" aria-label="Меню ящиков" @click="emit('menu')">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12h18M3 6h18M3 18h18" />
        </svg>
      </button>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <h2 class="truncate text-base font-bold tracking-tight">
            {{ isGlobalSearch ? 'Поиск' : 'Переписки' }}
          </h2>
          <span
            v-if="!isGlobalSearch && unreadTotal"
            class="shrink-0 rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-white"
          >
            {{ unreadTotal }}
          </span>
        </div>
        <p v-if="activeMailbox && !isGlobalSearch" class="truncate text-[11px] text-zinc-500">
          {{ activeMailbox.email }}
        </p>
        <p v-else-if="isGlobalSearch" class="truncate text-[11px] text-zinc-500">По всем ящикам</p>
      </div>
      <button
        v-if="!isGlobalSearch && unreadTotal"
        type="button"
        class="btn-ghost shrink-0 px-2 py-1 text-[10px] text-accent-hover"
        @click="emit('mark-all-read')"
      >
        Прочитать всё
      </button>
      <button type="button" class="btn-icon shrink-0" title="Обновить" @click="emit('refresh')">
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6" />
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
        </svg>
      </button>
      <button
        type="button"
        class="btn-icon shrink-0"
        :class="notificationsOn ? 'border-accent text-accent-hover' : ''"
        title="Уведомления"
        @click="emit('toggle-notifications')"
      >
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
      </button>
      <button v-if="isAdmin" type="button" class="btn-icon shrink-0" title="Настройки" @click="emit('settings')">
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      </button>
      <button type="button" class="btn-icon shrink-0" title="Профиль" @click="emit('profile')">
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </button>
      <button type="button" class="btn-icon shrink-0" title="Выйти" @click="emit('logout')">
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
        </svg>
      </button>
    </header>

    <!-- Десктопная шапка -->
    <header class="hidden items-center justify-between border-b border-border px-4 py-4 md:flex">
      <div class="flex flex-col gap-1.5">
        <div v-if="activeMailbox && !isGlobalSearch" class="flex items-center gap-1.5 text-xs text-zinc-500">
          <span class="h-2 w-2 shrink-0 rounded-full" :style="{ background: activeMailbox.color }" />
          {{ activeMailbox.email }}
        </div>
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold tracking-tight">
            {{ isGlobalSearch ? 'Поиск' : 'Переписки' }}
          </h2>
          <span
            v-if="!isGlobalSearch && unreadTotal"
            class="rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-white"
          >
            {{ unreadTotal }}
          </span>
        </div>
        <p v-if="isGlobalSearch" class="text-[11px] text-zinc-500">По всем доступным ящикам</p>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="!isGlobalSearch && unreadTotal"
          type="button"
          class="btn-ghost px-2 py-1.5 text-xs text-accent-hover"
          title="Прочитать всё"
          @click="emit('mark-all-read')"
        >
          Прочитать всё
        </button>
        <button type="button" class="btn-icon" title="Обновить" @click="emit('refresh')">
          <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Поиск -->
    <div class="relative border-b border-border px-3 py-2.5">
      <svg class="pointer-events-none absolute left-6 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500 md:left-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
      </svg>
      <input
        :value="searchQuery"
        type="search"
        class="input-field pl-9"
        placeholder="Поиск по всем ящикам..."
        enterkeyhint="search"
        @input="emit('update:searchQuery', $event.target.value)"
      />
    </div>

    <!-- Фильтры -->
    <div
      v-if="!isGlobalSearch"
      class="flex gap-1.5 border-b border-border px-3 py-2"
    >
      <button
        type="button"
        class="rounded-lg px-2.5 py-1 text-[11px] font-semibold transition"
        :class="listFilter === 'all'
          ? 'bg-accent-soft text-accent-hover'
          : 'bg-surface-active text-zinc-500 hover:text-zinc-300'"
        @click="listFilter = 'all'"
      >
        Все
      </button>
      <button
        type="button"
        class="rounded-lg px-2.5 py-1 text-[11px] font-semibold transition"
        :class="listFilter === 'unread'
          ? 'bg-accent-soft text-accent-hover'
          : 'bg-surface-active text-zinc-500 hover:text-zinc-300'"
        @click="listFilter = 'unread'"
      >
        Непрочитанные
      </button>
      <button
        type="button"
        class="rounded-lg px-2.5 py-1 text-[11px] font-semibold transition"
        :class="listFilter === 'starred'
          ? 'bg-amber-500/15 text-amber-400'
          : 'bg-surface-active text-zinc-500 hover:text-zinc-300'"
        @click="listFilter = 'starred'"
      >
        Важные
      </button>
    </div>

    <!-- Список -->
    <div class="flex-1 overflow-y-auto overscroll-contain">
      <div v-if="loading || searching" class="flex flex-col items-center gap-3 py-12 text-zinc-500">
        <div class="h-7 w-7 animate-spin rounded-full border-[3px] border-border border-t-accent" />
        <p class="text-sm">{{ searching ? 'Поиск...' : 'Загрузка...' }}</p>
      </div>

      <div v-else-if="!filtered.length" class="px-4 py-12 text-center text-sm text-zinc-500">
        <p>{{ isGlobalSearch ? 'Ничего не найдено' : listFilter === 'all' ? 'Нет переписок' : 'Нет подходящих переписок' }}</p>
        <p v-if="!isGlobalSearch && listFilter === 'all'" class="mt-1.5 text-xs">
          Напишите первое письмо или дождитесь входящего
        </p>
      </div>

      <button
        v-for="thread in filtered"
        :key="`${thread.mailbox_id || 'local'}-${thread.id}`"
        type="button"
        class="relative w-full border-b border-border px-4 py-4 text-left transition active:bg-surface-hover md:py-3.5 md:hover:bg-surface-hover"
        :class="[
          thread.id === activeThreadId ? 'bg-surface-active' : '',
          thread.is_unread ? 'bg-accent/5' : '',
          thread.is_starred ? 'border-l-2 border-l-amber-400/80' : '',
        ]"
        @click="emit('select', thread.id, thread.mailbox_id)"
      >
        <button
          type="button"
          class="absolute right-3 top-3 z-10 rounded-lg p-1.5 text-zinc-500 transition hover:bg-surface-hover hover:text-amber-400 md:top-3.5"
          :class="thread.is_starred ? 'text-amber-400' : ''"
          :title="thread.is_starred ? 'Убрать из важных' : 'Пометить как важное'"
          @click.stop="emit('star-thread', thread.id, !thread.is_starred, thread.mailbox_id)"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" :fill="thread.is_starred ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </button>
        <span
          v-if="thread.is_unread"
          class="absolute left-1.5 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-accent md:left-2"
        />
        <div
          v-if="thread.id === activeThreadId"
          class="absolute bottom-0 left-0 top-0 w-[3px] rounded-r bg-accent"
        />
        <div class="mb-1 flex items-baseline justify-between gap-2 pr-8">
          <span
            class="truncate text-[14px] md:text-[13px]"
            :class="thread.is_unread ? 'font-bold text-zinc-50' : 'font-semibold'"
          >
            {{ thread.correspondent }}
          </span>
          <span
            class="shrink-0 text-[11px]"
            :class="thread.is_unread ? 'font-semibold text-accent-hover' : 'text-zinc-500'"
          >
            {{ FormatHelper.formatDate(thread.last_message_at) }}
          </span>
        </div>
        <div
          class="truncate text-[13px]"
          :class="thread.is_unread ? 'font-medium text-zinc-200' : 'text-zinc-400'"
        >
          {{ thread.subject }}
        </div>
        <div
          class="truncate text-xs"
          :class="thread.is_unread ? 'text-zinc-400' : 'text-zinc-500'"
        >
          {{ thread.preview }}
        </div>
        <div class="mt-1.5 flex flex-wrap items-center gap-1.5">
          <span
            v-if="showMailbox && thread.mailbox_name"
            class="inline-flex items-center gap-1 rounded bg-surface-active px-1.5 py-0.5 text-[10px] font-medium text-zinc-400"
          >
            <span
              v-if="thread.mailbox_color"
              class="h-1.5 w-1.5 rounded-full"
              :style="{ background: thread.mailbox_color }"
            />
            {{ thread.mailbox_name }}
          </span>
          <span
            v-if="thread.is_unread && thread.unread_count"
            class="rounded bg-accent/20 px-1.5 py-0.5 text-[10px] font-bold text-accent-hover"
          >
            {{ thread.unread_count }} нов.
          </span>
          <span class="rounded bg-surface-active px-1.5 py-0.5 text-[10px] font-semibold text-zinc-500">
            {{ thread.message_count }} сообщ.
          </span>
          <span
            v-if="thread.is_starred"
            class="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-bold text-amber-400"
          >
            важное
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

      <div
        v-if="hasMore && filtered.length && !isGlobalSearch"
        class="border-b border-border px-4 py-3 text-center"
      >
        <button
          type="button"
          class="btn-secondary w-full text-xs sm:w-auto"
          :disabled="loadingMore"
          @click="emit('load-more')"
        >
          {{ loadingMore ? 'Загрузка...' : 'Загрузить ещё' }}
        </button>
      </div>
    </div>
  </section>
</template>
