#!/usr/bin/env python3
"""Простой стартовый скрипт для обработки аудио."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import TranscriptionPipeline
from config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Обработка аудио через конвейер")
    parser.add_argument("audio", help="Путь к аудио/видео файлу")
    parser.add_argument("--model", default=settings.whisper.model_size, help="Размер Whisper")
    parser.add_argument("--no-diar", action="store_true", help="Отключить диаризацию")
    parser.add_argument("--no-llm", action="store_true", help="Отключить LLM")
    args = parser.parse_args()

    settings.whisper.model_size = args.model
    settings.enable_diarization = not args.no_diar
    settings.enable_llm_postprocess = not args.no_llm

    pipeline = TranscriptionPipeline()
    result = pipeline.process(args.audio, on_progress=lambda msg, pct: print(f"[{pct:3d}%] {msg}"))
    print("\n=== ТРАНСКРИПЦИЯ ===")
    print(result.formatted_transcription or result.raw_transcription)
    if result.summary:
        print("\n=== КРАТКОЕ СОДЕРЖАНИЕ ===")
        print(result.summary)


if __name__ == "__main__":
    main()
