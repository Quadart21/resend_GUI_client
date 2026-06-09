<script setup>
import { ref, watch, computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiSegmentedControl from '@/components/ui/UiSegmentedControl.vue'
import ThreadListItem from '@/components/ThreadListItem.vue'

const props = defineProps({
  threads: { type: Array, default: () => [] },
  activeMailbox: { type: Object, default: null },
  activeThreadId: { type: String, default: null },
  loading: { type: Boolean, default: false },
  unreadTotal: { type: Number, default: 0 },
  hasMore: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  searching: { type: Boolean, default: false },
  showMailbox: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
  layout: { type: String, default: 'full' },
})

const emit = defineEmits([
  'select',
  'refresh',
  'load-more',
  'mark-all-read',
  'star-thread',
  'menu',
  'compose',
  'update:searchQuery',
])

const listFilter = ref('all')

const isGlobalSearch = computed(() => props.searchQuery.trim().length >= 2)

const filterOptions = computed(() => [
  { value: 'all', label: 'Все' },
  { value: 'unread', label: 'Новые', count: props.unreadTotal || null },
  { value: 'starred', label: 'Важные', warn: true },
])

const filtered = computed(() => {
  let items = props.threads
  if (listFilter.value === 'unread') items = items.filter((t) => t.is_unread)
  else if (listFilter.value === 'starred') items = items.filter((t) => t.is_starred)
  return items
})

const layoutClass = computed(() =>
  props.layout === 'split' ? 'inbox-split' : 'inbox-full',
)

watch(
  () => props.searchQuery,
  (value) => {
    if (value.trim().length >= 2) listFilter.value = 'all'
  },
)
</script>

<template>
  <section class="panel flex flex-col overflow-hidden bg-surface" :class="layoutClass">
    <header class="panel-header flex items-center gap-2">
      <button type="button" class="btn-icon btn-icon-ghost md:hidden" aria-label="Меню" @click="emit('menu')">
        <AppIcon name="menu" />
      </button>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <h2 class="truncate text-sm font-bold tracking-tight">
            {{ isGlobalSearch ? 'Поиск' : compact ? 'Переписки' : 'Входящие' }}
          </h2>
          <span
            v-if="!isGlobalSearch && unreadTotal"
            class="rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-white"
          >
            {{ unreadTotal }}
          </span>
        </div>
        <p v-if="!compact" class="truncate text-[11px] text-muted">
          {{ isGlobalSearch ? 'По всем ящикам' : activeMailbox?.email }}
        </p>
      </div>

      <button
        v-if="!isGlobalSearch && unreadTotal && !compact"
        type="button"
        class="btn-ghost hidden px-2 py-1 text-[11px] sm:inline-flex"
        @click="emit('mark-all-read')"
      >
        Прочитать всё
      </button>
      <button type="button" class="btn-icon btn-icon-ghost" title="Обновить" @click="emit('refresh')">
        <AppIcon name="refresh" />
      </button>
      <button
        v-if="!compact"
        type="button"
        class="btn-primary hidden px-3 py-2 text-xs md:inline-flex"
        @click="emit('compose')"
      >
        <AppIcon name="compose" size="sm" />
        Написать
      </button>
    </header>

    <div v-if="!compact" class="relative border-b border-border px-3 py-2.5">
      <AppIcon name="search" class="pointer-events-none absolute left-6 top-1/2 -translate-y-1/2 text-muted" />
      <input
        :value="searchQuery"
        type="search"
        class="input-field pl-10"
        placeholder="Поиск по всем ящикам..."
        enterkeyhint="search"
        @input="emit('update:searchQuery', $event.target.value)"
      />
    </div>

    <div v-if="!isGlobalSearch && !compact" class="border-b border-border px-3 py-2">
      <UiSegmentedControl v-model="listFilter" :options="filterOptions" />
    </div>

    <div class="flex-1 overflow-y-auto overscroll-contain">
      <div v-if="loading || searching" class="grid place-items-center py-16">
        <UiSpinner :label="searching ? 'Поиск...' : 'Загрузка...'" />
      </div>

      <UiEmptyState
        v-else-if="!filtered.length"
        :title="isGlobalSearch ? 'Ничего не найдено' : listFilter === 'all' ? 'Нет переписок' : 'Нет подходящих переписок'"
        :description="!isGlobalSearch && listFilter === 'all' && !compact ? 'Напишите первое письмо или дождитесь входящего' : ''"
        :icon="isGlobalSearch ? 'search' : 'inbox'"
      />

      <template v-else>
        <ThreadListItem
          v-for="thread in filtered"
          :key="`${thread.mailbox_id || 'local'}-${thread.id}`"
          :thread="thread"
          :active="thread.id === activeThreadId"
          :show-mailbox="showMailbox"
          :compact="compact"
          @select="(id, mb) => emit('select', id, mb)"
          @star="(id, starred, mb) => emit('star-thread', id, starred, mb)"
        />

        <div v-if="hasMore && !isGlobalSearch" class="px-4 py-4 text-center">
          <button type="button" class="btn-secondary w-full text-xs" :disabled="loadingMore" @click="emit('load-more')">
            {{ loadingMore ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </template>
    </div>
  </section>
</template>
