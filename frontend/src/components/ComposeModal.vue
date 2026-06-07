<script setup>
import { ref, watch } from 'vue'
import { FormatHelper } from '@/services/FormatHelper'

const props = defineProps({
  open: { type: Boolean, default: false },
  mailboxes: { type: Array, default: () => [] },
  activeMailboxId: { type: String, default: null },
})

const emit = defineEmits(['close', 'send'])

const mailboxId = ref('')
const to = ref('')
const cc = ref('')
const bcc = ref('')
const subject = ref('')
const body = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      mailboxId.value = props.activeMailboxId || props.mailboxes[0]?.id || ''
      to.value = ''
      cc.value = ''
      bcc.value = ''
      subject.value = ''
      body.value = ''
    }
  },
)

function submit() {
  emit('send', {
    mailbox_id: mailboxId.value,
    to: to.value,
    cc: cc.value,
    bcc: bcc.value,
    subject: subject.value,
    html: `<p>${FormatHelper.escapeHtml(body.value).replace(/\n/g, '<br>')}</p>`,
    text: body.value,
  })
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[1000] flex items-end justify-center bg-black/65 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[100dvh] w-full animate-slide-up flex-col overflow-hidden border-border bg-surface shadow-2xl sm:max-h-[90vh] sm:max-w-lg sm:rounded-[14px] sm:border">
        <header class="flex shrink-0 items-center justify-between border-b border-border px-4 py-4 sm:px-6 sm:py-5">
          <h2 class="text-[17px] font-bold">Новое письмо</h2>
          <button type="button" class="btn-icon" @click="emit('close')">✕</button>
        </header>

        <form class="flex-1 space-y-3.5 overflow-y-auto p-4 sm:p-6" style="padding-bottom: max(1rem, env(safe-area-inset-bottom));" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">От ящика</span>
            <select v-model="mailboxId" class="input-field" required>
              <option v-for="box in mailboxes" :key="box.id" :value="box.id">
                {{ box.name || box.email }} &lt;{{ box.email }}&gt;
              </option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Кому</span>
            <input v-model="to" type="text" class="input-field" required placeholder="email@example.com" />
          </label>

          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label class="block">
              <span class="mb-1.5 block text-xs font-semibold text-zinc-400">CC</span>
              <input v-model="cc" type="text" class="input-field" placeholder="необязательно" />
            </label>
            <label class="block">
              <span class="mb-1.5 block text-xs font-semibold text-zinc-400">BCC</span>
              <input v-model="bcc" type="text" class="input-field" placeholder="необязательно" />
            </label>
          </div>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Тема</span>
            <input v-model="subject" type="text" class="input-field" required placeholder="Тема письма" />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Сообщение</span>
            <textarea v-model="body" rows="8" class="input-field resize-y" required placeholder="Текст письма..." />
          </label>

          <div class="flex justify-end gap-2.5 pt-2">
            <button type="button" class="btn-secondary" @click="emit('close')">Отмена</button>
            <button type="submit" class="btn-primary">Отправить</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
