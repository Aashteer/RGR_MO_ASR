"""Форматирование и коррекция транскрипции (раздел 4.5 ВКР)."""

from __future__ import annotations

from llm.qwen_processor import QwenProcessor
from llm.sanitize import is_valid_russian_llm_output, strip_llm_artifacts

SYSTEM_PROMPT = """Ты — редактор транскрипций на русском языке.
Исправь пунктуацию и очевидные ошибки распознавания.
Сохрани все строки текста, ничего не сокращай и не выбрасывай.
Отвечай ТОЛЬКО на русском языке, без рассуждений и пояснений.
Выведи только готовый отредактированный текст."""


def format_transcription(raw_text: str, processor: QwenProcessor | None = None) -> str:
    if not raw_text.strip():
        return raw_text
    proc = processor or QwenProcessor()
    user = f"Отредактируй транскрипцию, сохрани все строки:\n\n{raw_text}"
    try:
        result = proc.generate(SYSTEM_PROMPT, user, fallback=raw_text)
        result = strip_llm_artifacts(result)
        if is_valid_russian_llm_output(result):
            return result
    except Exception:
        pass
    return raw_text
