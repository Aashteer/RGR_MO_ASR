"""Загрузка и валидация аудиофайлов."""

from __future__ import annotations

from pathlib import Path

from config.settings import SUPPORTED_EXTENSIONS


class AudioLoadError(Exception):
    pass


def validate_audio_file(path: str | Path) -> Path:
    file_path = Path(path).resolve()
    if not file_path.exists():
        raise AudioLoadError(f"Файл не найден: {file_path}")
    if not file_path.is_file():
        raise AudioLoadError(f"Путь не является файлом: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise AudioLoadError(
            f"Неподдерживаемый формат: {file_path.suffix}. "
            f"Поддерживаются: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    if file_path.stat().st_size == 0:
        raise AudioLoadError("Файл пуст")
    return file_path

