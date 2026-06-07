/**
 * HTTP-клиент для backend API (класс, ООП).
 */
export class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl
  }

  async request(path, options = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const detail = data.detail
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new Error(msg || `Ошибка ${response.status}`)
    }
    return data
  }

  login(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  }

  logout() {
    return this.request('/auth/logout', { method: 'POST' })
  }

  me() {
    return this.request('/auth/me')
  }

  listUsers() {
    return this.request('/users')
  }

  createUser(body) {
    return this.request('/users', { method: 'POST', body: JSON.stringify(body) })
  }

  updateUser(id, body) {
    return this.request(`/users/${id}`, { method: 'PUT', body: JSON.stringify(body) })
  }

  deleteUser(id) {
    return this.request(`/users/${id}`, { method: 'DELETE' })
  }

  getConfig() {
    return this.request('/config')
  }

  saveApiKey(api_key) {
    return this.request('/config', { method: 'POST', body: JSON.stringify({ api_key }) })
  }

  createMailbox(name, email) {
    return this.request('/mailboxes', { method: 'POST', body: JSON.stringify({ name, email }) })
  }

  deleteMailbox(id) {
    return this.request(`/mailboxes/${id}`, { method: 'DELETE' })
  }

  listThreads(mailboxId) {
    return this.request(`/mailboxes/${mailboxId}/threads`)
  }

  getThread(mailboxId, threadId) {
    return this.request(`/mailboxes/${mailboxId}/threads/${threadId}`)
  }

  sendEmail(body) {
    return this.request('/emails/send', { method: 'POST', body: JSON.stringify(body) })
  }

  replyThread(mailboxId, threadId, body) {
    return this.request(`/mailboxes/${mailboxId}/threads/${threadId}/reply`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  checkInboundNotifications(since) {
    const q = encodeURIComponent(since)
    return this.request(`/notifications/inbound?since=${q}`)
  }
}

/** Единственный экземпляр клиента для всего приложения */
export const api = new ApiClient()
