"""
Предобработка аудио: mel-спектрограммы и MFCC.
Блок 4 РГР — преобразование звука в признаки для нейросети.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
N_MELS = 64
N_MFCC = 40
N_FFT = 1024
HOP_LENGTH = 256
MAX_FRAMES = 80  # фиксированная длина по времени (~1.3 с)


def load_audio(path: str | Path, sr: int = SAMPLE_RATE) -> np.ndarray:
    import librosa

    y, _ = librosa.load(str(path), sr=sr, mono=True)
    return y.astype(np.float32)


def normalize_audio(y: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak < eps:
        return y
    return (y / peak).astype(np.float32)


def mel_spectrogram(
    y: np.ndarray,
    sr: int = SAMPLE_RATE,
    n_mels: int = N_MELS,
    n_fft: int = N_FFT,
    hop_length: int = HOP_LENGTH,
) -> np.ndarray:
    import librosa

    y = normalize_audio(y)
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        n_mels=n_mels,
        power=2.0,
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)
    return mel_db.astype(np.float32)


def mfcc_features(
    y: np.ndarray,
    sr: int = SAMPLE_RATE,
    n_mfcc: int = N_MFCC,
    n_fft: int = N_FFT,
    hop_length: int = HOP_LENGTH,
) -> np.ndarray:
    import librosa

    y = normalize_audio(y)
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )
    return mfcc.astype(np.float32)


def pad_or_trim(feat: np.ndarray, max_frames: int = MAX_FRAMES) -> np.ndarray:
    """feat: (n_features, time) → фиксированная длина по времени."""
    n_feat, t = feat.shape
    if t >= max_frames:
        return feat[:, :max_frames]
    out = np.zeros((n_feat, max_frames), dtype=np.float32)
    out[:, :t] = feat
    return out


def standardize(feat: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    mean = feat.mean()
    std = feat.std()
    return ((feat - mean) / (std + eps)).astype(np.float32)


def extract_features(
    path: str | Path,
    kind: str = "mel",
    max_frames: int = MAX_FRAMES,
) -> np.ndarray:
    y = load_audio(path)
    if kind == "mfcc":
        feat = mfcc_features(y)
    else:
        feat = mel_spectrogram(y)
    feat = pad_or_trim(feat, max_frames=max_frames)
    return standardize(feat)


def save_mel_preview(path: str | Path, out_png: str | Path) -> None:
    """Сохранить визуализацию mel-спектрограммы для отчёта."""
    import matplotlib.pyplot as plt
    import librosa.display

    y = load_audio(path)
    mel = mel_spectrogram(y)
    fig, ax = plt.subplots(figsize=(8, 3))
    img = librosa.display.specshow(
        mel,
        sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH,
        x_axis="time",
        y_axis="mel",
        ax=ax,
    )
    ax.set_title(f"Mel-спектрограмма: {Path(path).name}")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    fig.tight_layout()
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
