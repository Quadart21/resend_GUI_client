<script setup>
import { ref, watch, computed } from 'vue'
import { HtmlHelper } from '@/services/HtmlHelper'
import { AttachmentHelper } from '@/services/AttachmentHelper'
import RichTextEditor from '@/components/RichTextEditor.vue'
import UiModal from '@/components/ui/UiModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

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
  <UiModal :open="open" title="Новое письмо" size="lg" @close="emit('close')">
    <form id="compose-form" class="space-y-4" @submit.prevent="submit">
      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block sm:col-span-2">
          <span class="field-label">От ящика</span>
          <select v-model="mailboxId" class="input-field" required>
            <option v-for="box in mailboxes" :key="box.id" :value="box.id">
              {{ box.name || box.email }} &lt;{{ box.email }}&gt;
            </option>
          </select>
        </label>
        <label class="block sm:col-span-2">
          <span class="field-label">Кому</span>
          <input v-model="to" type="text" class="input-field" required placeholder="email@example.com" />
        </label>
        <label class="block sm:col-span-2">
          <span class="field-label">Тема</span>
          <input v-model="subject" type="text" class="input-field" required placeholder="Тема письма" />
        </label>
      </div>

      <label class="block">
        <span class="field-label">Сообщение</span>
        <RichTextEditor v-model="bodyHtml" placeholder="Текст письма..." min-height="200px" />
        <p v-if="activeMailbox?.signature" class="mt-2 text-[11px] text-muted">
          Подпись будет добавлена: <span class="text-zinc-400">{{ activeMailbox.signature }}</span>
        </p>
      </label>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <span class="field-label mb-0">Вложения</span>
          <span class="text-[10px] text-muted">до {{ limits.maxFiles }} файлов, {{ limits.maxTotalMb }} МБ</span>
        </div>
        <input ref="fileInput" type="file" multiple class="hidden" @change="onFilesSelected" />
        <button
          type="button"
          class="btn-secondary"
          :disabled="picking || attachments.length >= limits.maxFiles"
          @click="fileInput?.click()"
        >
          <AppIcon name="attach" size="sm" />
          {{ picking ? 'Загрузка...' : 'Прикрепить файлы' }}
        </button>
        <ul v-if="attachments.length" class="mt-2 space-y-1.5">
          <li
            v-for="(file, index) in attachments"
            :key="`${file.filename}-${index}`"
            class="flex items-center justify-between gap-2 rounded-xl border border-border bg-surface-elevated px-3 py-2 text-sm"
          >
            <div class="min-w-0">
              <div class="truncate font-medium">{{ file.filename }}</div>
              <div class="text-[11px] text-muted">{{ AttachmentHelper.formatSize(file.size) }}</div>
            </div>
            <button type="button" class="text-danger text-xs" @click="removeAttachment(index)">Убрать</button>
          </li>
        </ul>
      </div>
    </form>

    <template #footer>
      <button type="button" class="btn-secondary" @click="emit('close')">Отмена</button>
      <button type="submit" form="compose-form" class="btn-primary">Отправить</button>
    </template>
  </UiModal>
</template>

<style scoped>
.field-label {
  @apply mb-1.5 block text-xs font-semibold text-muted;
}
</style>
