#!/usr/bin/env python3
"""Оценка качества транскрибации (WER/CER) на тестовом наборе."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.metrics import cer, wer
from pipeline import TranscriptionPipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "test")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--no-diar", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    from config.settings import settings

    settings.whisper.model_size = args.model
    settings.enable_diarization = not args.no_diar
    settings.enable_llm_postprocess = not args.no_llm

    csv_path = args.data / "transcripts.csv"
    audio_dir = args.data / "audio"
    pipeline = TranscriptionPipeline()

    total_wer = 0.0
    total_cer = 0.0
    n = 0

    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            audio = audio_dir / row["file"].strip()
            reference = row["text"].strip()
            result = pipeline.process(str(audio))
            hypothesis = result.raw_transcription
            w = wer(reference, hypothesis)
            c = cer(reference, hypothesis)
            total_wer += w
            total_cer += c
            n += 1
            print(f"{row['file']}: WER={w:.2%}, CER={c:.2%}")

    if n:
        print(f"\nСредний WER: {total_wer / n:.2%}")
        print(f"Средний CER: {total_cer / n:.2%}")


if __name__ == "__main__":
    main()
