"""Парсер email-адресов из пользовательского ввода."""


class AddressParser:
    """Разбирает строку с одним или несколькими email-адресами."""

    @staticmethod
    def parse(value: str) -> list[str]:
        """
        Преобразует строку ``a@x.com, b@y.com`` в список адресов.

        Поддерживает разделители запятая и точка с запятой.
        """
        if not value or not value.strip():
            return []
        normalized = value.replace(";", ",")
        return [part.strip() for part in normalized.split(",") if part.strip()]
