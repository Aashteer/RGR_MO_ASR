"""
Оценка модели: Accuracy, Precision, Recall, F1, матрица ошибок, графики.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from rgr.dataset import DigitMelDataset, Sample
from rgr.features import extract_features, save_mel_preview
from rgr.model import SpeechCRNN
from rgr.train import History, load_trained_model

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "rgr"
CLASS_NAMES = [str(i) for i in range(10)]


@torch.no_grad()
def predict_all(
    model: SpeechCRNN,
    samples: list[Sample],
    batch_size: int = 32,
    device: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    device_t = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = model.to(device_t)
    model.eval()
    loader = DataLoader(DigitMelDataset(samples, augment=False), batch_size=batch_size)
    ys: list[np.ndarray] = []
    preds: list[np.ndarray] = []
    for x, y in loader:
        x = x.to(device_t)
        logits = model(x)
        pred = logits.argmax(dim=1).cpu().numpy()
        preds.append(pred)
        ys.append(y.numpy())
    return np.concatenate(ys), np.concatenate(preds)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, target_names=CLASS_NAMES, zero_division=0
        ),
    }


def plot_history(history: History | dict, out_dir: Path) -> list[Path]:
    import matplotlib.pyplot as plt

    if isinstance(history, History):
        h = {
            "train_loss": history.train_loss,
            "val_loss": history.val_loss,
            "train_acc": history.train_acc,
            "val_acc": history.val_acc,
        }
    else:
        h = history

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    epochs = range(1, len(h["train_loss"]) + 1)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(epochs, h["train_loss"], label="Train loss")
    ax.plot(epochs, h["val_loss"], label="Val loss")
    ax.set_xlabel("Эпоха")
    ax.set_ylabel("Loss")
    ax.set_title("Динамика функции потерь")
    ax.legend()
    ax.grid(True, alpha=0.3)
    p1 = out_dir / "loss_curve.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    paths.append(p1)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(epochs, h["train_acc"], label="Train accuracy")
    ax.plot(epochs, h["val_acc"], label="Val accuracy")
    ax.set_xlabel("Эпоха")
    ax.set_ylabel("Accuracy")
    ax.set_title("Динамика точности")
    ax.legend()
    ax.grid(True, alpha=0.3)
    p2 = out_dir / "accuracy_curve.png"
    fig.tight_layout()
    fig.savefig(p2, dpi=150)
    plt.close(fig)
    paths.append(p2)
    return paths


def plot_confusion(cm: list[list[int]] | np.ndarray, out_dir: Path) -> Path:
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm_arr = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm_arr,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        ax=ax,
    )
    ax.set_xlabel("Предсказанный класс")
    ax.set_ylabel("Истинный класс")
    ax.set_title("Матрица ошибок (тестовая выборка)")
    out = out_dir / "confusion_matrix.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def analyze_errors(
    samples: list[Sample],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    max_examples: int = 12,
) -> list[dict]:
    errors = []
    for i, (yt, yp) in enumerate(zip(y_true, y_pred)):
        if yt != yp:
            s = samples[i]
            errors.append(
                {
                    "file": s.path.name,
                    "speaker": s.speaker,
                    "true": int(yt),
                    "pred": int(yp),
                }
            )
            if len(errors) >= max_examples:
                break
    return errors


def run_evaluation(
    model: SpeechCRNN,
    test_samples: list[Sample],
    history: History | dict | None = None,
    out_dir: Path | None = None,
) -> dict:
    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    y_true, y_pred = predict_all(model, test_samples)
    metrics = compute_metrics(y_true, y_pred)
    errors = analyze_errors(test_samples, y_true, y_pred)

    artifacts: dict[str, str] = {}
    if history is not None:
        for p in plot_history(history, out_dir):
            artifacts[p.stem] = str(p)
    cm_path = plot_confusion(metrics["confusion_matrix"], out_dir)
    artifacts["confusion_matrix"] = str(cm_path)

    # превью mel для нескольких файлов
    previews = []
    for s in test_samples[:3]:
        png = out_dir / f"mel_{s.path.stem}.png"
        try:
            save_mel_preview(s.path, png)
            previews.append(str(png))
        except Exception as exc:
            previews.append(f"error:{exc}")
    artifacts["mel_previews"] = previews  # type: ignore[assignment]

    report = {
        "n_test": len(test_samples),
        "metrics": {k: v for k, v in metrics.items() if k != "classification_report"},
        "classification_report": metrics["classification_report"],
        "errors": errors,
        "artifacts": artifacts,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "classification_report.txt").write_text(
        metrics["classification_report"], encoding="utf-8"
    )
    print(metrics["classification_report"])
    print(f"Accuracy={metrics['accuracy']:.4f}, F1-macro={metrics['f1_macro']:.4f}")
    print(f"Результаты сохранены в {out_dir}")
    return report


def predict_file(model: SpeechCRNN, audio_path: str | Path, device: str | None = None) -> dict:
    """Инференс одного файла для GUI."""
    import torch

    device_t = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = model.to(device_t)
    model.eval()
    feat = extract_features(audio_path, kind="mel")
    x = torch.from_numpy(feat).unsqueeze(0).unsqueeze(0).to(device_t)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        pred = int(probs.argmax())
    return {
        "digit": pred,
        "text": str(pred),
        "confidence": float(probs[pred]),
        "probs": {str(i): float(probs[i]) for i in range(10)},
    }
