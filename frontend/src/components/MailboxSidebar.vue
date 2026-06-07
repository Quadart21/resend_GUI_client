<script setup>
import { FormatHelper } from '@/services/FormatHelper'

defineProps({
  mailboxes: { type: Array, default: () => [] },
  activeId: { type: String, default: null },
  threadCounts: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['select', 'add', 'compose'])
</script>

<template>
  <aside class="flex w-60 shrink-0 flex-col gap-4 overflow-y-auto border-r border-border bg-surface-elevated p-4">
    <!-- Бренд -->
    <div class="flex items-center gap-3 px-2">
      <div class="grid h-10 w-10 shrink-0 place-items-center rounded-[11px] bg-gradient-to-br from-accent to-purple-500 text-white">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
          <polyline points="22,6 12,13 2,6" />
        </svg>
      </div>
      <div>
        <h1 class="text-[15px] font-bold tracking-tight">Resend Mail</h1>
        <p class="text-[11px] text-zinc-500">Почтовый клиент</p>
      </div>
    </div>

    <!-- Написать -->
    <button class="btn-primary w-full" @click="emit('compose')">
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12h14" />
      </svg>
      Написать
    </button>

    <!-- Ящики -->
    <div class="flex min-h-0 flex-1 flex-col gap-1.5">
      <p class="px-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Почтовые ящики</p>

      <div v-if="!mailboxes.length" class="px-2 py-4 text-center text-xs text-zinc-500">
        Добавьте ящик в настройках
      </div>

      <button
        v-for="box in mailboxes"
        :key="box.id"
        class="flex w-full items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-left transition"
        :class="box.id === activeId
          ? 'bg-accent-soft text-zinc-100'
          : 'text-zinc-400 hover:bg-surface-hover hover:text-zinc-100'"
        @click="emit('select', box.id)"
      >
        <div
          class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xs font-bold text-white"
          :style="{ background: box.color }"
        >
          {{ FormatHelper.initials(box.name, box.email) }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="truncate text-[13px] font-semibold">{{ box.name || box.email }}</div>
          <div class="truncate text-[11px] text-zinc-500">{{ box.email }}</div>
        </div>
        <span
          v-if="threadCounts[box.id]"
          class="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold"
          :class="box.id === activeId ? 'bg-accent text-white' : 'bg-surface-active text-zinc-400'"
        >
          {{ threadCounts[box.id] }}
        </span>
      </button>

      <button
        class="mt-1 rounded-[10px] border border-dashed border-border-light px-2.5 py-2 text-xs text-zinc-500 transition hover:border-accent hover:text-accent-hover"
        @click="emit('add')"
      >
        + Добавить ящик
      </button>
    </div>

    <!-- Настройки -->
    <nav class="mt-auto">
      <button
        class="flex w-full items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-[13px] text-zinc-400 transition hover:bg-surface-hover hover:text-zinc-100"
        @click="emit('settings')"
      >
        <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
        Настройки
      </button>
    </nav>
  </aside>
</template>
