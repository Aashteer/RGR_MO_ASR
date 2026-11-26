"""Вспомогательные виджеты интерфейса."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.settings import SUPPORTED_EXTENSIONS


class DropZone(QWidget):
    """Зона перетаскивания аудио/видео файлов."""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("🎵")
        self.icon_label.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_label = QLabel("Перетащите аудио или видео сюда")
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hint_label = QLabel("MP3 · WAV · MP4 · MKV · FLAC · OGG · M4A и др.")
        self.hint_label.setObjectName("dropHint")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_browse = QPushButton("Выбрать файл")
        self.btn_browse.setObjectName("primaryBtn")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.drop_label)
        layout.addWidget(self.hint_label)
        layout.addSpacing(8)
        layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        event.acceptProposedAction()
                        self.setProperty("dragActive", True)
                        self.style().unpolish(self)
                        self.style().polish(self)
                        return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self.file_dropped.emit(str(path))
                    event.acceptProposedAction()
                    return
        event.ignore()

    def browse_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудио или видео",
            "",
            "Медиафайлы (*.mp3 *.wav *.m4a *.mp4 *.flac *.mkv *.ogg *.opus *.webm *.avi *.mov *.aac *.wma *.amr *.3gp);;Все файлы (*.*)",
        )
        if file_name:
            self.file_dropped.emit(file_name)


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        self.label = QLabel("Готов к работе")
        self.label.setObjectName("progressLabel")
        self.time_label = QLabel("")
        self.time_label.setObjectName("progressTime")
        row.addWidget(self.label, 1)
        row.addWidget(self.time_label)
        layout.addLayout(row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar)

    def set_progress(self, message: str, percent: int, elapsed: str = "") -> None:
        self.label.setText(message)
        self.bar.setValue(max(0, min(100, percent)))
        self.time_label.setText(elapsed)


class FileInfoCard(QWidget):
    """Карточка с информацией о выбранном файле."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("Выбранный файл")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        self.file_name = QLabel("Файл не выбран")
        self.file_name.setObjectName("fileName")
        self.file_name.setWordWrap(True)
        layout.addWidget(self.file_name)

        self.file_meta = QLabel("")
        self.file_meta.setObjectName("fileMeta")
        layout.addWidget(self.file_meta)

    def set_file(self, path: str) -> None:
        p = Path(path)
        self.file_name.setText(p.name)
        try:
            size_mb = p.stat().st_size / (1024 * 1024)
            self.file_meta.setText(f"{p.suffix.upper()[1:]} · {size_mb:.1f} МБ · {p.parent}")
        except OSError:
            self.file_meta.setText(str(p.parent))

    def clear(self) -> None:
        self.file_name.setText("Файл не выбран")
        self.file_meta.setText("")
