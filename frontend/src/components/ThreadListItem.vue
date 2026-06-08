<script setup>
import { FormatHelper } from '@/services/FormatHelper'
import AppIcon from '@/components/ui/AppIcon.vue'
import UiBadge from '@/components/ui/UiBadge.vue'

defineProps({
  thread: { type: Object, required: true },
  active: { type: Boolean, default: false },
  showMailbox: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'star'])
</script>

<template>
  <button
    type="button"
    class="thread-item group"
    :class="{
      'thread-item-active': active,
      'thread-item-unread': thread.is_unread,
      'border-l-2 border-l-warning/70 pl-[calc(1rem-2px)]': thread.is_starred,
    }"
    @click="emit('select', thread.id, thread.mailbox_id)"
  >
    <div class="flex items-start gap-3">
      <div
        class="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full text-[11px] font-bold text-white"
        :class="thread.is_unread ? 'bg-gradient-to-br from-accent to-brand-700' : 'bg-surface-active text-muted ring-1 ring-border'"
      >
        {{ FormatHelper.initials(thread.correspondent, thread.correspondent) }}
      </div>

      <div class="min-w-0 flex-1">
        <div class="mb-0.5 flex items-baseline justify-between gap-2">
          <span
            class="truncate text-[13px]"
            :class="thread.is_unread ? 'font-bold text-zinc-50' : 'font-semibold text-zinc-200'"
          >
            {{ thread.correspondent }}
          </span>
          <span
            class="shrink-0 text-[11px] tabular-nums"
            :class="thread.is_unread ? 'font-semibold text-accent-hover' : 'text-muted'"
          >
            {{ FormatHelper.formatDate(thread.last_message_at) }}
          </span>
        </div>

        <div
          class="truncate text-[13px] leading-snug"
          :class="thread.is_unread ? 'font-medium text-zinc-200' : 'text-zinc-400'"
        >
          {{ thread.subject }}
        </div>

        <div class="mt-0.5 truncate text-xs text-muted">
          {{ thread.preview }}
        </div>

        <div class="mt-2 flex flex-wrap items-center gap-1.5">
          <UiBadge v-if="showMailbox && thread.mailbox_name" variant="neutral">
            <span
              v-if="thread.mailbox_color"
              class="mr-1 inline-block h-1.5 w-1.5 rounded-full"
              :style="{ background: thread.mailbox_color }"
            />
            {{ thread.mailbox_name }}
          </UiBadge>
          <UiBadge v-if="thread.is_unread && thread.unread_count" variant="accent">
            {{ thread.unread_count }} нов.
          </UiBadge>
          <UiBadge v-if="thread.is_starred" variant="warning">важное</UiBadge>
          <UiBadge :variant="thread.last_direction === 'outbound' ? 'brand' : 'success'">
            {{ thread.last_direction === 'outbound' ? 'исх.' : 'вх.' }}
          </UiBadge>
        </div>
      </div>

      <button
        type="button"
        class="mt-1 shrink-0 rounded-lg p-1.5 text-muted opacity-100 transition hover:bg-surface-active hover:text-warning sm:opacity-0 sm:group-hover:opacity-100"
        :class="thread.is_starred ? 'text-warning opacity-100' : ''"
        :title="thread.is_starred ? 'Убрать из важных' : 'Пометить как важное'"
        @click.stop="emit('star', thread.id, !thread.is_starred, thread.mailbox_id)"
      >
        <AppIcon name="star" :filled="thread.is_starred" size="sm" />
      </button>
    </div>
  </button>
</template>
