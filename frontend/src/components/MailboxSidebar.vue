<script setup>
import { FormatHelper } from '@/services/FormatHelper'
import AppIcon from '@/components/ui/AppIcon.vue'
import UiAvatar from '@/components/ui/UiAvatar.vue'

defineProps({
  mailboxes: { type: Array, default: () => [] },
  activeId: { type: String, default: null },
  threadCounts: { type: Object, default: () => ({}) },
  isAdmin: { type: Boolean, default: false },
  username: { type: String, default: '' },
  notificationsOn: { type: Boolean, default: false },
})

const emit = defineEmits([
  'select', 'add', 'compose', 'settings', 'users', 'profile', 'logout', 'close', 'toggle-notifications',
])
</script>

<template>
  <aside
    class="flex shrink-0 flex-col gap-3 overflow-y-auto border-r border-border bg-surface-elevated p-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(1rem,env(safe-area-inset-top))] md:w-[15.5rem]"
  >
    <div class="flex items-center gap-3 px-1.5">
      <div class="brand-mark">
        <AppIcon name="mail" size="sm" class="text-white" />
      </div>
      <div class="min-w-0 flex-1">
        <h1 class="text-sm font-bold tracking-tight">Kubex Mail</h1>
        <p class="text-[11px] text-muted">Почтовый клиент</p>
      </div>
      <button type="button" class="btn-icon btn-icon-ghost md:hidden" aria-label="Закрыть" @click="emit('close')">
        <AppIcon name="close" />
      </button>
    </div>

    <button type="button" class="btn-primary w-full shadow-md shadow-accent/20" @click="emit('compose')">
      <AppIcon name="compose" size="sm" />
      Написать
    </button>

    <div class="flex min-h-0 flex-1 flex-col gap-1">
      <p class="px-2 text-[10px] font-bold uppercase tracking-widest text-muted">Ящики</p>

      <div v-if="!mailboxes.length" class="rounded-xl border border-dashed border-border px-3 py-6 text-center text-xs text-muted">
        {{ isAdmin ? 'Добавьте ящик в настройках' : 'Нет доступных ящиков' }}
      </div>

      <button
        v-for="box in mailboxes"
        :key="box.id"
        type="button"
        class="mailbox-item"
        :class="{ 'mailbox-item-active': box.id === activeId }"
        @click="emit('select', box.id)"
      >
        <UiAvatar :label="FormatHelper.initials(box.name, box.email)" :color="box.color" size="sm" />
        <div class="min-w-0 flex-1">
          <div class="truncate text-[13px] font-semibold">{{ box.name || box.email }}</div>
          <div class="truncate text-[11px] text-muted">{{ box.email }}</div>
        </div>
        <span
          v-if="threadCounts[box.id]"
          class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums"
          :class="box.id === activeId ? 'bg-white text-accent' : 'bg-accent text-white'"
        >
          {{ threadCounts[box.id] }}
        </span>
      </button>

      <button
        v-if="isAdmin"
        type="button"
        class="mt-1 rounded-xl border border-dashed border-border px-3 py-2 text-xs text-muted transition hover:border-accent hover:text-accent-hover"
        @click="emit('add')"
      >
        + Добавить ящик
      </button>
    </div>

    <div class="mt-auto space-y-1 border-t border-border pt-3">
      <div v-if="username" class="mb-2 flex items-center gap-2.5 px-2">
        <UiAvatar :label="FormatHelper.initials(username, username)" size="sm" />
        <div class="min-w-0 flex-1">
          <div class="truncate text-xs font-semibold">{{ username }}</div>
          <div class="text-[10px] text-muted">{{ isAdmin ? 'Администратор' : 'Пользователь' }}</div>
        </div>
      </div>

      <button
        type="button"
        class="nav-item"
        :class="{ 'nav-item-active': notificationsOn }"
        @click="emit('toggle-notifications')"
      >
        <AppIcon name="bell" />
        {{ notificationsOn ? 'Уведомления вкл.' : 'Уведомления' }}
      </button>
      <button type="button" class="nav-item" @click="emit('profile')">
        <AppIcon name="user" />
        Профиль
      </button>
      <button v-if="isAdmin" type="button" class="nav-item" @click="emit('settings')">
        <AppIcon name="settings" />
        Настройки
      </button>
      <button v-if="isAdmin" type="button" class="nav-item" @click="emit('users')">
        <AppIcon name="users" />
        Пользователи
      </button>
      <button type="button" class="nav-item text-danger hover:text-danger" @click="emit('logout')">
        <AppIcon name="logout" />
        Выйти
      </button>
    </div>
  </aside>
</template>
