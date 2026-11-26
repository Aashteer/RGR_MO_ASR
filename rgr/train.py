"""
Обучение CRNN на FSDD с логированием loss/accuracy.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from rgr.dataset import DigitMelDataset, Sample
from rgr.features import N_MELS
from rgr.model import SpeechCRNN, count_parameters

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "models" / "rgr_crnn"


@dataclass
class TrainConfig:
    epochs: int = 25
    batch_size: int = 32
    lr: float = 8e-4
    weight_decay: float = 1e-4
    num_workers: int = 0
    seed: int = 42
    device: str = "cpu"


@dataclass
class History:
    train_loss: list[float] = field(default_factory=list)
    train_acc: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    val_acc: list[float] = field(default_factory=list)


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


@torch.no_grad()
def evaluate_loader(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0
    for x, y in loader:
        x = x.to(device)
        y = y.to(device)
        logits = model(x)
        loss = criterion(logits, y)
        total_loss += float(loss.item()) * y.size(0)
        pred = logits.argmax(dim=1)
        correct += int((pred == y).sum().item())
        total += int(y.size(0))
    return total_loss / max(total, 1), correct / max(total, 1)


def train_model(
    train_samples: list[Sample],
    val_samples: list[Sample],
    cfg: TrainConfig | None = None,
    out_dir: Path | None = None,
) -> tuple[SpeechCRNN, History, Path]:
    cfg = cfg or TrainConfig()
    out_dir = Path(out_dir or DEFAULT_OUT)
    out_dir.mkdir(parents=True, exist_ok=True)
    set_seed(cfg.seed)

    device = torch.device(cfg.device if torch.cuda.is_available() or cfg.device == "cpu" else "cpu")
    if cfg.device == "cuda" and not torch.cuda.is_available():
        device = torch.device("cpu")

    train_ds = DigitMelDataset(train_samples, augment=True, seed=cfg.seed)
    val_ds = DigitMelDataset(val_samples, augment=False, seed=cfg.seed + 1)
    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
    )

    model = SpeechCRNN(n_mels=N_MELS, n_classes=10).to(device)
    print(f"Параметров модели: {count_parameters(model):,}")
    print(f"Устройство: {device}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    history = History()
    best_val = float("inf")
    best_path = out_dir / "best_model.pt"

    t0 = time.time()
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item()) * y.size(0)
            pred = logits.argmax(dim=1)
            correct += int((pred == y).sum().item())
            total += int(y.size(0))

        train_loss = running_loss / max(total, 1)
        train_acc = correct / max(total, 1)
        val_loss, val_acc = evaluate_loader(model, val_loader, device)
        scheduler.step()

        history.train_loss.append(train_loss)
        history.train_acc.append(train_acc)
        history.val_loss.append(val_loss)
        history.val_acc.append(val_acc)

        print(
            f"Epoch {epoch:02d}/{cfg.epochs} | "
            f"train_loss={train_loss:.4f} acc={train_acc:.3f} | "
            f"val_loss={val_loss:.4f} acc={val_acc:.3f}"
        )

        if val_loss < best_val:
            best_val = val_loss
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "config": asdict(cfg),
                    "n_mels": N_MELS,
                    "n_classes": 10,
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                    "epoch": epoch,
                },
                best_path,
            )

    elapsed = time.time() - t0
    meta = {
        "epochs": cfg.epochs,
        "batch_size": cfg.batch_size,
        "lr": cfg.lr,
        "weight_decay": cfg.weight_decay,
        "optimizer": "AdamW",
        "loss": "CrossEntropyLoss",
        "device": str(device),
        "params": count_parameters(model),
        "train_size": len(train_samples),
        "val_size": len(val_samples),
        "best_val_loss": best_val,
        "seconds": round(elapsed, 1),
        "history": asdict(history),
    }
    (out_dir / "train_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Лучшая модель: {best_path} (val_loss={best_val:.4f}), время {elapsed:.1f} с")

    # загружаем лучшие веса
    ckpt = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    return model, history, best_path


def load_trained_model(ckpt_path: Path | None = None, device: str | None = None) -> SpeechCRNN:
    path = Path(ckpt_path or (DEFAULT_OUT / "best_model.pt"))
    device_t = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    ckpt = torch.load(path, map_location=device_t, weights_only=False)
    model = SpeechCRNN(
        n_mels=int(ckpt.get("n_mels", N_MELS)),
        n_classes=int(ckpt.get("n_classes", 10)),
    ).to(device_t)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model
