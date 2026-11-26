#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "output" / "rgr" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    import matplotlib.pyplot as plt
    from PySide6.QtWidgets import QApplication

    from rgr.evaluate import predict_file
    from rgr.gui_demo import DemoWindow
    from rgr.train import load_trained_model

    app = QApplication.instance() or QApplication(sys.argv)
    win = DemoWindow()
    win.show()
    app.processEvents()

    model = load_trained_model()
    win.model = model
    err = ROOT / "data" / "fsdd" / "recordings" / "3_lucas_9.wav"
    r = predict_file(model, err)
    win.audio_path = err
    win.file_label.setText(str(err))
    win.out.setPlainText(
        f"Файл: {err.name}\n"
        f"Истинный класс: 3\n"
        f"Предсказание модели: {r['text']}\n"
        f"Уверенность: {r['confidence']:.2%}\n\n"
        "(пример характерной ошибки для анализа в отчёте)"
    )
    app.processEvents()
    p = OUT / "07_crnn_error_example.png"
    win.grab().save(str(p))
    print("saved", p)
    win.close()

    info = json.loads((ROOT / "output" / "rgr" / "dataset_info.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(7, 4))
    xs = list(range(10))
    ys = [info["per_class"][str(i)] for i in xs]
    ax.bar(xs, ys, color="#3b82f6")
    ax.set_xticks(xs)
    ax.set_xlabel("Класс (цифра)")
    ax.set_ylabel("Число записей")
    ax.set_title("Баланс классов датасета FSDD (3000 файлов)")
    ax.set_ylim(0, max(ys) * 1.25)
    for x, y in zip(xs, ys):
        ax.text(x, y + 5, str(y), ha="center")
    fig.tight_layout()
    out_bal = ROOT / "output" / "rgr" / "class_balance.png"
    fig.savefig(out_bal, dpi=150)
    plt.close(fig)
    print("saved", out_bal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
