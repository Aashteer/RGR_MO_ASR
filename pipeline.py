"""Центральный конвейер обработки аудио (алгоритм раздела 3.5 ВКР)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable

from audio.converter import convert_to_wav
from audio.file_loader import validate_audio_file
from audio.preprocessing import normalize_audio
from audio.vocal_isolation import isolate_vocals
from config.settings import AppSettings, settings
from export.txt_export import ExportData
from llm.formatter import format_transcription
from llm.qwen_processor import QwenProcessor
from llm.sanitize import is_valid_russian_llm_output, pick_best_text, strip_llm_artifacts
from llm.summarizer import summarize
from speech.diarization import DiarizationEngine
from speech.merge_segments import format_dialogue, merge_transcription_and_diarization
from speech.text_cleanup import cleanup_full_text, dedupe_segments, format_segments_as_lines
from speech.transcription import TranscriptionEngine

ProgressCallback = Callable[[str, int], None]  # (stage_message, percent)


@dataclass
class PipelineResult:
    source_file: str
    wav_path: str
    raw_transcription: str
    formatted_transcription: str
    summary: str
    language: str = ""
    duration_sec: float = 0.0
    segments: list[dict] = field(default_factory=list)
    speaker_segments: list[dict] = field(default_factory=list)
    info: dict = field(default_factory=dict)
    log: list[str] = field(default_factory=list)


class TranscriptionPipeline:
    def __init__(self, app_settings: AppSettings | None = None):
        self.cfg = app_settings or settings
        self.transcriber = TranscriptionEngine(self.cfg.whisper)
        self.diarizer = DiarizationEngine(self.cfg.diarization)
        self.llm: QwenProcessor | None = None
        self._cancel_event = Event()
        if self.cfg.enable_llm_postprocess and self.cfg.llm.enabled:
            self.llm = QwenProcessor(self.cfg.llm)

    def cancel(self) -> None:
        self._cancel_event.set()

    def _check_cancel(self) -> None:
        if self._cancel_event.is_set():
            raise InterruptedError("Транскрибация отменена пользователем")

    def process(
        self,
        audio_path: str | Path,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineResult:
        self._cancel_event.clear()

        def report(msg: str, pct: int) -> None:
            self._check_cancel()
            if on_progress:
                on_progress(msg, pct)

        log: list[str] = []

        def note(msg: str) -> None:
            log.append(msg)

        report("Проверка файла...", 2)
        src = validate_audio_file(audio_path)

        report("Конвертация аудио (FFmpeg)...", 8)
        wav = convert_to_wav(src)
        wav = normalize_audio(wav)

        if self.cfg.enable_vocal_isolation:
            report("Выделение вокала...", 12)
            try:
                wav = isolate_vocals(wav)
                note("Вокал: выделен (Demucs или FFmpeg)")
            except Exception as exc:
                note(f"Вокал: пропущен — {exc}")

        report("Загрузка модели Whisper...", 15)
        try:
            self.transcriber.load_model()
        except Exception as exc:
            report(f"Whisper недоступен: {exc}", 20)
            raise RuntimeError(f"Не удалось загрузить Whisper: {exc}") from exc

        report("Распознавание речи...", 25)
        try:
            segments, info = self.transcriber.transcribe(
                str(wav),
                on_progress=report,
                cancel_check=self._cancel_event.is_set,
            )
        except InterruptedError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Ошибка распознавания речи: {exc}") from exc

        segments = dedupe_segments(segments)
        trans_dicts = self.transcriber.segments_to_dicts(segments)
        note(f"Whisper: модель {self.cfg.whisper.model_size}")
        note(f"Распознано сегментов: {len(segments)}, язык: {info.get('language', '?')}")

        speaker_dicts: list[dict] = []
        if self.cfg.enable_diarization:
            try:
                report("Диаризация (pyannote)...", 55)
                self.diarizer.load_pipeline()
                sp_segs = self.diarizer.diarize(str(wav))
                speaker_dicts = self.diarizer.segments_to_dicts(sp_segs)
                speakers = {s["speaker"] for s in speaker_dicts}
                note(f"Диаризация: OK, дикторов: {len(speakers)}")
            except Exception as exc:
                note(f"Диаризация: пропущена — {exc}")
                report(f"Диаризация пропущена: {exc}", 55)
        else:
            note("Диаризация: выключена")

        report("Объединение сегментов...", 65)
        merged = merge_transcription_and_diarization(trans_dicts, speaker_dicts or None)
        if speaker_dicts:
            raw_text = format_dialogue(merged)
        else:
            raw_text = format_segments_as_lines(segments)
        raw_text = cleanup_full_text(raw_text)
        if not raw_text:
            raise RuntimeError(
                "Речь не распознана. Попробуйте отключить диаризацию, "
                "выбрать модель large-v3 или проверить качество записи."
            )

        formatted = raw_text
        summary_text = ""

        if self.llm and self.cfg.enable_llm_postprocess:
            if not self.llm.is_available:
                note("LLM: модель Qwen не найдена — скачайте scripts/download_models.py --qwen")
                report("LLM недоступна — файл модели не найден", 90)
            else:
                report("Загрузка Qwen LLM (может занять 1–3 мин)...", 72)
                try:
                    self.llm.load_model()
                    note("LLM: модель загружена")
                    report("Постобработка текста...", 80)
                    formatted = format_transcription(raw_text, self.llm)
                    formatted = strip_llm_artifacts(formatted)
                    if is_valid_russian_llm_output(formatted) and len(formatted) >= len(raw_text) * 0.45:
                        note("LLM: текст отредактирован")
                    else:
                        formatted = raw_text
                        note("LLM: использован исходный текст Whisper (ответ LLM отклонён)")
                    if self.cfg.enable_summarization:
                        report("Генерация краткого содержания...", 90)
                        summary_text = summarize(formatted, self.llm)
                        summary_text = strip_llm_artifacts(summary_text)
                        if summary_text.strip() and is_valid_russian_llm_output(summary_text):
                            note("LLM: краткое содержание создано")
                        else:
                            summary_text = ""
                            note("LLM: краткое содержание не получено")
                except Exception as exc:
                    note(f"LLM: ошибка — {exc}")
                    report(f"LLM пропущена: {exc}", 90)
                    formatted = raw_text
        elif self.cfg.enable_llm_postprocess:
            note("LLM: выключена в настройках модели")
            report("LLM недоступна — используется сырая транскрипция", 90)
        else:
            note("LLM: выключена")

        report("Готово", 100)
        return PipelineResult(
            source_file=str(src),
            wav_path=str(wav),
            raw_transcription=raw_text,
            formatted_transcription=formatted,
            summary=summary_text,
            language=info.get("language", ""),
            duration_sec=info.get("duration", 0.0),
            segments=[{"start": m.start, "end": m.end, "text": m.text, "speaker": m.speaker} for m in merged],
            speaker_segments=speaker_dicts,
            info=info,
            log=log,
        )

    def to_export_data(self, result: PipelineResult) -> ExportData:
        return ExportData(
            title="Транскрипция аудиозаписи",
            raw_transcription=result.raw_transcription,
            formatted_transcription=result.formatted_transcription,
            summary=result.summary,
            source_file=result.source_file,
            language=result.language,
            duration_sec=result.duration_sec,
            segments=result.segments,
        )
