"""Диаризация дикторов (pyannote.audio, раздел 4.4 ВКР)."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import DiarizationSettings, settings


@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker: str


class DiarizationEngine:
    def __init__(self, diar_settings: DiarizationSettings | None = None):
        self.cfg = diar_settings or settings.diarization
        self._pipeline = None

    def load_pipeline(self) -> None:
        if self._pipeline is not None:
            return
        if not self.cfg.hf_token:
            raise RuntimeError(
                "Для pyannote.audio нужен токен Hugging Face.\n"
                "1. Зарегистрируйтесь на https://huggingface.co\n"
                "2. Примите условия: https://huggingface.co/pyannote/speaker-diarization-3.1\n"
                "3. Создайте токен и задайте: set HF_TOKEN=ваш_токен"
            )
        from pyannote.audio import Pipeline
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self._pipeline = Pipeline.from_pretrained(
                self.cfg.pipeline_name,
                token=self.cfg.hf_token,
            )
        except TypeError:
            self._pipeline = Pipeline.from_pretrained(
                self.cfg.pipeline_name,
                use_auth_token=self.cfg.hf_token,
            )
        self._pipeline.to(device)

    def diarize(self, audio_path: str) -> list[SpeakerSegment]:
        self.load_pipeline()
        assert self._pipeline is not None

        kwargs = {}
        if self.cfg.min_speakers is not None:
            kwargs["min_speakers"] = self.cfg.min_speakers
        if self.cfg.max_speakers is not None:
            kwargs["max_speakers"] = self.cfg.max_speakers

        diarization = self._pipeline(audio_path, **kwargs)
        segments: list[SpeakerSegment] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(
                SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=str(speaker),
                )
            )
        segments.sort(key=lambda s: s.start)
        return segments

    def segments_to_dicts(self, segments: list[SpeakerSegment]) -> list[dict]:
        return [
            {"start": s.start, "end": s.end, "speaker": s.speaker}
            for s in segments
        ]
