"""Конфигурация приложения транскрибации (ВКР)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _resolve_roots() -> tuple[Path, Path]:
    """project_root — рабочая папка (models, output); bundle_root — ресурсы внутри exe."""
    if getattr(sys, "frozen", False):
        project = Path(sys.executable).resolve().parent
        bundle = Path(getattr(sys, "_MEIPASS", project))
        return project, bundle
    root = Path(__file__).resolve().parent.parent
    return root, root


# Корень проекта (рядом с exe — models, output, temp)
PROJECT_ROOT, BUNDLE_ROOT = _resolve_roots()
MODELS_DIR = PROJECT_ROOT / "models"
WHISPER_MODELS_DIR = MODELS_DIR / "whisper"
QWEN_MODELS_DIR = MODELS_DIR / "qwen"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

for _dir in (MODELS_DIR, WHISPER_MODELS_DIR, QWEN_MODELS_DIR, OUTPUT_DIR, TEMP_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Поддерживаемые форматы
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wma",
    ".amr", ".3gp", ".webm", ".oga",
}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

# Параметры аудио (стандарт ASR — 16 кГц, моно)
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1


@dataclass
class WhisperSettings:
    """Настройки faster-whisper (листинг 4.3–4.4 ВКР)."""

    model_size: str = "large-v3"
    device: str = "auto"
    compute_type: str = "auto"
    beam_size: int = 5
    vad_filter: bool = False
    word_timestamps: bool = True
    language: str | None = "ru"
    download_root: str = str(WHISPER_MODELS_DIR)


@dataclass
class DiarizationSettings:
    """Настройки pyannote.audio."""

    # Модель диаризации (требует HF token)
    pipeline_name: str = "pyannote/speaker-diarization-3.1"
    hf_token: str = field(default_factory=lambda: os.getenv("HF_TOKEN", ""))
    min_speakers: int | None = None
    max_speakers: int | None = None


@dataclass
class LLMSettings:
    """Настройки Qwen3-14B-Q4_K_M (GGUF, llama-cpp)."""

    model_filename: str = "Qwen3-14B-Q4_K_M.gguf"
    model_path: str = field(
        default_factory=lambda: str(QWEN_MODELS_DIR / "Qwen3-14B-Q4_K_M.gguf")
    )
    n_ctx: int = 8192
    n_gpu_layers: int = -1  # -1 = все слои на GPU; на CPU будет 0
    temperature: float = 0.3
    max_tokens: int = 2048
    enabled: bool = True


@dataclass
class AppSettings:
    """Главный конфиг приложения."""

    whisper: WhisperSettings = field(default_factory=WhisperSettings)
    diarization: DiarizationSettings = field(default_factory=DiarizationSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    enable_diarization: bool = False
    enable_llm_postprocess: bool = False
    enable_vocal_isolation: bool = True
    enable_summarization: bool = True
    ffmpeg_path: str | None = field(default_factory=lambda: _default_ffmpeg_path())


def _default_ffmpeg_path() -> str | None:
    for base in (BUNDLE_ROOT, PROJECT_ROOT):
        candidate = base / "tools" / "ffmpeg" / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
    return None


def resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def resolve_compute_type(compute_type: str, device: str) -> str:
    if compute_type != "auto":
        return compute_type
    return "float16" if device == "cuda" else "int8"


def resolve_gpu_layers(n_gpu_layers: int) -> int:
    if n_gpu_layers >= 0:
        return n_gpu_layers
    return -1 if resolve_device("auto") == "cuda" else 0


settings = AppSettings()
