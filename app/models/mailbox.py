"""Модель почтового ящика."""

import uuid
from dataclasses import dataclass, field


# Палитра цветов для аватаров ящиков в интерфейсе
MAILBOX_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
    "#f97316", "#eab308", "#22c55e", "#14b8a6",
    "#06b6d4", "#3b82f6",
]


@dataclass
class Mailbox:
    """Один почтовый ящик на верифицированном домене Resend."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    color: str = MAILBOX_COLORS[0]
    signature: str = ""

    def from_address(self) -> str:
        """Формирует адрес отправителя для Resend API."""
        email = self.email.strip()
        if not email:
            return ""
        name = self.name.strip()
        if name:
            return f"{name} <{email}>"
        return email

    def to_dict(self) -> dict:
        """Сериализация в словарь для config.json."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "color": self.color,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Mailbox":
        """Десериализация из словаря."""
        color = str(data.get("color", MAILBOX_COLORS[0]))
        if color not in MAILBOX_COLORS:
            color = MAILBOX_COLORS[hash(data.get("email", "")) % len(MAILBOX_COLORS)]
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            name=str(data.get("name", "")).strip(),
            email=str(data.get("email", "")).strip().lower(),
            color=color,
            signature=str(data.get("signature", "")).strip(),
        )
