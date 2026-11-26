"""Суммаризация транскрипции (раздел 4.5 ВКР)."""

from __future__ import annotations

from llm.qwen_processor import QwenProcessor
from llm.sanitize import is_valid_russian_llm_output, strip_llm_artifacts

SUMMARY_SYSTEM = """Ты — аналитик. Составь краткое содержание на русском языке (5–8 предложений).
Отвечай ТОЛЬКО на русском, без рассуждений и пояснений."""


def summarize(text: str, processor: QwenProcessor | None = None) -> str:
    if not text.strip():
        return ""
    proc = processor or QwenProcessor()
    user = f"Составь краткое содержание:\n\n{text[:6000]}"
    try:
        result = proc.generate(SUMMARY_SYSTEM, user, fallback="")
        result = strip_llm_artifacts(result)
        if is_valid_russian_llm_output(result):
            return result
    except Exception:
        pass
    return ""
