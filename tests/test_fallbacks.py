from llm.qwen_processor import QwenProcessor


def test_qwen_processor_falls_back_without_model_file() -> None:
    processor = QwenProcessor()
    result = processor.generate("Ты редактор текста", "Отредактируй: Привет мир")

    assert isinstance(result, str)
    assert len(result.strip()) > 0
