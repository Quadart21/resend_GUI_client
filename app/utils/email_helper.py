"""Вспомогательные функции для работы с email-адресами и темами."""

import hashlib
import re


class EmailHelper:
    """Утилиты парсинга адресов и нормализации тем писем."""

    _SUBJECT_PREFIX_RE = re.compile(
        r"^(re|fwd|fw|ответ|пересылка)\s*:\s*",
        re.IGNORECASE,
    )
    _EMAIL_IN_BRACKETS_RE = re.compile(r"<([^>]+)>")

    @classmethod
    def extract_email(cls, address: str) -> str:
        """
        Извлекает email из строки ``Имя <user@domain.com>``.

        :returns: email в нижнем регистре или пустая строка
        """
        if not address:
            return ""
        match = cls._EMAIL_IN_BRACKETS_RE.search(address)
        if match:
            return match.group(1).strip().lower()
        return address.strip().lower()

    @classmethod
    def normalize_addresses(cls, value: str | list | None) -> list[str]:
        """Преобразует поле from/to в список email-адресов."""
        if not value:
            return []
        if isinstance(value, str):
            return [cls.extract_email(value)] if cls.extract_email(value) else []
        result: list[str] = []
        for item in value:
            email = cls.extract_email(str(item))
            if email:
                result.append(email)
        return result

    @classmethod
    def normalize_subject(cls, subject: str | None) -> str:
        """
        Убирает префиксы Re:/Fwd: для группировки цепочек.

        ``Re: Re: Hello`` → ``hello``
        """
        if not subject:
            return "(без темы)"
        cleaned = subject.strip()
        while True:
            next_val = cls._SUBJECT_PREFIX_RE.sub("", cleaned).strip()
            if next_val == cleaned:
                break
            cleaned = next_val
        return cleaned.lower() or "(без темы)"

    @classmethod
    def thread_key(cls, subject: str | None, participants: set[str]) -> str:
        """
        Строит стабильный ключ цепочки по теме и участникам.

        Используется для объединения входящих и исходящих писем.
        """
        norm_subject = cls.normalize_subject(subject)
        sorted_participants = sorted(p for p in participants if p)
        raw = f"{norm_subject}|{'|'.join(sorted_participants)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @classmethod
    def display_name(cls, address: str) -> str:
        """Возвращает имя или email для отображения в UI."""
        if not address:
            return "—"
        match = cls._EMAIL_IN_BRACKETS_RE.search(address)
        if match:
            name_part = address[: match.start()].strip().strip('"')
            return name_part or match.group(1)
        return address
