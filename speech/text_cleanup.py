"""Очистка текста транскрипции от повторов и мусора Whisper."""

from __future__ import annotations

import re

from speech.hallucination_filter import filter_segment_text

# Частые англоязычные галлюцинации Whisper
ENGLISH_HALLUCINATIONS = (
    "thank you",
    "thanks for watching",
    "please subscribe",
    "subtitles by",
    "subtitle",
    "you",
    "the",
    "and",
    "music",
    "applause",
)

_CYRILLIC_RE = re.compile(r"[а-яёА-ЯЁ]")
_LATIN_WORD_RE = re.compile(r"\b[a-zA-Z]{2,}\b")


def collapse_word_repeats(text: str) -> str:
    """«даром, даром, даром» → «даром»."""
    words = text.split()
    if not words:
        return text.strip()
    result = [words[0]]
    for word in words[1:]:
        prev = re.sub(r"[^\wа-яёА-ЯЁ]", "", result[-1], flags=re.IGNORECASE).lower()
        cur = re.sub(r"[^\wа-яёА-ЯЁ]", "", word, flags=re.IGNORECASE).lower()
        if cur and cur == prev:
            continue
        result.append(word)
    return " ".join(result)


def is_mostly_english(text: str) -> bool:
    """True, если сегмент в основном на латинице."""
    words = re.findall(r"\S+", text)
    if not words:
        return True
    latin = sum(1 for w in words if _LATIN_WORD_RE.fullmatch(re.sub(r"[^\w]", "", w)))
    cyrillic = bool(_CYRILLIC_RE.search(text))
    if not cyrillic and latin > 0:
        return True
    if latin >= 2 and latin / len(words) > 0.4:
        return True
    lower = text.lower()
    if any(p in lower for p in ENGLISH_HALLUCINATIONS) and latin / max(len(words), 1) > 0.2:
        return True
    return False


def is_garbage_segment(text: str) -> bool:
    """Сегмент из одного повторяющегося слова."""
    cleaned = collapse_word_repeats(filter_segment_text(text))
    if is_mostly_english(cleaned):
        return True
    words = re.findall(r"[а-яёА-ЯЁa-zA-Z]+", cleaned)
    if not words:
        return True
    unique = {w.lower() for w in words}
    if len(words) >= 5 and len(unique) == 1:
        return True
    return False


def dedupe_segments(segments: list) -> list:
    """Убирает подряд идущие дубликаты и мусорные сегменты."""
    cleaned = []
    prev_key = ""

    for seg in segments:
        text = collapse_word_repeats(filter_segment_text(seg.text))
        if not text or is_garbage_segment(text):
            continue
        key = re.sub(r"\s+", " ", text.lower().strip())
        if key == prev_key:
            continue
        cleaned.append(
            type(seg)(
                start=seg.start,
                end=seg.end,
                text=text,
                words=seg.words,
            )
        )
        prev_key = key
    return cleaned


def format_segments_as_lines(segments: list, gap_sec: float = 1.2) -> str:
    """Склеивает сегменты в строки (кауплеты) по паузам."""
    if not segments:
        return ""
    lines: list[str] = []
    current: list[str] = []
    prev_end = segments[0].start

    for seg in segments:
        if current and seg.start - prev_end > gap_sec:
            lines.append(" ".join(current))
            current = []
        current.append(seg.text.strip())
        prev_end = seg.end

    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def cleanup_full_text(text: str) -> str:
    """Финальная очистка склеенного текста."""
    text = collapse_word_repeats(filter_segment_text(text))
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line and not is_mostly_english(line):
            lines.append(line)
    return "\n".join(lines).strip()

