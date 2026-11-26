"""Преобразование аудио через FFmpeg (раздел 3.5 ВКР)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from config.settings import TARGET_CHANNELS, TARGET_SAMPLE_RATE, TEMP_DIR, settings


class FFmpegError(Exception):
    pass


def _ffmpeg_executable() -> str:
    bundled = Path(settings.ffmpeg_path) if settings.ffmpeg_path else None
    if bundled and bundled.exists():
        return str(bundled)
    for base in (PROJECT_ROOT,):
        candidate = base / "tools" / "ffmpeg" / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
    exe = shutil.which("ffmpeg")
    if not exe:
        raise FFmpegError(
            "FFmpeg не найден. Установите FFmpeg и добавьте в PATH, "
            "либо укажите путь в config/settings.py (ffmpeg_path)."
        )
    return exe


def convert_to_wav(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    Конвертирует аудио/видео в WAV 16 кГц, моно — стандарт для ASR.
    """
    input_path = Path(input_path)
    if output_path is None:
        output_path = TEMP_DIR / f"{input_path.stem}_16k.wav"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        _ffmpeg_executable(),
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-map",
        "0:a:0?",
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-ac",
        str(TARGET_CHANNELS),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise FFmpegError(f"Ошибка FFmpeg:\n{result.stderr}")
    if not output_path.exists():
        raise FFmpegError("FFmpeg завершился без создания выходного файла")
    return output_path


def extract_wav_segment(
    wav_path: str | Path,
    start_sec: float,
    duration_sec: float,
    output_path: str | Path | None = None,
) -> Path:
    """Вырезает фрагмент WAV для пошаговой транскрибации (быстрая отмена)."""
    wav_path = Path(wav_path)
    if output_path is None:
        output_path = TEMP_DIR / f"{wav_path.stem}_seg_{int(start_sec)}.wav"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        _ffmpeg_executable(),
        "-y",
        "-ss",
        str(start_sec),
        "-t",
        str(duration_sec),
        "-i",
        str(wav_path),
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-ac",
        str(TARGET_CHANNELS),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise FFmpegError(f"Ошибка FFmpeg (сегмент):\n{result.stderr}")
    return output_path


def get_audio_duration(wav_path: str | Path) -> float:
    """Длительность аудио в секундах через ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        ffmpeg = _ffmpeg_executable()
        ffprobe = str(Path(ffmpeg).with_name("ffprobe.exe"))
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        try:
            import librosa
            return float(librosa.get_duration(path=str(wav_path)))
        except Exception as exc:
            raise FFmpegError(f"Не удалось определить длительность: {result.stderr}") from exc
    return float(result.stdout.strip())
