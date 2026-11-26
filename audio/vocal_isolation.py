"""Выделение вокала из песен и записей с фоновой музыкой."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from config.settings import TEMP_DIR


def isolate_vocals(wav_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    Пытается выделить вокал через Demucs, иначе — FFmpeg-фильтры.
    """
    wav_path = Path(wav_path)
    if output_path is None:
        output_path = TEMP_DIR / f"{wav_path.stem}_vocals.wav"
    output_path = Path(output_path)

    if _try_demucs(wav_path, output_path):
        return output_path
    return _enhance_vocals_ffmpeg(wav_path, output_path)


def _try_demucs(wav_path: Path, output_path: Path) -> bool:
    try:
        import demucs  # noqa: F401
    except ImportError:
        return False

    out_root = TEMP_DIR / "demucs_out"
    out_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        "htdemucs",
        "--two-stems",
        "vocals",
        "-o",
        str(out_root),
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return False

    vocals = out_root / "htdemucs" / wav_path.stem / "vocals.wav"
    if not vocals.exists():
        return False

    shutil.copy2(vocals, output_path)
    return output_path.exists()


def _enhance_vocals_ffmpeg(wav_path: Path, output_path: Path) -> Path:
    """Лёгкое усиление вокала без Demucs."""
    import shutil as sh

    ffmpeg = sh.which("ffmpeg")
    if not ffmpeg:
        shutil.copy2(wav_path, output_path)
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(wav_path),
        "-af",
        "highpass=f=120,lowpass=f=3800,compand=attacks=0:points=-80/-80|-45/-30|-27/-15|0/-5|20/-5,volume=1.6",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not output_path.exists():
        shutil.copy2(wav_path, output_path)
    return output_path
