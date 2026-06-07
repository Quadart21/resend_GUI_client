/**
 * Браузерные push-уведомления о новых входящих (Web Notifications API).
 */
const STORAGE_KEY = 'resend_notifications_enabled'
const SINCE_KEY = 'resend_notifications_since'
const SEEN_KEY = 'resend_notifications_seen'
const POLL_MS = 20_000
const MAX_SEEN = 200

export class NotificationWatcher {
  /**
   * @param {import('./ApiClient').ApiClient} api
   * @param {{ onNewMail?: () => void, onError?: (msg: string) => void }} callbacks
   */
  constructor(api, callbacks = {}) {
    this.api = api
    this.callbacks = callbacks
    this.timer = null
    this.enabled = localStorage.getItem(STORAGE_KEY) === '1'
    this.seenIds = new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || '[]'))
  }

  /** Поддерживает ли браузер системные уведомления */
  static isSupported() {
    return typeof window !== 'undefined' && 'Notification' in window
  }

  isEnabled() {
    return this.enabled && Notification.permission === 'granted'
  }

  permissionState() {
    if (!NotificationWatcher.isSupported()) return 'unsupported'
    return Notification.permission
  }

  /** Запросить разрешение и включить опрос */
  async enable() {
    if (!NotificationWatcher.isSupported()) {
      throw new Error('Браузер не поддерживает уведомления')
    }
    let perm = Notification.permission
    if (perm === 'default') {
      perm = await Notification.requestPermission()
    }
    if (perm !== 'granted') {
      throw new Error('Разрешение на уведомления не получено')
    }
    this.enabled = true
    localStorage.setItem(STORAGE_KEY, '1')
    if (!localStorage.getItem(SINCE_KEY)) {
      localStorage.setItem(SINCE_KEY, new Date().toISOString())
    }
    this.start()
    return true
  }

  disable() {
    this.enabled = false
    localStorage.setItem(STORAGE_KEY, '0')
    this.stop()
  }

  start() {
    this.stop()
    if (!this.isEnabled()) return
    this.check()
    this.timer = setInterval(() => this.check(), POLL_MS)
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  }

  _since() {
    return localStorage.getItem(SINCE_KEY) || new Date().toISOString()
  }

  _persistSince(iso) {
    localStorage.setItem(SINCE_KEY, iso)
  }

  _persistSeen() {
    const arr = [...this.seenIds].slice(-MAX_SEEN)
    this.seenIds = new Set(arr)
    localStorage.setItem(SEEN_KEY, JSON.stringify(arr))
  }

  async check() {
    if (!this.isEnabled()) return
    try {
      const data = await this.api.checkInboundNotifications(this._since())
      let hasNew = false

      for (const item of data.items || []) {
        if (this.seenIds.has(item.email_id)) continue
        this.showNotification(item)
        this.seenIds.add(item.email_id)
        hasNew = true
      }

      if (data.server_time) {
        this._persistSince(data.server_time)
      }
      if (hasNew) {
        this._persistSeen()
        this.callbacks.onNewMail?.()
      }
    } catch (err) {
      this.callbacks.onError?.(err.message)
    }
  }

  showNotification(item) {
    const title = item.subject || 'Новое письмо'
    const from = item.from || 'Неизвестный отправитель'
    const body = `${from}\n${item.preview || item.mailbox_email || ''}`

    const notification = new Notification(title, {
      body,
      tag: item.email_id,
      renotify: true,
      icon: '/favicon.svg',
    })

    notification.onclick = () => {
      window.focus()
      notification.close()
    }
  }
}
