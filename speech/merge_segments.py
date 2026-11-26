"""Объединение транскрипции и диаризации по временным меткам."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MergedSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speaker(
    seg_start: float,
    seg_end: float,
    speaker_segments: list[dict],
) -> str | None:
    """Назначает диктора сегменту по максимальному перекрытию по времени."""
    best_speaker = None
    best_overlap = 0.0
    for sp in speaker_segments:
        ov = _overlap(seg_start, seg_end, sp["start"], sp["end"])
        if ov > best_overlap:
            best_overlap = ov
            best_speaker = sp["speaker"]
    return best_speaker


def merge_transcription_and_diarization(
    transcription: list[dict],
    speaker_segments: list[dict] | None,
) -> list[MergedSegment]:
    merged: list[MergedSegment] = []
    for seg in transcription:
        speaker = None
        if speaker_segments:
            speaker = assign_speaker(seg["start"], seg["end"], speaker_segments)
        merged.append(
            MergedSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                speaker=speaker,
            )
        )
    return merged


def format_dialogue(segments: list[MergedSegment]) -> str:
    """Форматирует транскрипцию с метками дикторов."""
    lines: list[str] = []
    current_speaker = None
    buffer: list[str] = []

    def flush():
        nonlocal buffer, current_speaker
        if buffer:
            label = current_speaker or "Спикер"
            lines.append(f"[{label}]: {' '.join(buffer)}")
            buffer = []

    for seg in segments:
        if seg.speaker != current_speaker:
            flush()
            current_speaker = seg.speaker
        buffer.append(seg.text)
    flush()
    return "\n\n".join(lines)


def merged_to_dicts(segments: list[MergedSegment]) -> list[dict]:
    return [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "speaker": s.speaker,
        }
        for s in segments
    ]
