/** Утилиты форматирования (класс, ООП). */
export class FormatHelper {
  static formatDate(iso) {
    if (!iso) return ''
    const d = new Date(iso)
    const now = new Date()
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
  }

  static formatFullDate(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('ru-RU')
  }

  static escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text || ''
    return div.innerHTML
  }

  static initials(name, email) {
    const src = (name || email || '?').replace(/<[^>]+>/, '').trim()
    const parts = src.split(/\s+/)
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return src.slice(0, 2).toUpperCase()
  }

  static displaySender(msg, mailbox) {
    const isOut = msg.direction === 'outbound'
    if (isOut) return mailbox?.name || mailbox?.email || 'Вы'
    return (msg.from || '').replace(/<[^>]+>/, '').trim() || msg.from
  }
}

export const format = FormatHelper
