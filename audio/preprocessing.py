"""Предобработка аудиосигнала (нормализация, VAD-подготовка)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import librosa
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None

from config.settings import TARGET_SAMPLE_RATE


def normalize_audio(wav_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    Нормализация уровня громкости и удаление DC-смещения.
    """
    if librosa is None or sf is None:
        return Path(wav_path)

    wav_path = Path(wav_path)
    if output_path is None:
        output_path = wav_path.parent / f"{wav_path.stem}_norm.wav"
    output_path = Path(output_path)

    audio, sr = librosa.load(str(wav_path), sr=TARGET_SAMPLE_RATE, mono=True)
    audio = audio - np.mean(audio)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95

    sf.write(str(output_path), audio, sr, subtype="PCM_16")
    return output_path
