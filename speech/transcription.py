"""Модуль автоматической транскрибации (faster-whisper, листинги 4.3–4.5 ВКР)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from config.settings import (
    WhisperSettings,
    resolve_compute_type,
    resolve_device,
    settings,
)
from speech.hallucination_filter import filter_segment_text, is_music_hallucination
from speech.text_cleanup import is_mostly_english


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str
    words: list[dict[str, Any]] = field(default_factory=list)


class TranscriptionEngine:
    """Универсальная обёртка faster-whisper: речь, песни, видео, голосовые."""

    def __init__(self, whisper_settings: WhisperSettings | None = None):
        self.cfg = whisper_settings or settings.whisper
        self._model = None

    def load_model(self, model_size: str | None = None) -> None:
        size = model_size or self.cfg.model_size
        if self._model is not None and size == self.cfg.model_size:
            return

        if model_size and model_size != self.cfg.model_size:
            self._model = None
            self.cfg.model_size = model_size

        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Не установлен faster-whisper") from exc

        device = resolve_device(self.cfg.device)
        compute_type = resolve_compute_type(self.cfg.compute_type, device)
        self._model = WhisperModel(
            self.cfg.model_size,
            device=device,
            compute_type=compute_type,
            download_root=self.cfg.download_root,
        )

    def transcribe(
        self,
        audio_path: str,
        on_progress: Callable[[str, int], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> tuple[list[TranscriptionSegment], dict]:
        self.load_model()
        assert self._model is not None

        segments, info = self._run_pass(
            audio_path,
            on_progress=on_progress,
            cancel_check=cancel_check,
            pct_start=25,
            pct_end=52,
        )

        text = " ".join(s.text for s in segments).strip()
        duration = info.get("duration", 0.0) or 0.0

        if is_music_hallucination(text, duration) and self.cfg.model_size != "large-v3":
            if on_progress:
                on_progress("Повтор с моделью large-v3...", 53)
            self._model = None
            self.load_model("large-v3")
            segments, info = self._run_pass(
                audio_path,
                on_progress=on_progress,
                cancel_check=cancel_check,
                pct_start=53,
                pct_end=60,
            )

        # Зафиксировать русский после автоопределения
        detected = info.get("language", "")
        if self.cfg.language is None and detected == "ru":
            self.cfg.language = "ru"

        return segments, info

    def _run_pass(
        self,
        audio_path: str,
        on_progress: Callable[[str, int], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
        pct_start: int = 25,
        pct_end: int = 52,
    ) -> tuple[list[TranscriptionSegment], dict]:
        assert self._model is not None

        lang = self.cfg.language
        kwargs: dict[str, Any] = {
            "beam_size": max(self.cfg.beam_size, 5),
            "vad_filter": False,
            "word_timestamps": self.cfg.word_timestamps,
            "language": lang,
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.25,
            "compression_ratio_threshold": 2.4,
            "log_prob_threshold": -1.0,
            "temperature": (0.0, 0.2, 0.4),
        }
        if lang == "ru" or lang is None:
            kwargs["initial_prompt"] = (
                "Текст песни на русском языке. Стихи, lyrics, вокал, пение, rap."
            )

        segments_iter, info = self._model.transcribe(audio_path, **kwargs)

        duration = info.duration or 0.0
        segments: list[TranscriptionSegment] = []
        seg_count = 0

        for seg in segments_iter:
            if cancel_check and cancel_check():
                raise InterruptedError("Транскрибация отменена пользователем")

            text = filter_segment_text(seg.text.strip())
            if not text or is_mostly_english(text):
                continue

            words = []
            if getattr(seg, "words", None):
                words = [
                    {"start": w.start, "end": w.end, "word": w.word}
                    for w in seg.words
                ]

            segments.append(
                TranscriptionSegment(
                    start=seg.start,
                    end=seg.end,
                    text=text,
                    words=words,
                )
            )
            seg_count += 1

            if on_progress and duration > 0:
                ratio = min(1.0, seg.end / duration)
                pct = pct_start + int(ratio * (pct_end - pct_start))
                on_progress(f"Распознавание речи... ({seg_count} фрагм.)", pct)

        info_dict = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }
        return segments, info_dict

    def segments_to_dicts(self, segments: list[TranscriptionSegment]) -> list[dict]:
        return [
            {"start": s.start, "end": s.end, "text": s.text, "words": s.words}
            for s in segments
        ]
