"""DTO-модели для HTTP-запросов (Pydantic)."""

from pydantic import BaseModel, Field


class ConfigUpdateDto(BaseModel):
    """Тело запроса на обновление настроек."""

    api_key: str = Field(default="", description="API-ключ Resend (пустой = не менять)")
    webhook_secret: str = Field(
        default="",
        description="Signing secret webhook Resend whsec_... (пустой = не менять)",
    )


class MailboxCreateDto(BaseModel):
    """Создание почтового ящика."""

    name: str = Field(description="Отображаемое имя")
    email: str = Field(description="Email на вашем домене")


class MailboxUpdateDto(BaseModel):
    """Обновление почтового ящика."""

    name: str = Field(description="Отображаемое имя")
    email: str = Field(description="Email на вашем домене")


class SendEmailDto(BaseModel):
    """Тело запроса на отправку письма."""

    mailbox_id: str = Field(description="ID ящика-отправителя")
    to: str = Field(description="Получатели через запятую")
    subject: str = Field(description="Тема письма")
    html: str = Field(default="", description="HTML-содержимое")
    text: str = Field(default="", description="Текстовое содержимое")
    cc: str = Field(default="", description="Копия")
    bcc: str = Field(default="", description="Скрытая копия")
    reply_to: str = Field(default="", description="Адрес для ответа")


class ReplyEmailDto(BaseModel):
    """Тело запроса на ответ в цепочке."""

    mailbox_id: str = Field(description="ID ящика-отправителя")
    html: str = Field(default="", description="HTML-содержимое ответа")
    text: str = Field(default="", description="Текстовое содержимое ответа")


class LoginDto(BaseModel):
    """Вход в систему."""

    username: str = Field(min_length=1, description="Логин")
    password: str = Field(min_length=1, description="Пароль")


class UserCreateDto(BaseModel):
    """Создание пользователя (админ)."""

    username: str = Field(min_length=2, description="Логин")
    password: str = Field(min_length=4, description="Пароль")
    is_admin: bool = Field(default=False, description="Администратор")
    mailbox_ids: list[str] = Field(default_factory=list, description="Доступные ящики")


class UserUpdateDto(BaseModel):
    """Обновление пользователя (админ)."""

    password: str | None = Field(default=None, min_length=4, description="Новый пароль")
    is_admin: bool | None = Field(default=None, description="Администратор")
    is_active: bool | None = Field(default=None, description="Активен")
    mailbox_ids: list[str] | None = Field(default=None, description="Доступные ящики")
