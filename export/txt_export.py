"""Экспорт результатов (TXT, DOCX, PDF)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from llm.sanitize import is_valid_russian_llm_output, pick_best_text, strip_llm_artifacts


@dataclass
class ExportData:
    title: str
    raw_transcription: str
    formatted_transcription: str
    summary: str
    source_file: str
    language: str = ""
    duration_sec: float = 0.0
    segments: list[dict] | None = None


def _best_transcription(data: ExportData) -> str:
    """Возвращает лучший доступный текст транскрипции."""
    return pick_best_text(data.raw_transcription, data.formatted_transcription)


def _best_summary(data: ExportData) -> str:
    summary = strip_llm_artifacts(data.summary or "")
    if summary and is_valid_russian_llm_output(summary):
        return summary
    return "—"


def export_txt(data: ExportData, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    content = _build_document(data)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def export_docx(data: ExportData, output_path: str | Path) -> Path:
    from docx import Document
    from docx.shared import Pt

    output_path = Path(output_path)
    doc = Document()
    doc.add_heading(data.title, 0)
    doc.add_paragraph(f"Источник: {data.source_file}")
    doc.add_paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if data.language:
        doc.add_paragraph(f"Язык: {data.language}")

    doc.add_heading("Краткое содержание", level=1)
    doc.add_paragraph(_best_summary(data))

    doc.add_heading("Транскрипция", level=1)
    body = _best_transcription(data)
    for para in body.split("\n\n"):
        if para.strip():
            p = doc.add_paragraph(para)
            for run in p.runs:
                run.font.size = Pt(11)

    doc.save(str(output_path))
    return output_path


def export_pdf(data: ExportData, output_path: str | Path) -> Path:
    from fpdf import FPDF

    output_path = Path(output_path)
    font_path, font_name = _resolve_pdf_font()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font(font_name, "", str(font_path))
    pdf.set_font(font_name, size=11)

    pdf.set_font(font_name, size=16)
    pdf.cell(0, 10, data.title, ln=True)
    pdf.set_font(font_name, size=10)
    pdf.cell(0, 8, f"Источник: {data.source_file}", ln=True)
    pdf.ln(5)

    pdf.set_font(font_name, size=13)
    pdf.cell(0, 8, "Краткое содержание", ln=True)
    pdf.set_font(font_name, size=11)
    pdf.multi_cell(0, 6, _best_summary(data))
    pdf.ln(5)

    pdf.set_font(font_name, size=13)
    pdf.cell(0, 8, "Транскрипция", ln=True)
    pdf.set_font(font_name, size=11)
    pdf.multi_cell(0, 6, _best_transcription(data))

    pdf.output(str(output_path))
    return output_path


def _build_document(data: ExportData) -> str:
    lines = [
        data.title,
        "=" * len(data.title),
        f"Источник: {data.source_file}",
        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    ]
    if data.language:
        lines.append(f"Язык: {data.language}")
    if data.duration_sec:
        lines.append(f"Длительность: {data.duration_sec:.1f} с")
    lines.extend(["", "КРАТКОЕ СОДЕРЖАНИЕ", "-" * 20, _best_summary(data), "", "ТРАНСКРИПЦИЯ", "-" * 20])
    lines.append(_best_transcription(data))
    if data.segments:
        lines.extend(["", "ВРЕМЕННЫЕ МЕТКИ", "-" * 20])
        for seg in data.segments:
            start = _fmt_time(seg.get("start", 0))
            end = _fmt_time(seg.get("end", 0))
            speaker = f" [{seg['speaker']}]" if seg.get("speaker") else ""
            lines.append(f"[{start} → {end}]{speaker} {seg.get('text', '')}")
    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _resolve_pdf_font() -> tuple[Path, str]:
    """Шрифт с кириллицей для PDF (Windows / проект / fpdf)."""
    import os
    import fpdf

    win = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates: list[tuple[Path, str]] = [
        (win / "Fonts" / "arial.ttf", "Arial"),
        (win / "Fonts" / "segoeui.ttf", "Segoe"),
        (win / "Fonts" / "calibri.ttf", "Calibri"),
        (Path(fpdf.__file__).parent / "font" / "DejaVuSans.ttf", "DejaVu"),
        (Path(__file__).resolve().parent.parent / "assets" / "DejaVuSans.ttf", "DejaVu"),
    ]
    for path, name in candidates:
        if path.exists():
            return path, name
    raise FileNotFoundError(
        "Не найден шрифт с кириллицей для PDF (Arial/Segoe/DejaVu)."
    )
