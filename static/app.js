/**
 * Resend GUI Client — фронтенд на классах (ООП).
 * Каждый класс отвечает за одну область интерфейса.
 */

/** Утилита для HTTP-запросов к backend API. */
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
      throw new Error(data.detail || `Ошибка ${response.status}`);
    }
    return data;
  }

  getConfig() { return this.request("/config"); }
  saveConfig(body) { return this.request("/config", { method: "POST", body: JSON.stringify(body) }); }
  sendEmail(body) { return this.request("/emails/send", { method: "POST", body: JSON.stringify(body) }); }
  listSent(after) { return this.request(after ? `/emails/sent?after=${after}` : "/emails/sent"); }
  getSent(id) { return this.request(`/emails/sent/${id}`); }
  listReceived(after) { return this.request(after ? `/emails/received?after=${after}` : "/emails/received"); }
  getReceived(id) { return this.request(`/emails/received/${id}`); }
  reply(id, body) { return this.request(`/emails/received/${id}/reply`, { method: "POST", body: JSON.stringify(body) }); }
}

/** Вспомогательные функции форматирования. */
class FormatHelper {
  static formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("ru-RU");
  }

  static joinAddresses(value) {
    if (!value) return "—";
    if (Array.isArray(value)) return value.join(", ");
    return value;
  }

  static escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

/** Уведомления (toast). */
class ToastService {
  constructor(elementId) {
    this.el = document.getElementById(elementId);
  }

  show(message, type = "success") {
    this.el.textContent = message;
    this.el.className = `toast ${type}`;
    clearTimeout(this._timer);
    this._timer = setTimeout(() => {
      this.el.className = "toast hidden";
    }, 4000);
  }
}

/** Управление списком писем. */
class MailListView {
  constructor(containerId, onSelect) {
    this.container = document.getElementById(containerId);
    this.onSelect = onSelect;
    this.items = [];
    this.activeId = null;
  }

  render(items, viewType) {
    this.items = items;
    if (!items.length) {
      this.container.innerHTML = '<div class="empty-state">Писем нет</div>';
      return;
    }

    this.container.innerHTML = items.map((item) => {
      const subject = FormatHelper.escapeHtml(item.subject || "(без темы)");
      const peer = viewType === "inbox" ? item.from : FormatHelper.joinAddresses(item.to);
      const meta = viewType === "sent" && item.last_event
        ? `<span class="status">${item.last_event}</span>`
        : "";
      return `
        <div class="email-item${item.id === this.activeId ? " active" : ""}" data-id="${item.id}">
          <div class="subject">${subject}</div>
          <div class="meta">
            <span>${FormatHelper.escapeHtml(peer)}</span>
            <span>${FormatHelper.formatDate(item.created_at)} ${meta}</span>
          </div>
        </div>`;
    }).join("");

    this.container.querySelectorAll(".email-item").forEach((el) => {
      el.addEventListener("click", () => this.onSelect(el.dataset.id));
    });
  }

  setActive(id) {
    this.activeId = id;
    this.container.querySelectorAll(".email-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.id === id);
    });
  }

  filter(query) {
    const q = query.toLowerCase();
    return this.items.filter((item) => {
      const haystack = [
        item.subject,
        item.from,
        ...(Array.isArray(item.to) ? item.to : [item.to]),
      ].join(" ").toLowerCase();
      return haystack.includes(q);
    });
  }
}

/** Панель просмотра письма. */
class MailDetailView {
  constructor() {
    this.emptyEl = document.getElementById("detail-empty");
    this.contentEl = document.getElementById("detail-content");
    this.subjectEl = document.getElementById("detail-subject");
    this.fromEl = document.getElementById("detail-from");
    this.toEl = document.getElementById("detail-to");
    this.dateEl = document.getElementById("detail-date");
    this.statusRow = document.getElementById("detail-status-row");
    this.statusEl = document.getElementById("detail-status");
    this.bodyEl = document.getElementById("detail-body");
    this.replyBtn = document.getElementById("btn-reply");
    this.currentId = null;
    this.viewType = "inbox";
  }

  showEmpty() {
    this.emptyEl.classList.remove("hidden");
    this.contentEl.classList.add("hidden");
    this.currentId = null;
  }

  show(email, viewType) {
    this.currentId = email.id;
    this.viewType = viewType;
    this.emptyEl.classList.add("hidden");
    this.contentEl.classList.remove("hidden");

    this.subjectEl.textContent = email.subject || "(без темы)";
    this.fromEl.textContent = FormatHelper.joinAddresses(email.from);
    this.toEl.textContent = FormatHelper.joinAddresses(email.to);
    this.dateEl.textContent = FormatHelper.formatDate(email.created_at);

    if (viewType === "sent" && email.last_event) {
      this.statusRow.classList.remove("hidden");
      this.statusEl.textContent = email.last_event;
    } else {
      this.statusRow.classList.add("hidden");
    }

    if (email.html) {
      this.bodyEl.innerHTML = email.html;
    } else if (email.text) {
      this.bodyEl.innerHTML = `<pre>${FormatHelper.escapeHtml(email.text)}</pre>`;
    } else {
      this.bodyEl.innerHTML = '<p style="color:var(--muted)">Содержимое недоступно</p>';
    }

    this.replyBtn.classList.toggle("hidden", viewType !== "inbox");
  }
}

/** Форма написания / ответа на письмо. */
class ComposeView {
  constructor(onSend) {
    this.panel = document.getElementById("compose-panel");
    this.form = document.getElementById("compose-form");
    this.titleEl = document.getElementById("compose-title");
    this.toInput = document.getElementById("compose-to");
    this.ccInput = document.getElementById("compose-cc");
    this.bccInput = document.getElementById("compose-bcc");
    this.subjectInput = document.getElementById("compose-subject");
    this.bodyInput = document.getElementById("compose-body");
    this.sendBtn = document.getElementById("btn-send");
    this.format = "html";
    this.replyMode = false;
    this.replyId = null;
    this.onSend = onSend;

    this.form.addEventListener("submit", (e) => this._handleSubmit(e));
    document.querySelectorAll(".toggle-btn").forEach((btn) => {
      btn.addEventListener("click", () => this._setFormat(btn.dataset.format));
    });
  }

  _setFormat(format) {
    this.format = format;
    document.querySelectorAll(".toggle-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.format === format);
    });
    this.bodyInput.placeholder = format === "html" ? "<p>Привет!</p>" : "Текст письма...";
  }

  openNew() {
    this.replyMode = false;
    this.replyId = null;
    this.titleEl.textContent = "Новое письмо";
    this.form.reset();
    this.toInput.disabled = false;
    this.subjectInput.disabled = false;
    this._setFormat("html");
    this.panel.classList.remove("hidden");
  }

  openReply(emailId, to, subject) {
    this.replyMode = true;
    this.replyId = emailId;
    this.titleEl.textContent = "Ответ";
    this.toInput.value = to;
    this.toInput.disabled = true;
    this.subjectInput.value = subject.startsWith("Re:") ? subject : `Re: ${subject}`;
    this.subjectInput.disabled = true;
    this.bodyInput.value = "";
    this._setFormat("html");
    this.panel.classList.remove("hidden");
  }

  close() {
    this.panel.classList.add("hidden");
  }

  async _handleSubmit(e) {
    e.preventDefault();
    this.sendBtn.disabled = true;
    try {
      await this.onSend(this.getPayload());
      this.close();
    } finally {
      this.sendBtn.disabled = false;
    }
  }

  getPayload() {
    const body = this.bodyInput.value;
    return {
      replyMode: this.replyMode,
      replyId: this.replyId,
      to: this.toInput.value,
      cc: this.ccInput.value,
      bcc: this.bccInput.value,
      subject: this.subjectInput.value,
      html: this.format === "html" ? body : "",
      text: this.format === "text" ? body : "",
    };
  }
}

/** Форма настроек. */
class SettingsView {
  constructor(api, toast) {
    this.panel = document.getElementById("settings-panel");
    this.form = document.getElementById("settings-form");
    this.apiKeyInput = document.getElementById("settings-api-key");
    this.fromEmailInput = document.getElementById("settings-from-email");
    this.fromNameInput = document.getElementById("settings-from-name");
    this.apiKeyHint = document.getElementById("api-key-hint");
    this.fromPreview = document.getElementById("from-preview");
    this.api = api;
    this.toast = toast;

    this.form.addEventListener("submit", (e) => this._handleSubmit(e));
  }

  async load() {
    const cfg = await this.api.getConfig();
    this.fromEmailInput.value = cfg.from_email || "";
    this.fromNameInput.value = cfg.from_name || "";
    this.apiKeyHint.textContent = cfg.has_api_key
      ? `Текущий ключ: ${cfg.api_key_preview} (оставьте пустым, чтобы не менять)`
      : "Ключ ещё не задан";
    this._updatePreview(cfg);
  }

  _updatePreview(cfg) {
    const name = cfg.from_name || this.fromNameInput.value;
    const email = cfg.from_email || this.fromEmailInput.value;
    this.fromPreview.textContent = email
      ? (name ? `${name} <${email}>` : email)
      : "Настройте домен";
  }

  show() {
    this.panel.classList.remove("hidden");
    this.load();
  }

  hide() {
    this.panel.classList.add("hidden");
  }

  async _handleSubmit(e) {
    e.preventDefault();
    const saved = await this.api.saveConfig({
      api_key: this.apiKeyInput.value,
      from_email: this.fromEmailInput.value,
      from_name: this.fromNameInput.value,
    });
    this.apiKeyInput.value = "";
    this.toast.show("Настройки сохранены", "success");
    this._updatePreview(saved);
    await this.load();
  }
}

/** Главный контроллер приложения. */
class MailApp {
  constructor() {
    this.api = new ApiClient();
    this.toast = new ToastService("toast");
    this.listView = new MailListView("email-list", (id) => this.openEmail(id));
    this.detailView = new MailDetailView();
    this.composeView = new ComposeView((payload) => this.sendMail(payload));
    this.settingsView = new SettingsView(this.api, this.toast);

    this.currentView = "inbox";
    this.allItems = [];
    this.paginationAfter = null;
    this.hasMore = false;

    this._bindEvents();
    this.init();
  }

  _bindEvents() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => this.switchView(btn.dataset.view));
    });
    document.getElementById("btn-compose").addEventListener("click", () => this.openCompose());
    document.getElementById("btn-refresh").addEventListener("click", () => this.loadList());
    document.getElementById("btn-load-more").addEventListener("click", () => this.loadMore());
    document.getElementById("btn-close-compose").addEventListener("click", () => this.composeView.close());
    document.getElementById("btn-cancel-compose").addEventListener("click", () => this.composeView.close());
    document.getElementById("btn-reply").addEventListener("click", () => this.openReply());
    document.getElementById("search-input").addEventListener("input", (e) => {
      this.listView.render(this.listView.filter(e.target.value), this.currentView);
    });
  }

  async init() {
    await this.settingsView.load();
    await this.loadList();
  }

  switchView(view) {
    this.currentView = view;
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === view);
    });

    const listPanel = document.getElementById("list-panel");
    const detailPanel = document.getElementById("detail-panel");
    this.composeView.close();
    this.settingsView.hide();

    if (view === "settings") {
      listPanel.classList.add("hidden");
      detailPanel.classList.add("hidden");
      this.settingsView.show();
      return;
    }

    listPanel.classList.remove("hidden");
    detailPanel.classList.remove("hidden");
    document.getElementById("list-title").textContent = view === "inbox" ? "Входящие" : "Отправленные";
    this.detailView.showEmpty();
    this.paginationAfter = null;
    this.loadList();
  }

  async loadList() {
    this.paginationAfter = null;
    try {
      const data = this.currentView === "inbox"
        ? await this.api.listReceived()
        : await this.api.listSent();
      this.allItems = data.data || [];
      this.hasMore = data.has_more || false;
      this.listView.render(this.allItems, this.currentView);
      document.getElementById("btn-load-more").hidden = !this.hasMore;
    } catch (err) {
      this.toast.show(err.message, "error");
      this.listView.render([], this.currentView);
    }
  }

  async loadMore() {
    if (!this.hasMore || !this.allItems.length) return;
    const after = this.allItems[this.allItems.length - 1].id;
    try {
      const data = this.currentView === "inbox"
        ? await this.api.listReceived(after)
        : await this.api.listSent(after);
      const newItems = data.data || [];
      this.allItems = [...this.allItems, ...newItems];
      this.hasMore = data.has_more || false;
      this.listView.render(this.allItems, this.currentView);
      document.getElementById("btn-load-more").hidden = !this.hasMore;
    } catch (err) {
      this.toast.show(err.message, "error");
    }
  }

  async openEmail(id) {
    try {
      const email = this.currentView === "inbox"
        ? await this.api.getReceived(id)
        : await this.api.getSent(id);
      this.listView.setActive(id);
      this.detailView.show(email, this.currentView);
    } catch (err) {
      this.toast.show(err.message, "error");
    }
  }

  openCompose() {
    this.composeView.openNew();
  }

  openReply() {
    if (!this.detailView.currentId) return;
    this.composeView.openReply(
      this.detailView.currentId,
      this.detailView.fromEl.textContent,
      this.detailView.subjectEl.textContent,
    );
  }

  async sendMail(payload) {
    try {
      if (payload.replyMode) {
        await this.api.reply(payload.replyId, {
          html: payload.html,
          text: payload.text,
        });
        this.toast.show("Ответ отправлен", "success");
      } else {
        await this.api.sendEmail({
          to: payload.to,
          subject: payload.subject,
          html: payload.html,
          text: payload.text,
          cc: payload.cc,
          bcc: payload.bcc,
        });
        this.toast.show("Письмо отправлено", "success");
      }
      if (this.currentView === "sent") await this.loadList();
    } catch (err) {
      this.toast.show(err.message, "error");
      throw err;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new MailApp();
});
