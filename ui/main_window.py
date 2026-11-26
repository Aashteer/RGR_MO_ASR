"""Главное окно приложения (листинги 4.1–4.2, PySide6)."""

from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.settings import AppSettings, resolve_device, settings
from config.user_config import load_hf_token, save_hf_token
from export import ExportData, export_docx, export_pdf, export_txt
from llm.sanitize import is_valid_russian_llm_output, pick_best_text
from pipeline import PipelineResult, TranscriptionPipeline
from ui.dialogs import show_error, show_info
from ui.styles import get_stylesheet
from ui.widgets import DropZone, FileInfoCard, ProgressWidget


class ProcessingWorker(QThread):
    progress = Signal(str, int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, audio_path: str, pipeline: TranscriptionPipeline):
        super().__init__()
        self.audio_path = audio_path
        self.pipeline = pipeline
        self._start_time = 0.0

    def run(self) -> None:
        self._start_time = time.time()
        try:
            result = self.pipeline.process(
                self.audio_path,
                on_progress=self._on_progress,
            )
            self.finished_ok.emit(result)
        except InterruptedError:
            self.failed.emit("Транскрибация отменена")
        except Exception as exc:
            self.failed.emit(str(exc))

    def cancel(self) -> None:
        self.pipeline.cancel()


    def _on_progress(self, msg: str, pct: int) -> None:
        elapsed = time.time() - self._start_time
        mins, secs = divmod(int(elapsed), 60)
        self.progress.emit(msg, pct, f"{mins:02d}:{secs:02d}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система автоматической транскрибации")
        self.resize(1280, 860)
        self.setMinimumSize(960, 640)

        self.audio_path: str | None = None
        self.last_result: PipelineResult | None = None
        self.worker: ProcessingWorker | None = None
        self.pipeline = TranscriptionPipeline()
        self._dark_theme = False

        self.setStyleSheet(get_stylesheet(self._dark_theme))
        self._build_ui()
        self._update_system_badges()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 12)
        body_layout.setSpacing(16)

        body_layout.addWidget(self._build_left_panel(), 0)
        body_layout.addWidget(self._build_right_panel(), 1)
        root.addWidget(body, 1)

        root.addWidget(self._build_footer())

        self.statusBar().showMessage("Готов к работе — выберите аудио или видео")

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(72)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("Система автоматической транскрибации")
        title.setObjectName("appTitle")
        subtitle = QLabel("ВКР · Whisper ASR · Диаризация · Экспорт TXT / DOCX / PDF")
        subtitle.setObjectName("appSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block, 1)

        badges = QHBoxLayout()
        badges.setSpacing(8)
        self.badge_device = QLabel()
        self.badge_device.setObjectName("badge")
        self.badge_ffmpeg = QLabel()
        self.badge_ffmpeg.setObjectName("badgeOk")
        badges.addWidget(self.badge_device)
        badges.addWidget(self.badge_ffmpeg)

        self.btn_theme = QPushButton("🌙 Тёмная")
        self.btn_theme.setObjectName("themeBtn")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        badges.addWidget(self.btn_theme)

        layout.addLayout(badges)

        return header

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self._on_file_selected)
        self.drop_zone.btn_browse.clicked.connect(self.drop_zone.browse_file)
        layout.addWidget(self.drop_zone)

        self.file_card = FileInfoCard()
        layout.addWidget(self.file_card)

        settings_card = QWidget()
        settings_card.setObjectName("card")
        s_layout = QVBoxLayout(settings_card)
        s_layout.setContentsMargins(16, 14, 16, 14)
        s_layout.setSpacing(10)

        s_title = QLabel("Настройки")
        s_title.setObjectName("cardTitle")
        s_layout.addWidget(s_title)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Whisper:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText(settings.whisper.model_size)
        self.model_combo.setToolTip("large-v3 — лучшее качество. tiny/base — только для быстрых тестов.")
        model_row.addWidget(self.model_combo, 1)
        s_layout.addLayout(model_row)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Авто", "Русский", "English", "Deutsch", "Français", "Español"])
        self.lang_combo.setCurrentText("Русский")
        lang_row.addWidget(self.lang_combo, 1)
        s_layout.addLayout(lang_row)

        self.chk_diar = QCheckBox("Диаризация дикторов (pyannote)")
        self.chk_diar.setChecked(settings.enable_diarization)
        self.chk_diar.setToolTip("Разделение речи разных спикеров. Требует HF токен.")
        s_layout.addWidget(self.chk_diar)

        self.chk_vocal = QCheckBox("Выделить вокал (для песен)")
        self.chk_vocal.setChecked(settings.enable_vocal_isolation)
        self.chk_vocal.setToolTip("Отделяет голос от музыки перед распознаванием")
        s_layout.addWidget(self.chk_vocal)

        self.chk_llm = QCheckBox("LLM постобработка (Qwen)")
        self.chk_llm.setChecked(settings.enable_llm_postprocess)
        self.chk_llm.setToolTip("Коррекция текста и краткое содержание. Медленно без GPU.")
        s_layout.addWidget(self.chk_llm)

        token_row = QVBoxLayout()
        token_row.addWidget(QLabel("HF токен:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("hf_... (для диаризации)")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        saved_token = load_hf_token()
        if saved_token:
            self.token_input.setText(saved_token)
        token_row.addWidget(self.token_input)
        s_layout.addLayout(token_row)

        layout.addWidget(settings_card)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶  Начать транскрибацию")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_transcription)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("dangerBtn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_transcription)

        btn_row.addWidget(self.btn_start, 2)
        btn_row.addWidget(self.btn_cancel, 1)
        layout.addLayout(btn_row)

        layout.addStretch()
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.progress_widget = ProgressWidget()
        layout.addWidget(self.progress_widget)

        self.tabs = QTabWidget()
        self.text_raw = QTextEdit()
        self.text_raw.setObjectName("resultText")
        self.text_raw.setReadOnly(True)
        self.text_raw.setPlaceholderText("Транскрипция появится здесь после обработки...")

        self.text_summary = QTextEdit()
        self.text_summary.setObjectName("resultText")
        self.text_summary.setReadOnly(True)
        self.text_summary.setPlaceholderText("Краткое содержание (при включённой LLM)...")

        self.text_timestamps = QTextEdit()
        self.text_timestamps.setObjectName("resultText")
        self.text_timestamps.setReadOnly(True)
        self.text_timestamps.setPlaceholderText("Транскрипция с временными метками...")

        self.tabs.addTab(self.text_raw, "📝 Транскрипция")
        self.tabs.addTab(self.text_summary, "📋 Краткое содержание")
        self.tabs.addTab(self.text_timestamps, "⏱ С метками времени")

        self.text_log = QTextEdit()
        self.text_log.setObjectName("resultText")
        self.text_log.setReadOnly(True)
        self.text_log.setPlaceholderText("Журнал обработки (LLM, диаризация)...")
        self.tabs.addTab(self.text_log, "📊 Журнал")

        layout.addWidget(self.tabs, 1)

        return panel

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 10, 24, 10)

        export_label = QLabel("Экспорт:")
        export_label.setObjectName("footerLabel")
        layout.addWidget(export_label)

        self.btn_txt = QPushButton("📄 TXT")
        self.btn_docx = QPushButton("📘 DOCX")
        self.btn_pdf = QPushButton("📕 PDF")
        for btn in (self.btn_txt, self.btn_docx, self.btn_pdf):
            btn.setObjectName("exportBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setEnabled(False)

        self.btn_txt.clicked.connect(lambda: self.export_result("txt"))
        self.btn_docx.clicked.connect(lambda: self.export_result("docx"))
        self.btn_pdf.clicked.connect(lambda: self.export_result("pdf"))

        layout.addWidget(self.btn_txt)
        layout.addWidget(self.btn_docx)
        layout.addWidget(self.btn_pdf)
        layout.addStretch()

        self.result_badge = QLabel("")
        self.result_badge.setObjectName("badgeOk")
        self.result_badge.hide()
        layout.addWidget(self.result_badge)

        return footer

    def _update_system_badges(self) -> None:
        device = resolve_device(settings.whisper.device)
        gpu = "GPU" if device == "cuda" else "CPU"
        self.badge_device.setText(f"⚡ {gpu}")

        import shutil
        ffmpeg_ok = shutil.which("ffmpeg") is not None
        self.badge_ffmpeg.setObjectName("badgeOk" if ffmpeg_ok else "badgeWarn")
        self.badge_ffmpeg.setText("✓ FFmpeg" if ffmpeg_ok else "✗ FFmpeg")
        self.badge_ffmpeg.style().unpolish(self.badge_ffmpeg)
        self.badge_ffmpeg.style().polish(self.badge_ffmpeg)

    def toggle_theme(self) -> None:
        self._dark_theme = not self._dark_theme
        self.setStyleSheet(get_stylesheet(self._dark_theme))
        self.btn_theme.setText("☀️ Светлая" if self._dark_theme else "🌙 Тёмная")

    def _on_file_selected(self, path: str) -> None:
        self.audio_path = path
        self.file_card.set_file(path)
        self.btn_start.setEnabled(True)
        self.drop_zone.drop_label.setText("Файл выбран ✓")
        self.statusBar().showMessage(f"Выбран: {Path(path).name}")

    def _apply_settings(self) -> AppSettings:
        cfg = AppSettings()
        cfg.whisper.model_size = self.model_combo.currentText()

        lang_map = {
            "Авто": None,
            "Русский": "ru",
            "English": "en",
            "Deutsch": "de",
            "Français": "fr",
            "Español": "es",
        }
        cfg.whisper.language = lang_map.get(self.lang_combo.currentText())
        cfg.enable_diarization = self.chk_diar.isChecked()
        cfg.enable_vocal_isolation = self.chk_vocal.isChecked()
        cfg.enable_llm_postprocess = self.chk_llm.isChecked()

        token = self.token_input.text().strip()
        if token:
            cfg.diarization.hf_token = token
            os.environ["HF_TOKEN"] = token
            save_hf_token(token)

        return cfg

    def start_transcription(self) -> None:
        if not self.audio_path:
            show_error(self, "Ошибка", "Сначала выберите файл")
            return

        if self.chk_diar.isChecked() and not self.token_input.text().strip():
            reply = QMessageBox.question(
                self,
                "HF токен",
                "Диаризация включена, но HF токен не указан.\n"
                "Продолжить без диаризации?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        cfg = self._apply_settings()
        self.pipeline = TranscriptionPipeline(cfg)

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self._set_export_enabled(False)
        self.text_raw.clear()
        self.text_summary.clear()
        self.text_timestamps.clear()
        self.text_log.clear()
        self.result_badge.hide()

        self.worker = ProcessingWorker(self.audio_path, self.pipeline)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_ok.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def cancel_transcription(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_widget.set_progress("Отменено", 0, "")
        self.statusBar().showMessage("Транскрибация отменена")

    def on_progress(self, message: str, percent: int, elapsed: str) -> None:
        self.progress_widget.set_progress(message, percent, elapsed)
        self.statusBar().showMessage(f"{message}  [{elapsed}]")

    def on_finished(self, result: PipelineResult) -> None:
        self.last_result = result
        display = pick_best_text(result.raw_transcription, result.formatted_transcription)
        self.text_raw.setPlainText(display)

        summary = result.summary.strip()
        if summary and is_valid_russian_llm_output(summary):
            self.text_summary.setPlainText(summary)
        else:
            self.text_summary.setPlainText(
                "Краткое содержание не сформировано.\nВключите «LLM постобработка» для генерации."
            )

        ts_lines = []
        for seg in result.segments:
            start = self._fmt_time(seg["start"])
            end = self._fmt_time(seg["end"])
            speaker = f" [{seg['speaker']}]" if seg.get("speaker") else ""
            ts_lines.append(f"[{start} → {end}]{speaker} {seg['text']}")
        self.text_timestamps.setPlainText("\n".join(ts_lines))

        if result.log:
            self.text_log.setPlainText("\n".join(f"• {line}" for line in result.log))

        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._set_export_enabled(True)

        lang = result.language or "?"
        dur = result.duration_sec
        chars = len(display)
        self.result_badge.setText(f"✓ {chars} симв. · {lang} · {dur:.0f} с")
        self.result_badge.show()

        self.progress_widget.set_progress("Готово!", 100, "")
        self.statusBar().showMessage(
            f"Транскрибация завершена — {chars} символов, язык: {lang}"
        )
        show_info(self, "Готово", f"Обработка завершена.\nСимволов: {chars}\nЯзык: {lang}")

    def on_failed(self, error: str) -> None:
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_widget.set_progress("Отменено" if "отменена" in error.lower() else "Ошибка", 0, "")
        self.statusBar().showMessage(error)
        if "отменена" not in error.lower():
            show_error(self, "Ошибка обработки", f"{error}\n\nПроверьте FFmpeg, модели Whisper и настройки.")

    def _set_export_enabled(self, enabled: bool) -> None:
        self.btn_txt.setEnabled(enabled)
        self.btn_docx.setEnabled(enabled)
        self.btn_pdf.setEnabled(enabled)

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def export_result(self, fmt: str) -> None:
        if not self.last_result:
            show_error(self, "Ошибка", "Нет данных для экспорта")
            return

        ext_map = {"txt": "Text (*.txt)", "docx": "Word (*.docx)", "pdf": "PDF (*.pdf)"}
        default_name = Path(self.last_result.source_file).stem + f"_transcript.{fmt}"
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", default_name, ext_map[fmt])
        if not path:
            return

        data = self.pipeline.to_export_data(self.last_result)
        try:
            if fmt == "txt":
                export_txt(data, path)
            elif fmt == "docx":
                export_docx(data, path)
            else:
                export_pdf(data, path)
            show_info(self, "Экспорт", f"Файл сохранён:\n{path}")
        except Exception as exc:
            show_error(self, "Ошибка экспорта", str(exc))
