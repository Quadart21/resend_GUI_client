"""DTO-модели для HTTP-запросов (Pydantic)."""

from pydantic import BaseModel, Field


class ConfigUpdateDto(BaseModel):
    """Тело запроса на обновление настроек."""

    api_key: str = Field(default="", description="API-ключ Resend")
    from_email: str = Field(default="", description="Email отправителя на вашем домене")
    from_name: str = Field(default="", description="Отображаемое имя отправителя")


class SendEmailDto(BaseModel):
    """Тело запроса на отправку письма."""

    to: str = Field(description="Получатели через запятую")
    subject: str = Field(description="Тема письма")
    html: str = Field(default="", description="HTML-содержимое")
    text: str = Field(default="", description="Текстовое содержимое")
    cc: str = Field(default="", description="Копия")
    bcc: str = Field(default="", description="Скрытая копия")
    reply_to: str = Field(default="", description="Адрес для ответа")


class ReplyEmailDto(BaseModel):
    """Тело запроса на ответ входящему письму."""

    html: str = Field(default="", description="HTML-содержимое ответа")
    text: str = Field(default="", description="Текстовое содержимое ответа")
