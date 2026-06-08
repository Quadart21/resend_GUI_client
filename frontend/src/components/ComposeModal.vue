<script setup>
import { ref, watch, computed } from 'vue'
import { HtmlHelper } from '@/services/HtmlHelper'
import { AttachmentHelper } from '@/services/AttachmentHelper'
import RichTextEditor from '@/components/RichTextEditor.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  mailboxes: { type: Array, default: () => [] },
  activeMailboxId: { type: String, default: null },
})

const emit = defineEmits(['close', 'send', 'notify'])

const mailboxId = ref('')
const to = ref('')
const subject = ref('')
const bodyHtml = ref('')
const attachments = ref([])
const picking = ref(false)
const fileInput = ref(null)

const limits = AttachmentHelper.limits

const activeMailbox = computed(() =>
  props.mailboxes.find((b) => b.id === mailboxId.value) || null,
)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      mailboxId.value = props.activeMailboxId || props.mailboxes[0]?.id || ''
      to.value = ''
      subject.value = ''
      bodyHtml.value = ''
      attachments.value = []
    }
  },
)

async function onFilesSelected(event) {
  const input = event.target
  picking.value = true
  try {
    const items = await AttachmentHelper.readFiles(input.files)
    attachments.value = [...attachments.value, ...items].slice(0, limits.maxFiles)
  } catch (err) {
    emit('notify', err.message, 'error')
  } finally {
    picking.value = false
    if (input) input.value = ''
  }
}

function removeAttachment(index) {
  attachments.value = attachments.value.filter((_, i) => i !== index)
}

function submit() {
  const hasBody = !HtmlHelper.isEmpty(bodyHtml.value)
  const hasFiles = attachments.value.length > 0
  if (!hasBody && !hasFiles) {
    emit('notify', 'Укажите текст или прикрепите файл', 'error')
    return
  }

  const html = hasBody ? HtmlHelper.sanitize(bodyHtml.value) : '<p></p>'

  emit('send', {
    mailbox_id: mailboxId.value,
    to: to.value,
    subject: subject.value,
    html,
    text: hasBody ? HtmlHelper.toPlainText(html) : '',
    attachments: AttachmentHelper.toPayload(attachments.value),
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

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Тема</span>
            <input v-model="subject" type="text" class="input-field" required placeholder="Тема письма" />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-xs font-semibold text-zinc-400">Сообщение</span>
            <RichTextEditor v-model="bodyHtml" placeholder="Текст письма..." min-height="180px" />
            <p
              v-if="activeMailbox?.signature"
              class="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-zinc-500"
            >
              Подпись ящика будет добавлена автоматически:<br>
              <span class="text-zinc-400">{{ activeMailbox.signature }}</span>
            </p>
          </label>

          <div class="block">
            <div class="mb-1.5 flex items-center justify-between gap-2">
              <span class="text-xs font-semibold text-zinc-400">Вложения</span>
              <span class="text-[10px] text-zinc-500">до {{ limits.maxFiles }} файлов, {{ limits.maxTotalMb }} МБ</span>
            </div>

            <input
              ref="fileInput"
              type="file"
              multiple
              class="hidden"
              @change="onFilesSelected"
            />

            <button
              type="button"
              class="btn-secondary w-full sm:w-auto"
              :disabled="picking || attachments.length >= limits.maxFiles"
              @click="fileInput?.click()"
            >
              {{ picking ? 'Загрузка...' : 'Прикрепить файлы' }}
            </button>

            <ul v-if="attachments.length" class="mt-2 space-y-1.5">
              <li
                v-for="(file, index) in attachments"
                :key="`${file.filename}-${index}`"
                class="flex items-center justify-between gap-2 rounded-lg border border-border bg-surface-elevated px-3 py-2 text-sm"
              >
                <div class="min-w-0">
                  <div class="truncate font-medium text-zinc-200">{{ file.filename }}</div>
                  <div class="text-[11px] text-zinc-500">{{ AttachmentHelper.formatSize(file.size) }}</div>
                </div>
                <button type="button" class="btn-ghost shrink-0 px-2 py-1 text-xs text-red-400" @click="removeAttachment(index)">
                  Убрать
                </button>
              </li>
            </ul>
          </div>

          <div class="flex justify-end gap-2.5 pt-2">
            <button type="button" class="btn-secondary" @click="emit('close')">Отмена</button>
            <button type="submit" class="btn-primary">Отправить</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
