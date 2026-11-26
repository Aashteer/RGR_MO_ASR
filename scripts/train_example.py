#!/usr/bin/env python3
"""Пример запуска обучения Whisper на локальном датасете."""

from __future__ import annotations

import argparse
from pathlib import Path

from training.train_whisper import train


def main() -> None:
    parser = argparse.ArgumentParser(description="Пример fine-tuning Whisper")
    parser.add_argument("--data", type=Path, default=Path("data/train"))
    parser.add_argument("--model", default="openai/whisper-small")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    train(args.data, model_name=args.model, epochs=args.epochs, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
