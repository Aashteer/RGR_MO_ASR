#!/usr/bin/env python3
"""Сборка пояснительной записки РГР (DOCX) по структуре блока 4 + скриншоты."""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "rgr"
SHOTS = OUT / "screenshots"
REPORT_PATH = ROOT / "РГР_Леонтьев_Вариант53.docx"


def set_run_font(run, size=12, bold=False, name="Times New Roman", italic=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = name
    r = run._element
    r.rPr.rFonts.set(qn("w:eastAsia"), name)


def add_para(doc: Document, text: str, bold: bool = False, first_indent: bool = True) -> None:
    p = doc.add_paragraph()
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    run = p.add_run(text)
    set_run_font(run, bold=bold)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    for run in p.runs:
        set_run_font(run)


def add_code(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    set_run_font(run, size=9, name="Consolas")


def try_pic(doc: Document, path: Path, width_cm: float = 15.0, caption: str = "") -> None:
    if not path.exists():
        add_para(doc, f"[Рисунок отсутствует: {path.name}]", first_indent=False)
        return
    doc.add_picture(str(path), width=Cm(width_cm))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            set_run_font(run, size=11, italic=True)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def snippet(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    chunk = lines[start - 1 : end]
    return "\n".join(chunk)


def build() -> Path:
    metrics = load_json(OUT / "metrics.json")
    summary = load_json(OUT / "summary.json")
    manifest = load_json(OUT / "dataset_manifest.json")
    ds_info = load_json(OUT / "dataset_info.json")
    train_meta = load_json(ROOT / "models" / "rgr_crnn" / "train_meta.json")
    m = metrics.get("metrics", {})
    acc, f1, prec, rec = (
        m.get("accuracy"),
        m.get("f1_macro"),
        m.get("precision_macro"),
        m.get("recall_macro"),
    )

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)

    for line in [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РФ",
        "ФГБОУ ВО «НОВОСИБИРСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ»",
        "Кафедра автоматизированных систем управления",
    ]:
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            set_run_font(run, size=12)

    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run(
        "РАСЧЁТНО-ГРАФИЧЕСКАЯ РАБОТА\n"
        "по дисциплине «Технологии AI и ML»\n\n"
        "Блок 4. Распознавание и классификация звуковых сигналов\n"
        "Вариант 53. Собственная тема:\n"
        "«Автоматическое распознавание речи и транскрибация аудиоконтента\n"
        "на основе нейросетевых моделей»"
    )
    set_run_font(r, size=14, bold=True)

    doc.add_paragraph()
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    ir = info.add_run("Выполнил: Леонтьев А.В.\nГруппа: АВТ-314\nНовосибирск 2026")
    set_run_font(ir)

    doc.add_page_break()

    # ---------- 1 ----------
    doc.add_heading("1. Введение", level=1)
    add_para(
        doc,
        "Целью работы является практическое освоение методов обработки звуковых сигналов "
        "и машинного обучения применительно к задаче автоматического распознавания речи "
        "(Automatic Speech Recognition, ASR) и транскрибации аудиоконтента.",
    )
    add_para(doc, "Задачи работы:")
    add_bullet(doc, "использовать готовый датасет аудиозаписей;")
    add_bullet(doc, "выполнить предобработку: mel/MFCC, нормализация, аугментация;")
    add_bullet(doc, "обучить нейросеть архитектуры CRNN;")
    add_bullet(doc, "оценить качество на тесте (Accuracy, Precision, Recall, F1-Score);")
    add_bullet(doc, "разработать GUI для демонстрации обученной модели;")
    add_bullet(
        doc,
        "представить практическое применение ASR в системе транскрибации (ВКР) на базе Whisper.",
    )

    # ---------- 2 ----------
    doc.add_heading("2. Описание задачи и постановка эксперимента", level=1)
    doc.add_heading("2.1. Выбор и описание датасета", level=2)
    add_para(
        doc,
        "Для контролируемого эксперимента обучения модели «с нуля» выбран датасет "
        "Free Spoken Digit Dataset (FSDD, GitHub: Jakobovski). Задача: распознать "
        "произнесённую цифру 0–9 и выдать её текстовый класс — базовый сценарий ASR "
        "на ограниченном словаре (соответствует требованиям блока 4; близко к варианту 46, "
        "оформлено как собственная тема варианта 53 в связке с системой транскрибации).",
    )
    if ds_info:
        add_para(
            doc,
            f"Характеристики датасета: {ds_info.get('n_files')} записей WAV, "
            f"{ds_info.get('n_speakers')} дикторов ({', '.join(ds_info.get('speakers', []))}), "
            f"классы 0–9 полностью сбалансированы по {ds_info['per_class'].get('0')} файлов на класс. "
            f"Суммарная длительность ≈ {ds_info.get('duration_sec_total')} с "
            f"(средняя длительность записи {ds_info.get('duration_sec_mean')} с, "
            f"диапазон {ds_info.get('duration_sec_min')}–{ds_info.get('duration_sec_max')} с).",
        )
    if manifest:
        tr, va, te = manifest.get("train", {}), manifest.get("val", {}), manifest.get("test", {})
        add_para(
            doc,
            f"Разделение стратифицировано по парам (диктор, класс): "
            f"train={tr.get('n_files')}, val={va.get('n_files')}, test={te.get('n_files')} "
            f"(≈70/15/15).",
        )
    try_pic(doc, OUT / "class_balance.png", caption="Рисунок 1 — Баланс классов датасета FSDD")

    doc.add_heading("2.2. Предобработка данных", level=2)
    add_para(
        doc,
        "Аудио приводится к 16 кГц, моно, нормализуется по пиковой амплитуде. "
        "Извлекается mel-спектрограмма (n_mels=64, n_fft=1024, hop_length=256), "
        "шкала дБ, фиксированная длина 80 кадров по времени, стандартизация признаков. "
        "Дополнительно реализовано извлечение MFCC (n_mfcc=40).",
    )
    add_para(doc, "Аугментация обучающей выборки:")
    add_bullet(doc, "гауссовский шум (SNR ≈ 18–30 дБ);")
    add_bullet(doc, "случайный временной сдвиг;")
    add_bullet(doc, "изменение темпа;")
    add_bullet(doc, "pitch shift (реализован в модуле аугментации).")
    mels = sorted(OUT.glob("mel_*.png"))
    if mels:
        try_pic(doc, mels[0], caption="Рисунок 2 — Пример mel-спектрограммы")

    doc.add_heading("2.3. Выбор архитектуры модели", level=2)
    add_para(
        doc,
        "Выбрана CRNN: стек CNN извлекает локальные спектрально-временные признаки, "
        "двунаправленный GRU моделирует последовательность кадров, attention-pooling "
        "агрегирует контекст, полносвязный слой классифицирует 10 цифр. "
        "Архитектура типична для keyword spotting / классификации звука и обучается на CPU.",
    )
    add_para(
        doc,
        "Для полной транскрибации произвольной речи в программном комплексе используется "
        "предобученный Transformer Whisper (faster-whisper) с GUI, диаризацией и экспортом.",
    )

    # ---------- 3 ----------
    doc.add_heading("3. Процесс обучения", level=1)
    add_para(
        doc,
        "Функция потерь — CrossEntropyLoss (label smoothing 0.05); оптимизатор — AdamW; "
        "планировщик — CosineAnnealingLR.",
    )
    if train_meta:
        add_para(
            doc,
            f"Гиперпараметры: epochs={train_meta.get('epochs')}, "
            f"batch_size={train_meta.get('batch_size')}, lr={train_meta.get('lr')}, "
            f"weight_decay={train_meta.get('weight_decay')}, device={train_meta.get('device')}, "
            f"параметров модели={train_meta.get('params')}. "
            f"Train/val: {train_meta.get('train_size')}/{train_meta.get('val_size')}, "
            f"время обучения ≈ {train_meta.get('seconds')} с.",
        )
    try_pic(doc, OUT / "loss_curve.png", caption="Рисунок 3 — Динамика функции потерь (train/val)")
    try_pic(doc, OUT / "accuracy_curve.png", caption="Рисунок 4 — Динамика точности (train/val)")

    # ---------- 4 ----------
    doc.add_heading("4. Интерпретация результатов", level=1)
    if acc is not None:
        add_para(
            doc,
            f"На тестовой выборке ({metrics.get('n_test')} файлов): "
            f"Accuracy={acc:.4f} ({acc:.2%}), Precision(macro)={prec:.4f}, "
            f"Recall(macro)={rec:.4f}, F1-Score(macro)={f1:.4f}.",
        )
    try_pic(doc, OUT / "confusion_matrix.png", caption="Рисунок 5 — Матрица ошибок на тесте")
    report_txt = OUT / "classification_report.txt"
    if report_txt.exists():
        add_para(doc, "Отчёт classification_report:", bold=True, first_indent=False)
        add_code(doc, report_txt.read_text(encoding="utf-8"))

    doc.add_heading("4.1. Анализ успехов и ошибок", level=2)
    add_para(
        doc,
        "Успешные случаи: чёткие короткие произнесения распознаются с уверенностью >95% "
        "(см. скриншоты GUI). Ошибки редки (~0.8%) и связаны с акустической близостью "
        "отдельных цифр и особенностями дикторов.",
    )
    errors = metrics.get("errors", [])
    if errors:
        add_para(doc, "Примеры характерных ошибок:")
        for e in errors[:6]:
            add_bullet(
                doc,
                f"{e.get('file')}: истина {e.get('true')} → предсказано {e.get('pred')} "
                f"(диктор {e.get('speaker')})",
            )
    try_pic(
        doc,
        SHOTS / "02_crnn_success.png",
        width_cm=14,
        caption="Рисунок 6 — Успешное распознавание цифры «4» (уверенность 96.87%)",
    )
    try_pic(
        doc,
        SHOTS / "07_crnn_error_example.png",
        width_cm=14,
        caption="Рисунок 7 — Пример ошибки распознавания (анализ в GUI)",
    )

    # ---------- 5 ----------
    doc.add_heading("5. Тестирование и демонстрация программного обеспечения", level=1)
    add_para(
        doc,
        "Разработаны два GUI-приложения. Первое демонстрирует обученную CRNN-модель "
        "на тестовых WAV. Второе — система транскрибации аудиоконтента (ВКР): Whisper ASR, "
        "настройки, вкладки результата и экспорт.",
    )
    add_para(doc, "Запуск демо CRNN: python rgr/gui_demo.py", first_indent=False)
    add_para(doc, "Запуск системы транскрибации: python main.py", first_indent=False)

    try_pic(
        doc,
        SHOTS / "01_crnn_gui_start.png",
        width_cm=14,
        caption="Рисунок 8 — GUI демонстрации CRNN (стартовый экран)",
    )
    try_pic(
        doc,
        SHOTS / "03_crnn_second_example.png",
        width_cm=14,
        caption="Рисунок 9 — Повторная проверка на другом тестовом файле",
    )
    try_pic(
        doc,
        SHOTS / "04_transcription_gui_main.png",
        width_cm=15,
        caption="Рисунок 10 — Главное окно системы транскрибации",
    )
    try_pic(
        doc,
        SHOTS / "05_transcription_gui_result.png",
        width_cm=15,
        caption="Рисунок 11 — Вкладка «Транскрипция» с результатом",
    )
    try_pic(
        doc,
        SHOTS / "06_transcription_gui_timestamps.png",
        width_cm=15,
        caption="Рисунок 12 — Вкладка «С метками времени»",
    )

    add_para(
        doc,
        "Тестирование подтвердило: загрузку модели и аудио, корректный вывод класса и "
        "вероятностей, работу интерфейса транскрибации (выбор модели Whisper, языка, "
        "опций диаризации/LLM, вкладок результата и экспорта).",
    )

    # ---------- 6 ----------
    doc.add_heading("6. Заключение", level=1)
    add_para(
        doc,
        "Выполнен полный цикл блока 4: датасет → предобработка/аугментация → обучение CRNN → "
        "метрики и матрица ошибок → GUI-демонстрация. "
        + (
            f"Достигнуты Accuracy={acc:.2%} и F1-macro={f1:.2%} на тесте FSDD. "
            if acc is not None
            else ""
        )
        + "Рекомендации: CRNN — для ограниченного словаря и встраиваемых сценариев; "
        "Whisper — для непрерывной транскрибации речи с локальной обработкой данных.",
    )

    # ---------- checklist ----------
    doc.add_heading("Соответствие требованиям блока 4", level=1)
    checks = [
        "1. Датасет аудиозаписей — FSDD, 3000 WAV, 10 классов, 6 дикторов.",
        "2. Предобработка — mel/MFCC, нормализация, аугментация (шум, сдвиг, темп, pitch).",
        "3. Обучение нейросети — CRNN (CNN + BiGRU + attention), PyTorch.",
        "4. Оценка на тесте — Accuracy/Precision/Recall/F1, матрица ошибок, графики обучения.",
        "5. GUI — rgr/gui_demo.py (обученная модель) и main.py (система транскрибации).",
        "6. Отчёт — введение, эксперимент, обучение, результаты, демо, заключение, приложения.",
    ]
    for c in checks:
        add_bullet(doc, c)

    # ---------- 7 code ----------
    doc.add_heading("7. Приложения (фрагменты кода)", level=1)
    doc.add_heading("Приложение А. Извлечение mel-спектрограммы", level=2)
    add_code(doc, snippet(ROOT / "rgr" / "features.py", 34, 53))

    doc.add_heading("Приложение Б. Аугментация", level=2)
    add_code(doc, snippet(ROOT / "rgr" / "augment.py", 48, 62))

    doc.add_heading("Приложение В. Архитектура CRNN", level=2)
    add_code(doc, snippet(ROOT / "rgr" / "model.py", 13, 63))

    doc.add_heading("Приложение Г. Фрагмент цикла обучения", level=2)
    add_code(doc, snippet(ROOT / "rgr" / "train.py", 110, 145))

    doc.add_heading("Приложение Д. Структура проекта", level=2)
    add_bullet(doc, "rgr/features.py, augment.py, dataset.py, model.py, train.py, evaluate.py")
    add_bullet(doc, "rgr/run_experiment.py — полный эксперимент")
    add_bullet(doc, "rgr/gui_demo.py — GUI обученной модели")
    add_bullet(doc, "main.py / pipeline.py — система транскрибации ВКР")
    add_bullet(doc, "output/rgr/ — метрики, графики, screenshots/")
    add_bullet(doc, "models/rgr_crnn/best_model.pt — чекпоинт")

    doc.add_heading("Список использованных источников", level=1)
    sources = [
        "Radford A. et al. Robust Speech Recognition via Large-Scale Weak Supervision. arXiv:2212.04356, 2022.",
        "Jakobovski. Free Spoken Digit Dataset (FSDD). GitHub.",
        "Choi K. et al. Convolutional Recurrent Neural Networks for Music Classification // ICASSP, 2017.",
        "Bredin H. et al. pyannote.audio // ICASSP, 2020.",
        "SYSTRAN. faster-whisper (CTranslate2).",
        "McFee B. et al. librosa: Audio and Music Signal Analysis in Python.",
    ]
    for i, s in enumerate(sources, 1):
        p = doc.add_paragraph(f"{i}. {s}")
        for run in p.runs:
            set_run_font(run, size=12)

    doc.save(str(REPORT_PATH))
    print(f"Отчёт сохранён: {REPORT_PATH}")
    return REPORT_PATH


if __name__ == "__main__":
    build()
