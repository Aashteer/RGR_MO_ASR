#!/usr/bin/env python3
"""
Дообучение (fine-tuning) Whisper на своих данных.

Формат датасета (папка data/train/):
  audio/
    sample001.wav
    sample002.wav
  transcripts.csv  — колонки: file,text

Пример transcripts.csv:
  file,text
  sample001.wav,Привет мир это тестовая запись
  sample002.wav,Вторая запись для обучения модели

Требования: GPU с >= 8 ГБ VRAM для base/small, >= 16 ГБ для medium/large.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@dataclass
class Sample:
    audio_path: Path
    text: str


def load_dataset(data_dir: Path) -> list[Sample]:
    csv_path = data_dir / "transcripts.csv"
    audio_dir = data_dir / "audio"
    if not csv_path.exists():
        raise FileNotFoundError(f"Нет {csv_path}")
    samples: list[Sample] = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row["file"].strip()
            text = row["text"].strip()
            ap = audio_dir / fname
            if ap.exists() and text:
                samples.append(Sample(ap, text))
    if not samples:
        raise ValueError("Датасет пуст")
    return samples


def train(
    data_dir: Path,
    model_name: str = "openai/whisper-small",
    output_dir: Path | None = None,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 1e-5,
) -> None:
    import torch
    from datasets import Dataset
    from transformers import (
        WhisperForConditionalGeneration,
        WhisperProcessor,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )

    if output_dir is None:
        output_dir = ROOT / "models" / "whisper_finetuned"
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = load_dataset(data_dir)
    print(f"Загружено {len(samples)} образцов")

    processor = WhisperProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name)
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []

    def prepare_example(sample: Sample) -> dict:
        import librosa

        audio, _ = librosa.load(str(sample.audio_path), sr=16000)
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        labels = processor.tokenizer(sample.text, return_tensors="pt").input_ids[0]
        return {
            "input_features": inputs.input_features[0].numpy(),
            "labels": labels.numpy(),
        }

    records = [prepare_example(s) for s in samples]
    dataset = Dataset.from_list(records)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=2,
        learning_rate=learning_rate,
        num_train_epochs=epochs,
        fp16=torch.cuda.is_available(),
        save_steps=100,
        logging_steps=10,
        remove_unused_columns=False,
        predict_with_generate=True,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=processor,
    )

    print("Старт обучения...")
    trainer.train()
    trainer.save_model(str(output_dir))
    processor.save_pretrained(str(output_dir))
    print(f"Модель сохранена: {output_dir}")
    print("Для использования в faster-whisper конвертируйте в CTranslate2:")
    print(f"  ct2-transformers-converter --model {output_dir} --output_dir models/whisper_finetuned_ct2")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning Whisper")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "train")
    parser.add_argument("--model", default="openai/whisper-small")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-5)
    args = parser.parse_args()
    train(
        args.data,
        model_name=args.model,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()
