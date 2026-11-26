"""Базовый процессор Qwen3-14B-Q4_K_M через llama-cpp-python (GGUF)."""

from __future__ import annotations

from pathlib import Path

from config.settings import LLMSettings, resolve_gpu_layers, settings
from llm.sanitize import strip_llm_artifacts

_IM_START = "<|" + "im_start" + "|>"
_IM_END = "<|" + "im_end" + "|>"


class QwenProcessor:
    def __init__(self, llm_settings: LLMSettings | None = None):
        self.cfg = llm_settings or settings.llm
        self._llm = None

    @property
    def is_available(self) -> bool:
        return Path(self.cfg.model_path).exists()

    def load_model(self) -> None:
        if self._llm is not None:
            return
        model_path = Path(self.cfg.model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Модель Qwen не найдена: {model_path}\n"
                "Скачайте GGUF: python scripts/download_models.py --qwen"
            )
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("llama-cpp-python не установлен") from exc

        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=self.cfg.n_ctx,
            n_gpu_layers=resolve_gpu_layers(self.cfg.n_gpu_layers),
            verbose=False,
        )

    def generate(self, system_prompt: str, user_prompt: str, fallback: str = "") -> str:
        if not self.is_available or not self.cfg.enabled:
            raise RuntimeError("LLM отключена или модель Qwen не найдена")

        self.load_model()
        assert self._llm is not None

        # /no_think — отключает блок рассуждений Qwen3
        user_body = user_prompt.rstrip() + " /no_think"
        prompt = (
            f"{_IM_START}system\n{system_prompt}{_IM_END}\n"
            f"{_IM_START}user\n{user_body}{_IM_END}\n"
            f"{_IM_START}assistant\n"
        )
        out = self._llm(
            prompt,
            max_tokens=min(self.cfg.max_tokens, 2048),
            temperature=self.cfg.temperature,
            stop=[_IM_END, "<|endoftext|>"],
        )
        text = strip_llm_artifacts(out["choices"][0]["text"].strip())
        if not text:
            raise RuntimeError("LLM вернула пустой ответ")
        return text
