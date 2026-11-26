#!/usr/bin/env python3
"""
Скачивание русского датасета Common Voice для обучения Whisper.

Пример:
  python scripts/download_dataset.py --samples 200
  python training/train_whisper.py --data data/train --model openai/whisper-small --epochs 5
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data" / "train"
AUDIO_DIR = DATA_DIR / "audio"


def download_common_voice_ru(max_samples: int = 200) -> int:
  from datasets import load_dataset

  print(f"Загрузка Common Voice (ru), до {max_samples} записей...")
  ds = load_dataset(
      "mozilla-foundation/common_voice_16_1",
      "ru",
      split=f"train[:{max_samples}]",
      trust_remote_code=True,
  )

  AUDIO_DIR.mkdir(parents=True, exist_ok=True)
  rows: list[tuple[str, str]] = []

  for i, item in enumerate(ds):
      text = (item.get("sentence") or "").strip()
      if len(text) < 5:
          continue

      audio = item["audio"]
      fname = f"cv_{i:05d}.wav"
      target = AUDIO_DIR / fname

      array = audio["array"]
      sr = audio["sampling_rate"]
      import soundfile as sf

      sf.write(str(target), array, sr)
      rows.append((fname, text))

  csv_path = DATA_DIR / "transcripts.csv"
  with csv_path.open("w", encoding="utf-8", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(["file", "text"])
      writer.writerows(rows)

  print(f"Сохранено {len(rows)} записей в {DATA_DIR}")
  return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=200, help="Число записей")
    args = parser.parse_args()
    count = download_common_voice_ru(args.samples)
    if count == 0:
        print("Датасет пуст. Проверьте интернет и доступ к Hugging Face.")
        sys.exit(1)
    print("\nДальше обучение:")
    print("  pip install -r requirements-train.txt")
    print("  python training/train_whisper.py --data data/train --model openai/whisper-small --epochs 5")


if __name__ == "__main__":
    main()
