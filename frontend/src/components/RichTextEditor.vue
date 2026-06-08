<script setup>
import { ref, watch, onMounted } from 'vue'
import { HtmlHelper } from '@/services/HtmlHelper'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Текст письма...' },
  minHeight: { type: String, default: '160px' },
})

const emit = defineEmits(['update:modelValue'])

const editor = ref(null)

onMounted(() => {
  if (editor.value && props.modelValue) {
    editor.value.innerHTML = props.modelValue
  }
})

watch(
  () => props.modelValue,
  (val) => {
    if (editor.value && editor.value.innerHTML !== val) {
      editor.value.innerHTML = val || ''
    }
  },
)

function sync() {
  if (!editor.value) return
  emit('update:modelValue', HtmlHelper.sanitize(editor.value.innerHTML))
}

function cmd(command, value = null) {
  editor.value?.focus()
  document.execCommand(command, false, value)
  sync()
}

function insertLink() {
  const url = window.prompt('Ссылка (https://...)', 'https://')
  if (!url) return
  cmd('createLink', url)
}
</script>

<template>
  <div class="overflow-hidden rounded-[10px] border border-border bg-surface-elevated">
    <div class="flex flex-wrap gap-0.5 border-b border-border bg-surface px-2 py-1.5">
      <button type="button" class="toolbar-btn" title="Жирный" @click="cmd('bold')"><strong>B</strong></button>
      <button type="button" class="toolbar-btn" title="Курсив" @click="cmd('italic')"><em>I</em></button>
      <button type="button" class="toolbar-btn" title="Подчёркнутый" @click="cmd('underline')"><span class="underline">U</span></button>
      <span class="mx-1 w-px self-stretch bg-border" />
      <button type="button" class="toolbar-btn" title="Маркированный список" @click="cmd('insertUnorderedList')">•≡</button>
      <button type="button" class="toolbar-btn" title="Нумерованный список" @click="cmd('insertOrderedList')">1.</button>
      <button type="button" class="toolbar-btn" title="Ссылка" @click="insertLink">🔗</button>
    </div>
    <div
      ref="editor"
      contenteditable="true"
      class="editor-body px-3 py-3 text-sm leading-relaxed text-zinc-100 outline-none"
      :style="{ minHeight }"
      :data-placeholder="placeholder"
      @input="sync"
      @blur="sync"
    />
  </div>
</template>

<style scoped>
.toolbar-btn {
  @apply rounded-md px-2.5 py-1 text-xs text-zinc-400 transition hover:bg-surface-hover hover:text-zinc-100;
}
.editor-body:empty::before {
  content: attr(data-placeholder);
  @apply pointer-events-none text-zinc-500;
}
.editor-body :deep(a) {
  @apply text-accent-hover underline;
}
.editor-body :deep(ul) {
  @apply my-2 list-disc pl-5;
}
.editor-body :deep(ol) {
  @apply my-2 list-decimal pl-5;
}
.editor-body :deep(p) {
  @apply mb-2 last:mb-0;
}
</style>
