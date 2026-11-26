#!/usr/bin/env python3
"""
Скрипт загрузки моделей для ВКР:
- Whisper (faster-whisper скачает автоматически при первом запуске)
- Qwen3-14B-Q4_K_M (GGUF с Hugging Face)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import QWEN_MODELS_DIR, WHISPER_MODELS_DIR


def download_whisper(model_size: str = "large-v3") -> None:
    print(f"Загрузка Whisper {model_size}...")
    from faster_whisper import WhisperModel

    WhisperModel(model_size, download_root=str(WHISPER_MODELS_DIR))
    print(f"Whisper {model_size} готов в {WHISPER_MODELS_DIR}")


def download_qwen() -> None:
    import shutil

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Установите: pip install huggingface_hub")
        sys.exit(1)

    repo = "Kondara/Qwen3-14B-Q4_K_M-GGUF"
    filename = "qwen3-14b-q4_k_m.gguf"
    target = QWEN_MODELS_DIR / "Qwen3-14B-Q4_K_M.gguf"

    if target.exists() and target.stat().st_size > 8_000_000_000:
        print(f"Qwen уже скачан: {target}")
        return

    print(f"Загрузка {filename} (~8.5 ГБ)...")
    cached = hf_hub_download(
        repo_id=repo,
        filename=filename,
        cache_dir=str(QWEN_MODELS_DIR),
    )
    cached_path = Path(cached)
    if cached_path.resolve() != target.resolve():
        shutil.copy2(cached_path, target)
    print(f"Qwen сохранён: {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--whisper", action="store_true", help="Скачать Whisper")
    parser.add_argument("--qwen", action="store_true", help="Скачать Qwen GGUF")
    parser.add_argument("--model", default="large-v3", help="Размер Whisper")
    parser.add_argument("--all", action="store_true", help="Скачать всё")
    args = parser.parse_args()

    if args.all or args.whisper:
        download_whisper(args.model)
    if args.all or args.qwen:
        download_qwen()
    if not (args.all or args.whisper or args.qwen):
        parser.print_help()


if __name__ == "__main__":
    main()
