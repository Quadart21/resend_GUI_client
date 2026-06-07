/**
 * Resend GUI Client — фронтенд (ООП).
 * Поддержка нескольких ящиков и цепочек переписки.
 */

/** HTTP-клиент для backend API. */
class ApiClient {
  constructor(baseUrl = "/api") {
    this.baseUrl = baseUrl;
  }

  async request(path, options = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail;
      const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
      throw new Error(msg || `Ошибка ${response.status}`);
    }
    return data;
  }

  getConfig() { return this.request("/config"); }
  saveApiKey(api_key) { return this.request("/config", { method: "POST", body: JSON.stringify({ api_key }) }); }
  listMailboxes() { return this.request("/mailboxes"); }
  createMailbox(name, email) {
    return this.request("/mailboxes", { method: "POST", body: JSON.stringify({ name, email }) });
  }
  updateMailbox(id, name, email) {
    return this.request(`/mailboxes/${id}`, { method: "PUT", body: JSON.stringify({ name, email }) });
  }
  deleteMailbox(id) { return this.request(`/mailboxes/${id}`, { method: "DELETE" }); }
  listThreads(mailboxId) { return this.request(`/mailboxes/${mailboxId}/threads`); }
  getThread(mailboxId, threadId) { return this.request(`/mailboxes/${mailboxId}/threads/${threadId}`); }
  sendEmail(body) { return this.request("/emails/send", { method: "POST", body: JSON.stringify(body) }); }
  replyThread(mailboxId, threadId, body) {
    return this.request(`/mailboxes/${mailboxId}/threads/${threadId}/reply`, {
      method: "POST", body: JSON.stringify(body),
    });
  }
}

/** Форматирование дат и текста. */
class FormatHelper {
  static formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) {
      return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
  }

  static formatFullDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("ru-RU");
  }

  static escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
  }

  static initials(name, email) {
    const src = name || email || "?";
    const parts = src.replace(/<[^>]+>/, "").trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return src.slice(0, 2).toUpperCase();
  }
}

/** Toast-уведомления. */
class ToastService {
  constructor(elementId) {
    this.el = document.getElementById(elementId);
  }

  show(message, type = "success") {
    this.el.textContent = message;
    this.el.className = `toast ${type}`;
    clearTimeout(this._timer);
    this._timer = setTimeout(() => { this.el.className = "toast hidden"; }, 4000);
  }
}

/** Список ящиков в сайдбаре. */
class MailboxSidebar {
  constructor(containerId, onSelect) {
    this.container = document.getElementById(containerId);
    this.onSelect = onSelect;
    this.mailboxes = [];
    this.activeId = null;
    this.threadCounts = {};
  }

  render(mailboxes, activeId, threadCounts = {}) {
    this.mailboxes = mailboxes;
    this.activeId = activeId;
    this.threadCounts = threadCounts;

    if (!mailboxes.length) {
      this.container.innerHTML = `
        <div class="empty-state" style="padding:16px 8px;font-size:12px">
          Добавьте ящик в настройках
        </div>`;
      return;
    }

    this.container.innerHTML = mailboxes.map((box) => {
      const count = threadCounts[box.id] || 0;
      const initials = FormatHelper.initials(box.name, box.email);
      return `
        <button class="mailbox-item${box.id === activeId ? " active" : ""}" data-id="${box.id}">
          <div class="mailbox-avatar" style="background:${box.color}">${initials}</div>
          <div class="mailbox-info">
            <div class="mailbox-name">${FormatHelper.escapeHtml(box.name || box.email)}</div>
            <div class="mailbox-email">${FormatHelper.escapeHtml(box.email)}</div>
          </div>
          ${count ? `<span class="mailbox-count">${count}</span>` : ""}
        </button>`;
    }).join("");

    this.container.querySelectorAll(".mailbox-item").forEach((el) => {
      el.addEventListener("click", () => this.onSelect(el.dataset.id));
    });
  }

  getActive() {
    return this.mailboxes.find((b) => b.id === this.activeId) || null;
  }
}

/** Список цепочек переписки. */
class ThreadListView {
  constructor(containerId, onSelect) {
    this.container = document.getElementById(containerId);
    this.onSelect = onSelect;
    this.threads = [];
    this.activeId = null;
  }

  render(threads) {
    this.threads = threads;
    if (!threads.length) {
      this.container.innerHTML = `<div class="empty-state"><p>Нет переписок</p><p style="font-size:12px;margin-top:6px">Напишите первое письмо или дождитесь входящего</p></div>`;
      return;
    }

    this.container.innerHTML = threads.map((t) => {
      const dirLabel = t.last_direction === "outbound" ? "исх." : "вх.";
      const dirClass = t.last_direction === "outbound" ? "outbound" : "inbound";
      return `
        <div class="thread-item${t.id === this.activeId ? " active" : ""}" data-id="${t.id}">
          <div class="thread-top">
            <span class="thread-correspondent">${FormatHelper.escapeHtml(t.correspondent)}</span>
            <span class="thread-date">${FormatHelper.formatDate(t.last_message_at)}</span>
          </div>
          <div class="thread-subject">${FormatHelper.escapeHtml(t.subject)}</div>
          <div class="thread-preview">${FormatHelper.escapeHtml(t.preview)}</div>
          <div class="thread-footer">
            <span class="thread-count">${t.message_count} сообщ.</span>
            <span class="dir-badge ${dirClass}">${dirLabel}</span>
          </div>
        </div>`;
    }).join("");

    this.container.querySelectorAll(".thread-item").forEach((el) => {
      el.addEventListener("click", () => this.onSelect(el.dataset.id));
    });
  }

  setActive(id) {
    this.activeId = id;
    this.container.querySelectorAll(".thread-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.id === id);
    });
  }

  filter(query) {
    const q = query.toLowerCase();
    return this.threads.filter((t) =>
      [t.subject, t.correspondent, t.preview, ...(t.participants || [])]
        .join(" ").toLowerCase().includes(q)
    );
  }
}

/** Панель переписки (чат-вид). */
class ConversationView {
  constructor() {
    this.emptyEl = document.getElementById("conversation-empty");
    this.contentEl = document.getElementById("conversation-content");
    this.subjectEl = document.getElementById("conv-subject");
    this.metaEl = document.getElementById("conv-meta");
    this.scrollEl = document.getElementById("messages-scroll");
    this.quickReplyEl = document.getElementById("quick-reply");
    this.quickReplyBody = document.getElementById("quick-reply-body");
    this.thread = null;
  }

  showEmpty() {
    this.emptyEl.classList.remove("hidden");
    this.contentEl.classList.add("hidden");
    this.thread = null;
    this.hideQuickReply();
  }

  show(thread, mailbox) {
    this.thread = thread;
    this.emptyEl.classList.add("hidden");
    this.contentEl.classList.remove("hidden");

    this.subjectEl.textContent = thread.subject || "(без темы)";
    this.metaEl.textContent = `${thread.message_count} сообщений · ${thread.participants?.join(", ") || ""}`;

    this.scrollEl.innerHTML = (thread.messages || []).map((msg) => {
      const isOut = msg.direction === "outbound";
      const sender = isOut
        ? (mailbox?.name || mailbox?.email || "Вы")
        : FormatHelper.escapeHtml(msg.from?.replace(/<[^>]+>/, "").trim() || msg.from);
      const body = msg.html
        ? `<div class="message-body">${msg.html}</div>`
        : msg.text
          ? `<div class="message-body"><pre>${FormatHelper.escapeHtml(msg.text)}</pre></div>`
          : `<div class="message-body" style="color:var(--text-muted)">Содержимое недоступно</div>`;

      return `
        <div class="message-bubble ${msg.direction}">
          <div class="message-meta">
            <span class="message-sender">${sender}</span>
            <span class="message-time">${FormatHelper.formatFullDate(msg.created_at)}</span>
            <span class="message-dir">${isOut ? "→ отправлено" : "← получено"}</span>
          </div>
          ${body}
          ${msg.last_event ? `<div class="message-status">Статус: ${msg.last_event}</div>` : ""}
        </div>`;
    }).join("");

    this.scrollEl.scrollTop = this.scrollEl.scrollHeight;
    this.hideQuickReply();
  }

  showQuickReply() {
    this.quickReplyEl.classList.remove("hidden");
    this.quickReplyBody.value = "";
    this.quickReplyBody.focus();
  }

  hideQuickReply() {
    this.quickReplyEl.classList.add("hidden");
    this.quickReplyBody.value = "";
  }
}

/** Модальное окно написания письма. */
class ComposeModal {
  constructor(onSend) {
    this.overlay = document.getElementById("compose-modal");
    this.form = document.getElementById("compose-form");
    this.titleEl = document.getElementById("compose-title");
    this.mailboxSelect = document.getElementById("compose-mailbox");
    this.toInput = document.getElementById("compose-to");
    this.ccInput = document.getElementById("compose-cc");
    this.bccInput = document.getElementById("compose-bcc");
    this.subjectInput = document.getElementById("compose-subject");
    this.bodyInput = document.getElementById("compose-body");
    this.sendBtn = document.getElementById("btn-send");
    this.onSend = onSend;
    this.mode = "new";

    this.form.addEventListener("submit", (e) => this._submit(e));
  }

  populateMailboxes(mailboxes, activeId) {
    this.mailboxSelect.innerHTML = mailboxes.map((b) =>
      `<option value="${b.id}"${b.id === activeId ? " selected" : ""}>${FormatHelper.escapeHtml(b.name || b.email)} &lt;${b.email}&gt;</option>`
    ).join("");
  }

  openNew(mailboxes, activeMailboxId) {
    this.mode = "new";
    this.titleEl.textContent = "Новое письмо";
    this.form.reset();
    this.populateMailboxes(mailboxes, activeMailboxId);
    this.toInput.disabled = false;
    this.subjectInput.disabled = false;
    this.overlay.classList.remove("hidden");
  }

  close() {
    this.overlay.classList.add("hidden");
  }

  async _submit(e) {
    e.preventDefault();
    this.sendBtn.disabled = true;
    try {
      await this.onSend({
        mailbox_id: this.mailboxSelect.value,
        to: this.toInput.value,
        cc: this.ccInput.value,
        bcc: this.bccInput.value,
        subject: this.subjectInput.value,
        html: `<p>${FormatHelper.escapeHtml(this.bodyInput.value).replace(/\n/g, "<br>")}</p>`,
        text: this.bodyInput.value,
      });
      this.close();
    } finally {
      this.sendBtn.disabled = false;
    }
  }
}

/** Модальное окно настроек. */
class SettingsModal {
  constructor(api, toast, onMailboxesChanged) {
    this.overlay = document.getElementById("settings-modal");
    this.apiForm = document.getElementById("settings-api-form");
    this.apiKeyInput = document.getElementById("settings-api-key");
    this.apiKeyHint = document.getElementById("api-key-hint");
    this.mailboxesEl = document.getElementById("settings-mailboxes");
    this.mailboxForm = document.getElementById("settings-mailbox-form");
    this.api = api;
    this.toast = toast;
    this.onMailboxesChanged = onMailboxesChanged;

    this.apiForm.addEventListener("submit", (e) => this._saveApiKey(e));
    this.mailboxForm.addEventListener("submit", (e) => this._addMailbox(e));
  }

  async open() {
    this.overlay.classList.remove("hidden");
    await this.load();
  }

  close() {
    this.overlay.classList.add("hidden");
  }

  async load() {
    const cfg = await this.api.getConfig();
    this.apiKeyHint.textContent = cfg.has_api_key
      ? `Текущий: ${cfg.api_key_preview} (оставьте пустым, чтобы не менять)`
      : "Ключ ещё не задан";
    this.renderMailboxes(cfg.mailboxes || []);
  }

  renderMailboxes(mailboxes) {
    if (!mailboxes.length) {
      this.mailboxesEl.innerHTML = `<p class="hint">Ящиков пока нет</p>`;
      return;
    }
    this.mailboxesEl.innerHTML = mailboxes.map((b) => {
      const initials = FormatHelper.initials(b.name, b.email);
      return `
        <div class="settings-mailbox-item" data-id="${b.id}">
          <div class="mailbox-avatar" style="background:${b.color}">${initials}</div>
          <div class="info">
            <div class="name">${FormatHelper.escapeHtml(b.name || b.email)}</div>
            <div class="email">${FormatHelper.escapeHtml(b.email)}</div>
          </div>
          <button type="button" class="danger-btn" data-delete="${b.id}">Удалить</button>
        </div>`;
    }).join("");

    this.mailboxesEl.querySelectorAll("[data-delete]").forEach((btn) => {
      btn.addEventListener("click", () => this._deleteMailbox(btn.dataset.delete));
    });
  }

  async _saveApiKey(e) {
    e.preventDefault();
    await this.api.saveApiKey(this.apiKeyInput.value);
    this.apiKeyInput.value = "";
    this.toast.show("API-ключ сохранён", "success");
    await this.load();
  }

  async _addMailbox(e) {
    e.preventDefault();
    const name = document.getElementById("new-mailbox-name").value;
    const email = document.getElementById("new-mailbox-email").value;
    try {
      await this.api.createMailbox(name, email);
      this.mailboxForm.reset();
      this.toast.show("Ящик добавлен", "success");
      await this.load();
      await this.onMailboxesChanged();
    } catch (err) {
      this.toast.show(err.message, "error");
    }
  }

  async _deleteMailbox(id) {
    if (!confirm("Удалить этот ящик?")) return;
    await this.api.deleteMailbox(id);
    this.toast.show("Ящик удалён", "success");
    await this.load();
    await this.onMailboxesChanged();
  }
}

/** Главный контроллер приложения. */
class MailApp {
  constructor() {
    this.api = new ApiClient();
    this.toast = new ToastService("toast");
    this.mailboxSidebar = new MailboxSidebar("mailbox-list", (id) => this.selectMailbox(id));
    this.threadList = new ThreadListView("thread-list", (id) => this.openThread(id));
    this.conversation = new ConversationView();
    this.composeModal = new ComposeModal((payload) => this.sendMail(payload));
    this.settingsModal = new SettingsModal(this.api, this.toast, () => this.reloadMailboxes());

    this.mailboxes = [];
    this.activeMailboxId = null;
    this.threads = [];
    this.activeThreadId = null;

    this._bindEvents();
    this.init();
  }

  _bindEvents() {
    document.getElementById("btn-compose").addEventListener("click", () => this.openCompose());
    document.getElementById("btn-refresh").addEventListener("click", () => this.loadThreads());
    document.getElementById("btn-settings").addEventListener("click", () => this.settingsModal.open());
    document.getElementById("btn-close-settings").addEventListener("click", () => this.settingsModal.close());
    document.getElementById("btn-close-compose").addEventListener("click", () => this.composeModal.close());
    document.getElementById("btn-cancel-compose").addEventListener("click", () => this.composeModal.close());
    document.getElementById("btn-add-mailbox").addEventListener("click", () => this.settingsModal.open());
    document.getElementById("btn-reply").addEventListener("click", () => this.conversation.showQuickReply());
    document.getElementById("btn-cancel-quick-reply").addEventListener("click", () => this.conversation.hideQuickReply());
    document.getElementById("btn-send-quick-reply").addEventListener("click", () => this.sendQuickReply());
    document.getElementById("search-input").addEventListener("input", (e) => {
      this.threadList.render(this.threadList.filter(e.target.value));
    });

    [this.composeModal.overlay, this.settingsModal.overlay].forEach((overlay) => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.classList.add("hidden");
      });
    });
  }

  async init() {
    try {
      const cfg = await this.api.getConfig();
      this.mailboxes = cfg.mailboxes || [];
      if (this.mailboxes.length) {
        this.activeMailboxId = this.mailboxes[0].id;
      }
      this.renderMailboxes();
      if (this.activeMailboxId) await this.loadThreads();
      else this.threadList.render([]);
    } catch (err) {
      this.toast.show(err.message, "error");
    }
  }

  async reloadMailboxes() {
    const cfg = await this.api.getConfig();
    this.mailboxes = cfg.mailboxes || [];
    if (!this.mailboxes.find((b) => b.id === this.activeMailboxId)) {
      this.activeMailboxId = this.mailboxes[0]?.id || null;
    }
    this.renderMailboxes();
    if (this.activeMailboxId) await this.loadThreads();
  }

  renderMailboxes() {
    const counts = {};
    if (this.threads.length && this.activeMailboxId) {
      counts[this.activeMailboxId] = this.threads.length;
    }
    this.mailboxSidebar.render(this.mailboxes, this.activeMailboxId, counts);
    this._updateMailboxBadge();
  }

  _updateMailboxBadge() {
    const box = this.mailboxSidebar.getActive();
    const badge = document.getElementById("active-mailbox-badge");
    if (!box) {
      badge.innerHTML = `<span style="color:var(--text-muted)">Выберите ящик</span>`;
      return;
    }
    badge.innerHTML = `
      <span class="badge-dot" style="background:${box.color}"></span>
      <span>${FormatHelper.escapeHtml(box.email)}</span>`;
  }

  async selectMailbox(id) {
    this.activeMailboxId = id;
    this.activeThreadId = null;
    this.conversation.showEmpty();
    this.renderMailboxes();
    await this.loadThreads();
  }

  async loadThreads() {
    if (!this.activeMailboxId) return;
    const listEl = document.getElementById("thread-list");
    listEl.innerHTML = `<div class="empty-state"><div class="spinner"></div><p>Загрузка...</p></div>`;

    try {
      const data = await this.api.listThreads(this.activeMailboxId);
      this.threads = data.threads || [];
      this.threadList.render(this.threads);
      this.renderMailboxes();
    } catch (err) {
      this.toast.show(err.message, "error");
      this.threadList.render([]);
    }
  }

  async openThread(threadId) {
    if (!this.activeMailboxId) return;
    try {
      const thread = await this.api.getThread(this.activeMailboxId, threadId);
      this.activeThreadId = threadId;
      this.threadList.setActive(threadId);
      const mailbox = this.mailboxSidebar.getActive();
      this.conversation.show(thread, mailbox);
    } catch (err) {
      this.toast.show(err.message, "error");
    }
  }

  openCompose() {
    if (!this.mailboxes.length) {
      this.toast.show("Сначала добавьте почтовый ящик в настройках", "error");
      this.settingsModal.open();
      return;
    }
    this.composeModal.openNew(this.mailboxes, this.activeMailboxId);
  }

  async sendMail(payload) {
    try {
      await this.api.sendEmail(payload);
      this.toast.show("Письмо отправлено", "success");
      await this.loadThreads();
    } catch (err) {
      this.toast.show(err.message, "error");
      throw err;
    }
  }

  async sendQuickReply() {
    const body = this.conversation.quickReplyBody.value.trim();
    if (!body || !this.activeThreadId || !this.activeMailboxId) return;

    const btn = document.getElementById("btn-send-quick-reply");
    btn.disabled = true;
    try {
      await this.api.replyThread(this.activeMailboxId, this.activeThreadId, {
        mailbox_id: this.activeMailboxId,
        html: `<p>${FormatHelper.escapeHtml(body).replace(/\n/g, "<br>")}</p>`,
        text: body,
      });
      this.toast.show("Ответ отправлен", "success");
      await this.openThread(this.activeThreadId);
      await this.loadThreads();
    } catch (err) {
      this.toast.show(err.message, "error");
    } finally {
      btn.disabled = false;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new MailApp();
});
