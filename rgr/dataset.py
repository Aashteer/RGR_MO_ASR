"""
Датасет Free Spoken Digit Dataset (FSDD) для эксперимента РГР.
Задача: распознавание произнесённых цифр 0–9 (речь → класс/текст).
"""

from __future__ import annotations

import json
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rgr.augment import random_augment
from rgr.features import (
    MAX_FRAMES,
    load_audio,
    mel_spectrogram,
    pad_or_trim,
    standardize,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "fsdd"
FSDD_ZIP_URL = (
    "https://github.com/Jakobovski/free-spoken-digit-dataset/archive/refs/heads/master.zip"
)


@dataclass
class Sample:
    path: Path
    label: int  # 0..9
    speaker: str


def download_fsdd(dest: Path = DATA_DIR, force: bool = False) -> Path:
    """Скачать и распаковать FSDD. Возвращает путь к папке recordings."""
    dest.mkdir(parents=True, exist_ok=True)
    recordings = dest / "recordings"
    if recordings.exists() and any(recordings.glob("*.wav")) and not force:
        return recordings

    zip_path = dest / "fsdd.zip"
    print(f"Скачивание FSDD → {zip_path}", flush=True)
    urllib.request.urlretrieve(FSDD_ZIP_URL, zip_path)

    extract_dir = dest / "_extract"
    if extract_dir.exists():
        import shutil

        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    found = list(extract_dir.rglob("recordings"))
    if not found:
        raise RuntimeError("В архиве FSDD не найдена папка recordings")
    src = found[0]
    if recordings.exists():
        import shutil

        shutil.rmtree(recordings)
    src.rename(recordings)
    print(
        f"FSDD готов: {recordings} ({len(list(recordings.glob('*.wav')))} файлов)",
        flush=True,
    )
    return recordings


def parse_filename(path: Path) -> Sample | None:
    stem = path.stem
    parts = stem.split("_")
    if len(parts) < 3:
        return None
    try:
        label = int(parts[0])
    except ValueError:
        return None
    if not (0 <= label <= 9):
        return None
    return Sample(path=path, label=label, speaker=parts[1])


def load_samples(recordings: Path | None = None) -> list[Sample]:
    recordings = recordings or (DATA_DIR / "recordings")
    if not recordings.exists():
        recordings = download_fsdd()
    samples: list[Sample] = []
    for wav in sorted(recordings.glob("*.wav")):
        s = parse_filename(wav)
        if s is not None:
            samples.append(s)
    if not samples:
        raise RuntimeError(f"Нет wav-файлов в {recordings}")
    return samples


def split_by_speaker(
    samples: list[Sample],
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[Sample], list[Sample], list[Sample]]:
    """
    Стратифицированное разделение: для каждой пары (диктор, класс)
    записи делятся на train/val/test.
    """
    rng = np.random.default_rng(seed)
    buckets: dict[tuple[str, int], list[Sample]] = {}
    for s in samples:
        buckets.setdefault((s.speaker, s.label), []).append(s)

    train: list[Sample] = []
    val: list[Sample] = []
    test: list[Sample] = []
    for _, items in buckets.items():
        items = list(items)
        rng.shuffle(items)
        n = len(items)
        n_te = max(1, int(round(n * test_ratio))) if n >= 5 else max(1, n // 5 or 1)
        n_va = max(1, int(round(n * val_ratio))) if n >= 5 else max(1, n // 5 or 1)
        if n_te + n_va >= n:
            n_te = 1
            n_va = 1 if n > 2 else 0
        test.extend(items[:n_te])
        val.extend(items[n_te : n_te + n_va])
        train.extend(items[n_te + n_va :])
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


class DigitMelDataset:
    """PyTorch Dataset: mel → метка цифры. Mel кэшируются для ускорения."""

    def __init__(
        self,
        samples: list[Sample],
        augment: bool = False,
        max_frames: int = MAX_FRAMES,
        seed: int = 0,
    ):
        self.samples = samples
        self.augment = augment
        self.max_frames = max_frames
        self.rng = np.random.default_rng(seed)
        self._cache: dict[str, np.ndarray] = {}
        if not augment:
            print(f"Кэш mel для {len(samples)} файлов...", flush=True)
            for s in samples:
                self._cache[str(s.path)] = self._mel_from_path(s.path)

    def _mel_from_path(self, path: Path, y: np.ndarray | None = None) -> np.ndarray:
        if y is None:
            y = load_audio(path)
        mel = mel_spectrogram(y)
        mel = pad_or_trim(mel, max_frames=self.max_frames)
        return standardize(mel)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        import torch

        sample = self.samples[idx]
        if self.augment:
            y = load_audio(sample.path)
            y = random_augment(y, rng=self.rng)
            mel = self._mel_from_path(sample.path, y=y)
        else:
            mel = self._cache[str(sample.path)]
        x = torch.from_numpy(mel).unsqueeze(0)
        label = torch.tensor(sample.label, dtype=torch.long)
        return x, label


def dataset_stats(samples: list[Sample]) -> dict:
    from collections import Counter

    labels = Counter(s.label for s in samples)
    speakers = sorted({s.speaker for s in samples})
    return {
        "n_files": len(samples),
        "n_speakers": len(speakers),
        "speakers": speakers,
        "per_class": {str(k): labels[k] for k in range(10)},
    }


def save_manifest(
    train: list[Sample],
    val: list[Sample],
    test: list[Sample],
    out_path: Path,
) -> None:
    payload = {
        "train": dataset_stats(train),
        "val": dataset_stats(val),
        "test": dataset_stats(test),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
