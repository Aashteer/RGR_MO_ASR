"""Стили интерфейса приложения транскрибации (ВКР)."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #f0f2f5;
}

QWidget#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e3a5f, stop:1 #2d5a8e);
    border-radius: 0px;
}

QLabel#appTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: bold;
}

QLabel#appSubtitle {
    color: #b8cfe8;
    font-size: 12px;
}

QWidget#card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

QLabel#cardTitle {
    color: #1e293b;
    font-size: 13px;
    font-weight: bold;
}

QLabel#hint {
    color: #64748b;
    font-size: 11px;
}

QLabel#fileName {
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
}

QLabel#fileMeta {
    color: #64748b;
    font-size: 11px;
}

QWidget#dropZone {
    background-color: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 10px;
}

QWidget#dropZone[dragActive="true"] {
    background-color: #eff6ff;
    border-color: #3b82f6;
}

QLabel#dropLabel {
    color: #475569;
    font-size: 13px;
}

QLabel#dropHint {
    color: #94a3b8;
    font-size: 11px;
}

QPushButton {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #cbd5e1;
}

QPushButton:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    padding: 10px 24px;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}

QPushButton#primaryBtn:pressed {
    background-color: #1e40af;
}

QPushButton#primaryBtn:disabled {
    background-color: #93c5fd;
    color: #eff6ff;
}

QPushButton#dangerBtn {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
}

QPushButton#dangerBtn:hover {
    background-color: #fee2e2;
}

QPushButton#exportBtn {
    background-color: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
}

QPushButton#exportBtn:hover {
    background-color: #dcfce7;
}

QPushButton#exportBtn:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QPushButton#themeBtn {
    background-color: rgba(255, 255, 255, 0.15);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}

QPushButton#themeBtn:hover {
    background-color: rgba(255, 255, 255, 0.25);
}

QComboBox, QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1e293b;
    font-size: 12px;
}

QComboBox:hover, QLineEdit:hover {
    border-color: #94a3b8;
}

QComboBox:focus, QLineEdit:focus {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QCheckBox {
    color: #334155;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #6366f1);
    border-radius: 6px;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
    font-size: 12px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    color: #1e293b;
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: #bfdbfe;
}

QTextEdit#resultText {
    font-family: "Segoe UI", "Calibri", sans-serif;
}

QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
}

QWidget#footer {
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
}

QLabel#footerLabel {
    font-weight: 600;
    color: #334155;
    font-size: 12px;
}

QLabel#badge {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}

QLabel#badgeOk {
    background-color: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}

QLabel#badgeWarn {
    background-color: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}

QLabel#progressLabel {
    color: #334155;
    font-size: 12px;
    font-weight: 600;
}

QLabel#progressTime {
    color: #64748b;
    font-size: 11px;
}

QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
"""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #0f172a;
}

QWidget#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0c1929, stop:1 #1e3a5f);
}

QLabel#appTitle { color: #f1f5f9; font-size: 20px; font-weight: bold; }
QLabel#appSubtitle { color: #94a3b8; font-size: 12px; }

QWidget#card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
}

QLabel#cardTitle { color: #e2e8f0; font-size: 13px; font-weight: bold; }
QLabel#hint { color: #94a3b8; font-size: 11px; }
QLabel#fileName { color: #f8fafc; font-size: 13px; font-weight: 600; }
QLabel#fileMeta { color: #94a3b8; font-size: 11px; }

QWidget#dropZone {
    background-color: #1e293b;
    border: 2px dashed #475569;
    border-radius: 10px;
}
QWidget#dropZone[dragActive="true"] {
    background-color: #1e3a5f;
    border-color: #3b82f6;
}
QLabel#dropLabel { color: #cbd5e1; font-size: 13px; }
QLabel#dropHint { color: #64748b; font-size: 11px; }

QPushButton {
    background-color: #334155;
    color: #e2e8f0;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover { background-color: #475569; }
QPushButton:disabled { background-color: #1e293b; color: #64748b; }

QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
}
QPushButton#primaryBtn:hover { background-color: #1d4ed8; }
QPushButton#primaryBtn:disabled { background-color: #1e3a5f; color: #64748b; }

QPushButton#dangerBtn {
    background-color: #450a0a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
}
QPushButton#exportBtn {
    background-color: #14532d;
    color: #bbf7d0;
    border: 1px solid #166534;
}
QPushButton#exportBtn:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #334155;
}

QPushButton#themeBtn {
    background-color: transparent;
    color: #e2e8f0;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}
QPushButton#themeBtn:hover { background-color: #334155; }

QComboBox, QLineEdit {
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e2e8f0;
    font-size: 12px;
}
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}

QCheckBox { color: #cbd5e1; font-size: 12px; }
QCheckBox::indicator {
    border: 1px solid #475569;
    background: #0f172a;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QProgressBar {
    background-color: #334155;
    border: none;
    border-radius: 6px;
    height: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #818cf8);
    border-radius: 6px;
}

QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 8px;
    background: #1e293b;
}
QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #1e293b;
    color: #60a5fa;
    border-bottom: 2px solid #3b82f6;
}

QTextEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    color: #e2e8f0;
    font-size: 13px;
    selection-background-color: #1d4ed8;
}

QStatusBar {
    background-color: #1e293b;
    color: #94a3b8;
    border-top: 1px solid #334155;
}

QLabel#badge {
    background-color: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #1d4ed8;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}
QLabel#badgeOk {
    background-color: #14532d;
    color: #86efac;
    border: 1px solid #166534;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}
QLabel#badgeWarn {
    background-color: #451a03;
    color: #fcd34d;
    border: 1px solid #92400e;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 600;
}

QLabel#progressLabel { color: #e2e8f0; font-size: 12px; font-weight: 600; }
QLabel#progressTime { color: #94a3b8; font-size: 11px; }

QWidget#footer {
    background-color: #1e293b;
    border-top: 1px solid #334155;
}
QLabel#footerLabel { font-weight: 600; color: #cbd5e1; font-size: 12px; }

QScrollBar:vertical { background: #1e293b; width: 8px; }
QScrollBar::handle:vertical { background: #475569; border-radius: 4px; }
"""


def get_stylesheet(dark: bool = False) -> str:
    return DARK_STYLESHEET if dark else APP_STYLESHEET
