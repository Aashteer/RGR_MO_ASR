"""Очистка ответов LLM от thinking-блоков и английского мусора."""

from __future__ import annotations

import re

_THINK_OPEN = re.compile(r"<\s*(?:think|redacted_thinking)\b[^>]*>", re.IGNORECASE)
_THINK_CLOSE = re.compile(r"<\s*/\s*(?:think|redacted_thinking)\s*>", re.IGNORECASE)
_CYRILLIC_RE = re.compile(r"[а-яёА-ЯЁ]")
_LATIN_WORD_RE = re.compile(r"\b[a-zA-Z]{3,}\b")


def strip_llm_artifacts(text: str) -> str:
    """Убирает блоки рассуждений Qwen3 и лишний английский мусор."""
    if not text:
        return ""
    result = text

    while True:
        m = _THINK_OPEN.search(result)
        if not m:
            break
        close = _THINK_CLOSE.search(result, m.end())
        if close:
            result = result[: m.start()] + result[close.end() :]
        else:
            result = result[: m.start()]
            break

    for marker in ("okay, i need to", "let me start by", "the user mentioned", "first, i notice"):
        idx = result.lower().find(marker)
        if idx != -1 and idx < 150:
            tail = result[idx:]
            cyr = re.search(r"[а-яёА-ЯЁ]{3,}", tail)
            if cyr:
                result = result[:idx] + tail[cyr.start() :]
            else:
                result = result[:idx]

    return re.sub(r"\n{3,}", "\n\n", result).strip()


def latin_word_ratio(text: str) -> float:
    words = re.findall(r"\S+", text)
    if not words:
        return 0.0
    latin = sum(1 for w in words if _LATIN_WORD_RE.search(w))
    return latin / len(words)


def is_valid_russian_llm_output(text: str) -> bool:
    cleaned = strip_llm_artifacts(text)
    if len(cleaned) < 10:
        return False
    if latin_word_ratio(cleaned) > 0.2:
        return False
    if not _CYRILLIC_RE.search(cleaned):
        return False
    lower = cleaned.lower()
    if any(p in lower for p in ("i need to", "the user mentioned", "looking at the")):
        return False
    return True


def pick_best_text(raw: str, formatted: str) -> str:
    raw = raw.strip()
    formatted_clean = strip_llm_artifacts(formatted or "")
    if formatted_clean and is_valid_russian_llm_output(formatted_clean):
        if len(formatted_clean) >= len(raw) * 0.45:
            return formatted_clean
    return raw
