/** Простая работа с HTML из rich-text редактора. */

export class HtmlHelper {
  static toPlainText(html) {
    if (!html) return ''
    const div = document.createElement('div')
    div.innerHTML = html
    return (div.textContent || div.innerText || '').replace(/\u00a0/g, ' ').trim()
  }

  static isEmpty(html) {
    return !this.toPlainText(html)
  }

  static sanitize(html) {
    if (!html) return ''
    const allowed = new Set([
      'B', 'STRONG', 'I', 'EM', 'U', 'A', 'UL', 'OL', 'LI', 'P', 'BR', 'DIV', 'SPAN',
    ])
    const doc = new DOMParser().parseFromString(html, 'text/html')
    const walk = (node) => {
      ;[...node.childNodes].forEach((child) => {
        if (child.nodeType === Node.ELEMENT_NODE) {
          if (!allowed.has(child.tagName)) {
            const text = document.createTextNode(child.textContent || '')
            child.replaceWith(text)
            return
          }
          ;[...child.attributes].forEach((attr) => {
            if (child.tagName === 'A' && attr.name === 'href') return
            child.removeAttribute(attr.name)
          })
          if (child.tagName === 'A' && child.getAttribute('href')?.startsWith('javascript:')) {
            child.removeAttribute('href')
          }
        }
        walk(child)
      })
    }
    walk(doc.body)
    return doc.body.innerHTML.trim()
  }
}
