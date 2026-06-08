/** Чтение файлов для отправки через Resend (Base64 без data URI). */

const MAX_FILES = 10
const MAX_TOTAL_BYTES = 35 * 1024 * 1024

export class AttachmentHelper {
  static get limits() {
    return { maxFiles: MAX_FILES, maxTotalMb: Math.round(MAX_TOTAL_BYTES / 1024 / 1024) }
  }

  static formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  static async readFiles(fileList) {
    const files = Array.from(fileList || [])
    if (!files.length) return []

    if (files.length > MAX_FILES) {
      throw new Error(`Не более ${MAX_FILES} файлов за раз`)
    }

    const items = []
    let total = 0

    for (const file of files) {
      total += file.size
      if (total > MAX_TOTAL_BYTES) {
        throw new Error(`Общий размер файлов больше ${this.limits.maxTotalMb} МБ`)
      }
      const content = await this._readBase64(file)
      items.push({
        filename: file.name,
        content,
        content_type: file.type || undefined,
        size: file.size,
      })
    }

    return items
  }

  static _readBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const raw = String(reader.result || '')
        const base64 = raw.includes(',') ? raw.split(',')[1] : raw
        resolve(base64)
      }
      reader.onerror = () => reject(new Error(`Не удалось прочитать «${file.name}»`))
      reader.readAsDataURL(file)
    })
  }

  static toPayload(items) {
    return (items || []).map(({ filename, content, content_type }) => ({
      filename,
      content,
      ...(content_type ? { content_type } : {}),
    }))
  }
}
