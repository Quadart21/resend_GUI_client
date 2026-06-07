"""Модель настроек приложения."""

from dataclasses import dataclass


@dataclass
class AppSettings:
    """Локальные настройки почтового клиента."""

    api_key: str = ""
    from_email: str = ""
    from_name: str = ""

    def has_api_key(self) -> bool:
        """Проверяет, задан ли API-ключ Resend."""
        return bool(self.api_key.strip())

    def api_key_preview(self) -> str:
        """Возвращает маскированный префикс ключа для отображения в UI."""
        if not self.api_key:
            return ""
        return self.api_key[:8] + "..."

    def from_address(self) -> str:
        """
        Формирует адрес отправителя в формате Resend.

        Примеры: ``hello@domain.com`` или ``Компания <hello@domain.com>``.
        """
        email = self.from_email.strip()
        if not email:
            return ""
        name = self.from_name.strip()
        if name:
            return f"{name} <{email}>"
        return email

    def to_dict(self) -> dict[str, str]:
        """Сериализует настройки в словарь."""
        return {
            "api_key": self.api_key,
            "from_email": self.from_email,
            "from_name": self.from_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """Создаёт объект настроек из словаря."""
        return cls(
            api_key=str(data.get("api_key", "")).strip(),
            from_email=str(data.get("from_email", "")).strip(),
            from_name=str(data.get("from_name", "")).strip(),
        )
