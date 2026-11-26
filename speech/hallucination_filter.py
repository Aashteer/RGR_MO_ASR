"""Фильтрация типичных галлюцинаций Whisper на музыке."""

from __future__ import annotations

import re

# Типичные «фейковые» подписи Whisper на музыке/тишине
HALLUCINATION_PATTERNS: tuple[str, ...] = (
    "динамическая музыка",
    "спокойная музыка",
    "музыкальная заставка",
    "фоновая музыка",
    "продолжение следует",
    "субтитры",
    "subtitles",
    "subtitle",
    "thank you for watching",
    "thanks for watching",
    "please subscribe",
    "спасибо за просмотр",
    "подписывайтесь",
    "редактор субтитров",
    "корректор",
    "dimatorzok",
    "amara.org",
    "[музыка]",
    "[music]",
    "[аплодисменты]",
    "[applause]",
    "♪",
    "www.",
    "http",
)

_HALLUCINATION_RE = re.compile(
    "|".join(re.escape(p) for p in HALLUCINATION_PATTERNS),
    re.IGNORECASE,
)


def is_music_hallucination(text: str, duration_sec: float = 0.0) -> bool:
    """True, если текст похож на галлюцинацию Whisper (типично для песен на tiny/base)."""
    cleaned = text.strip()
    if not cleaned:
        return True

    lower = cleaned.lower()
    hits = len(_HALLUCINATION_RE.findall(lower))

    # Короткий текст с музыкальными шаблонами
    if len(cleaned) < 120 and hits > 0:
        return True

    # Очень мало слов на длинной записи
    words = cleaned.split()
    if duration_sec > 30 and len(words) < max(8, duration_sec / 15):
        if hits > 0 or any(p in lower for p in ("музык", "music")):
            return True

    # Текст почти целиком из шаблонов
    stripped = _HALLUCINATION_RE.sub("", lower).strip(" .,;:-—")
    if hits >= 2 and len(stripped) < 40:
        return True

    return False


def filter_segment_text(text: str) -> str:
    """Убирает отдельные галлюцинаторные фразы из сегмента."""
    result = text.strip()
    for pattern in HALLUCINATION_PATTERNS:
        result = re.sub(re.escape(pattern), "", result, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip()
