#!/usr/bin/env python3
"""CLI-режим транскрибации без GUI."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from export import export_txt
from pipeline import TranscriptionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Транскрибация аудио (CLI)")
    parser.add_argument("audio", help="Путь к аудио/видео файлу")
    parser.add_argument("-o", "--output", help="Путь к выходному TXT")
    parser.add_argument("--model", default=settings.whisper.model_size, help="Размер Whisper")
    parser.add_argument("--no-diar", action="store_true", help="Отключить диаризацию")
    parser.add_argument("--no-llm", action="store_true", help="Отключить LLM")
    args = parser.parse_args()

    settings.whisper.model_size = args.model
    settings.enable_diarization = not args.no_diar
    settings.enable_llm_postprocess = not args.no_llm

    pipeline = TranscriptionPipeline()

    def on_progress(msg: str, pct: int) -> None:
        print(f"[{pct:3d}%] {msg}")

    result = pipeline.process(args.audio, on_progress=on_progress)
    print("\n" + "=" * 60)
    print(result.formatted_transcription or result.raw_transcription)
    if result.summary:
        print("\n--- КРАТКОЕ СОДЕРЖАНИЕ ---\n")
        print(result.summary)

    out = args.output or str(Path(args.audio).with_suffix(".txt"))
    export_txt(pipeline.to_export_data(result), out)
    print(f"\nСохранено: {out}")


if __name__ == "__main__":
    main()
