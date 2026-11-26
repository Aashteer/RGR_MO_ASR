"""
Аугментация аудиоданных для РГР (блок 4):
шум, сдвиг по времени, изменение темпа и высоты тона.
"""

from __future__ import annotations

import numpy as np

from rgr.features import SAMPLE_RATE, normalize_audio


def add_noise(y: np.ndarray, snr_db: float = 15.0, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng()
    y = y.astype(np.float32)
    power = np.mean(y**2) + 1e-8
    noise_power = power / (10 ** (snr_db / 10.0))
    noise = rng.normal(0.0, np.sqrt(noise_power), size=y.shape).astype(np.float32)
    return normalize_audio(y + noise)


def time_shift(y: np.ndarray, max_shift_sec: float = 0.1, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng()
    shift = int(rng.uniform(-max_shift_sec, max_shift_sec) * SAMPLE_RATE)
    return np.roll(y, shift).astype(np.float32)


def change_speed(y: np.ndarray, rate: float = 1.0) -> np.ndarray:
    """Простое изменение темпа через линейную интерполяцию."""
    if abs(rate - 1.0) < 1e-3:
        return y.astype(np.float32)
    n = len(y)
    new_n = max(1, int(n / rate))
    x_old = np.linspace(0.0, 1.0, n, dtype=np.float32)
    x_new = np.linspace(0.0, 1.0, new_n, dtype=np.float32)
    return np.interp(x_new, x_old, y).astype(np.float32)


def change_pitch(y: np.ndarray, n_steps: float = 0.0, sr: int = SAMPLE_RATE) -> np.ndarray:
    if abs(n_steps) < 1e-3:
        return y.astype(np.float32)
    try:
        import librosa

        return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps).astype(np.float32)
    except Exception:
        # fallback: лёгкий resample как приближение
        factor = 2 ** (n_steps / 12.0)
        return change_speed(y, rate=factor)


def random_augment(y: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    """Лёгкая аугментация — агрессивная ломает короткие цифры."""
    rng = rng or np.random.default_rng()
    out = y.astype(np.float32)
    if rng.random() < 0.5:
        out = add_noise(out, snr_db=float(rng.uniform(18, 30)), rng=rng)
    if rng.random() < 0.5:
        out = time_shift(out, max_shift_sec=0.05, rng=rng)
    if rng.random() < 0.35:
        out = change_speed(out, rate=float(rng.uniform(0.95, 1.05)))
    # pitch_shift (librosa) намеренно не используем в горячем цикле — слишком медленно на CPU
    return normalize_audio(out)
