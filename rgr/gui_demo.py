#!/usr/bin/env python3
"""
GUI-демонстрация обученной CRNN-модели (требование блока 4 РГР).
Распознавание произнесённой цифры из wav/mp3 файла.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rgr.evaluate import predict_file
from rgr.train import load_trained_model


class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("РГР — распознавание произнесённых цифр (CRNN)")
        self.resize(720, 480)
        self.model = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        title = QLabel("Демонстрация обученной модели CRNN (FSDD, цифры 0–9)")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        hint = QLabel(
            "Выберите wav-файл с произнесённой цифрой "
            "(можно взять из data/fsdd/recordings)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        row = QHBoxLayout()
        self.btn_load_model = QPushButton("Загрузить модель")
        self.btn_open = QPushButton("Выбрать аудио…")
        self.btn_predict = QPushButton("Распознать")
        self.btn_predict.setEnabled(False)
        row.addWidget(self.btn_load_model)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_predict)
        layout.addLayout(row)

        self.file_label = QLabel("Файл не выбран")
        layout.addWidget(self.file_label)

        self.out = QTextEdit()
        self.out.setReadOnly(True)
        layout.addWidget(self.out)

        self.audio_path: Path | None = None
        self.btn_load_model.clicked.connect(self.load_model)
        self.btn_open.clicked.connect(self.open_file)
        self.btn_predict.clicked.connect(self.run_predict)

        # автозагрузка, если чекпоинт есть
        ckpt = ROOT / "models" / "rgr_crnn" / "best_model.pt"
        if ckpt.exists():
            try:
                self.model = load_trained_model(ckpt)
                self.out.append(f"Модель загружена: {ckpt}")
                self.btn_predict.setEnabled(True)
            except Exception as exc:
                self.out.append(f"Не удалось автозагрузить модель: {exc}")

    def load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Чекпоинт модели", str(ROOT / "models" / "rgr_crnn"), "PyTorch (*.pt)"
        )
        if not path:
            return
        try:
            self.model = load_trained_model(Path(path))
            self.out.append(f"Модель загружена: {path}")
            self.btn_predict.setEnabled(self.audio_path is not None)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Аудиофайл",
            str(ROOT / "data" / "fsdd" / "recordings"),
            "Audio (*.wav *.mp3 *.flac *.m4a)",
        )
        if not path:
            return
        self.audio_path = Path(path)
        self.file_label.setText(str(self.audio_path))
        self.btn_predict.setEnabled(self.model is not None)

    def run_predict(self) -> None:
        if self.model is None or self.audio_path is None:
            return
        try:
            result = predict_file(self.model, self.audio_path)
            lines = [
                f"Файл: {self.audio_path.name}",
                f"Распознанная цифра (текст): {result['text']}",
                f"Уверенность: {result['confidence']:.2%}",
                "",
                "Распределение вероятностей:",
            ]
            for k, v in sorted(result["probs"].items(), key=lambda kv: -kv[1]):
                lines.append(f"  {k}: {v:.2%}")
            self.out.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка распознавания", str(exc))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("РГР CRNN Demo")
    w = DemoWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
