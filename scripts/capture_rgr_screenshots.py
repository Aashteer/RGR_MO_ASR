#!/usr/bin/env python3
"""Скриншоты GUI для пояснительной записки РГР."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "output" / "rgr" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def capture_crnn_demo() -> list[Path]:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from rgr.evaluate import predict_file
    from rgr.gui_demo import DemoWindow
    from rgr.train import load_trained_model

    app = QApplication.instance() or QApplication(sys.argv)
    win = DemoWindow()
    win.show()
    app.processEvents()

    paths: list[Path] = []
    p1 = OUT / "01_crnn_gui_start.png"
    win.grab().save(str(p1))
    paths.append(p1)

    ckpt = ROOT / "models" / "rgr_crnn" / "best_model.pt"
    model = load_trained_model(ckpt)
    win.model = model
    win.out.setPlainText(f"Модель загружена: {ckpt}")
    win.btn_predict.setEnabled(True)
    app.processEvents()

    # успешное распознавание
    ok_file = next((ROOT / "data" / "fsdd" / "recordings").glob("4_*.wav"))
    win.audio_path = ok_file
    win.file_label.setText(str(ok_file))
    result = predict_file(model, ok_file)
    lines = [
        f"Файл: {ok_file.name}",
        f"Распознанная цифра (текст): {result['text']}",
        f"Уверенность: {result['confidence']:.2%}",
        "",
        "Распределение вероятностей:",
    ]
    for k, v in sorted(result["probs"].items(), key=lambda kv: -kv[1])[:5]:
        lines.append(f"  {k}: {v:.2%}")
    win.out.setPlainText("\n".join(lines))
    app.processEvents()
    p2 = OUT / "02_crnn_success.png"
    win.grab().save(str(p2))
    paths.append(p2)

    # ещё один пример
    ok2 = next((ROOT / "data" / "fsdd" / "recordings").glob("7_george_*.wav"), None)
    if ok2 is None:
        ok2 = next((ROOT / "data" / "fsdd" / "recordings").glob("7_*.wav"))
    result2 = predict_file(model, ok2)
    win.audio_path = ok2
    win.file_label.setText(str(ok2))
    win.out.setPlainText(
        f"Файл: {ok2.name}\n"
        f"Распознанная цифра (текст): {result2['text']}\n"
        f"Уверенность: {result2['confidence']:.2%}\n\n"
        + "\n".join(
            f"  {k}: {v:.2%}"
            for k, v in sorted(result2["probs"].items(), key=lambda kv: -kv[1])[:5]
        )
    )
    app.processEvents()
    p3 = OUT / "03_crnn_second_example.png"
    win.grab().save(str(p3))
    paths.append(p3)

    win.close()
    return paths


def capture_main_transcription() -> list[Path]:
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.setWindowTitle("Система автоматической транскрибации аудиоконтента (ВКР/РГР)")
    win.resize(1100, 720)
    win.show()
    app.processEvents()

    paths: list[Path] = []
    p1 = OUT / "04_transcription_gui_main.png"
    win.grab().save(str(p1))
    paths.append(p1)

    if hasattr(win, "text_raw"):
        win.text_raw.setPlainText(
            "Пример результата транскрибации (демо для отчёта РГР):\n\n"
            "Добрый день, начинаем совещание. Сегодня обсудим план работ на неделю."
        )
    if hasattr(win, "text_summary"):
        win.text_summary.setPlainText(
            "Краткое содержание: участники обсудили план работ на неделю."
        )
    if hasattr(win, "text_timestamps"):
        win.text_timestamps.setPlainText(
            "[00:00:01 – 00:00:05] Спикер 1: Добрый день, начинаем совещание.\n"
            "[00:00:05 – 00:00:12] Спикер 2: Сегодня обсудим план работ на неделю."
        )
    if hasattr(win, "text_log"):
        win.text_log.setPlainText(
            "[info] Модель: Whisper large-v3\n"
            "[info] Язык: ru\n"
            "[ok] Транскрибация завершена (демо-скриншот для РГР)"
        )
    if hasattr(win, "result_badge"):
        win.result_badge.setText("Готово (демо)")

    app.processEvents()
    p2 = OUT / "05_transcription_gui_result.png"
    win.grab().save(str(p2))
    paths.append(p2)

    # вкладка с временными метками, если есть tab widget
    tab = getattr(win, "tabs", None) or getattr(win, "result_tabs", None)
    if tab is not None and hasattr(tab, "setCurrentIndex"):
        try:
            tab.setCurrentIndex(2)
            app.processEvents()
            p3 = OUT / "06_transcription_gui_timestamps.png"
            win.grab().save(str(p3))
            paths.append(p3)
        except Exception:
            pass

    win.close()
    return paths


def capture_plots_collage_note() -> None:
    """Копия ключевых графиков рядом со скриншотами для удобства."""
    import shutil

    for name in ("loss_curve.png", "accuracy_curve.png", "confusion_matrix.png"):
        src = ROOT / "output" / "rgr" / name
        if src.exists():
            shutil.copy2(src, OUT / f"plot_{name}")


def main() -> int:
    print("Съёмка GUI CRNN...", flush=True)
    crnn = capture_crnn_demo()
    print("Съёмка GUI транскрибации...", flush=True)
    main_gui = capture_main_transcription()
    capture_plots_collage_note()
    all_paths = crnn + main_gui
    for p in all_paths:
        print(f"  saved {p} ({p.stat().st_size} bytes)", flush=True)
    print(f"Всего скриншотов: {len(all_paths)} → {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
