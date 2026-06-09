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
  'select',
  'compose',
  'add',
  'settings',
  'users',
  'profile',
  'logout',
  'toggle-notifications',
  'open-menu',
])
</script>

<template>
  <header
    class="top-nav shrink-0 border-b border-border bg-surface-elevated/95 backdrop-blur-md"
    style="padding-top: max(0.5rem, env(safe-area-inset-top));"
  >
    <div class="flex items-center gap-2 px-3 py-2 sm:gap-3 sm:px-4">
      <button type="button" class="btn-icon btn-icon-ghost md:hidden" aria-label="Меню" @click="emit('open-menu')">
        <AppIcon name="menu" />
      </button>

      <div class="flex shrink-0 items-center gap-2.5">
        <div class="brand-mark h-9 w-9" title="Kubex Mail">
          <AppIcon name="mail" size="sm" class="text-white" />
        </div>
        <div class="hidden min-w-0 sm:block">
          <h1 class="text-sm font-bold tracking-tight">Kubex Mail</h1>
          <p class="text-[10px] text-muted">Почтовый клиент</p>
        </div>
      </div>

      <button type="button" class="btn-primary shrink-0 px-3 py-2 text-xs" @click="emit('compose')">
        <AppIcon name="compose" size="sm" />
        <span class="hidden sm:inline">Написать</span>
      </button>

      <div class="mx-1 hidden h-8 w-px bg-border sm:block" />

      <div class="top-nav-mailboxes min-w-0 flex-1">
        <div v-if="!mailboxes.length" class="text-xs text-muted">
          {{ isAdmin ? 'Добавьте ящик' : 'Нет ящиков' }}
        </div>

        <div v-else class="flex items-center gap-1.5 overflow-x-auto overscroll-x-contain pb-0.5">
          <button
            v-for="box in mailboxes"
            :key="box.id"
            type="button"
            class="top-nav-mailbox"
            :class="{ 'top-nav-mailbox-active': box.id === activeId }"
            @click="emit('select', box.id)"
          >
            <UiAvatar :label="FormatHelper.initials(box.name, box.email)" :color="box.color" size="sm" />
            <span class="max-w-[8rem] truncate text-xs font-semibold">{{ box.name || box.email }}</span>
            <span
              v-if="threadCounts[box.id]"
              class="rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-bold text-white"
            >
              {{ threadCounts[box.id] > 99 ? '99+' : threadCounts[box.id] }}
            </span>
          </button>

          <button
            v-if="isAdmin"
            type="button"
            class="top-nav-mailbox top-nav-mailbox-add"
            title="Добавить ящик"
            @click="emit('add')"
          >
            <AppIcon name="plus" size="sm" />
          </button>
        </div>
      </div>

      <div class="flex shrink-0 items-center gap-0.5 sm:gap-1">
        <button
          type="button"
          class="btn-icon btn-icon-ghost"
          :class="notificationsOn ? 'text-accent-hover' : ''"
          :title="notificationsOn ? 'Уведомления вкл.' : 'Уведомления'"
          @click="emit('toggle-notifications')"
        >
          <AppIcon name="bell" size="sm" />
        </button>

        <button
          type="button"
          class="top-nav-profile hidden sm:flex"
          :title="username || 'Профиль'"
          @click="emit('profile')"
        >
          <UiAvatar :label="FormatHelper.initials(username, username)" size="sm" />
        </button>

        <button
          v-if="isAdmin"
          type="button"
          class="btn-icon btn-icon-ghost hidden md:inline-flex"
          title="Настройки"
          @click="emit('settings')"
        >
          <AppIcon name="settings" size="sm" />
        </button>

        <button
          type="button"
          class="btn-icon btn-icon-ghost hidden lg:inline-flex"
          title="Выйти"
          @click="emit('logout')"
        >
          <AppIcon name="logout" size="sm" />
        </button>
      </div>
    </div>
  </header>
</template>
