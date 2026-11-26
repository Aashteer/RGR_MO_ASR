#!/usr/bin/env python3
"""
Полный цикл эксперимента РГР (блок 4, вариант 53):
датасет → предобработка/аугментация → обучение CRNN → оценка → графики.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Эксперимент РГР: CRNN на FSDD")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "rgr")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models" / "rgr_crnn")
    args = parser.parse_args()

    from rgr.dataset import download_fsdd, load_samples, save_manifest, split_by_speaker
    from rgr.evaluate import run_evaluation
    from rgr.train import TrainConfig, train_model

    args.out.mkdir(parents=True, exist_ok=True)
    args.model_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        download_fsdd()

    samples = load_samples()
    train_s, val_s, test_s = split_by_speaker(samples)
    save_manifest(train_s, val_s, test_s, args.out / "dataset_manifest.json")
    print(f"Выборки: train={len(train_s)}, val={len(val_s)}, test={len(test_s)}")

    cfg = TrainConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
    )
    model, history, ckpt = train_model(train_s, val_s, cfg=cfg, out_dir=args.model_dir)
    report = run_evaluation(model, test_s, history=history, out_dir=args.out)

    summary = {
        "topic": "Вариант 53. Автоматическое распознавание речи / транскрибация аудиоконтента",
        "experiment": "Классификация произнесённых цифр 0–9 (FSDD) моделью CRNN на mel-спектрограммах",
        "checkpoint": str(ckpt),
        "accuracy": report["metrics"]["accuracy"],
        "f1_macro": report["metrics"]["f1_macro"],
        "precision_macro": report["metrics"]["precision_macro"],
        "recall_macro": report["metrics"]["recall_macro"],
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== Итог эксперимента ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
