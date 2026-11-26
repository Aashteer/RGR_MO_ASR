# Система автоматической транскрибации аудиоконтента

Программный комплекс по ВКР «Разработка ПО для транскрибации аудиоконтента».

## Архитектура (модульная)

| Модуль | Технология | Назначение |
|--------|-----------|------------|
| ASR | **faster-whisper** (Whisper large-v3, CTranslate2) | Речь → текст |
| Диаризация | **pyannote.audio** 3.1 | Разделение дикторов |
| LLM | **Qwen3-14B-Q4_K_M** (GGUF, llama-cpp) | Постобработка, суммаризация |
| GUI | **PySide6** (Qt) | Графический интерфейс |
| Аудио | **FFmpeg** + librosa | Конвертация, нормализация |

## Структура проекта

```
вкр/
├── main.py                 # Запуск GUI
├── pipeline.py             # Конвейер обработки
├── config/settings.py      # Настройки моделей
├── audio/                  # Загрузка, FFmpeg, предобработка
├── speech/                 # Whisper, pyannote, merge
├── llm/                    # Qwen постобработка
├── export/                 # TXT, DOCX, PDF
├── ui/                     # PySide6 интерфейс
├── training/               # Дообучение Whisper
├── scripts/                # CLI, загрузка моделей, оценка
└── models/                 # Локальные модели
```

## Установка

### 1. Python 3.10+

```powershell
cd h:\вкр
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. FFmpeg

Скачайте с https://ffmpeg.org и добавьте в PATH.

### 3. CUDA (опционально, для GPU)

Установите CUDA-совместимый PyTorch: https://pytorch.org

Для llama-cpp с GPU:
```powershell
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

### 4. Hugging Face токен (для pyannote)

1. Регистрация: https://huggingface.co
2. Примите условия: https://huggingface.co/pyannote/speaker-diarization-3.1
3. Создайте токен и задайте:
```powershell
$env:HF_TOKEN = "hf_ваш_токен"
```

### 5. Загрузка моделей

```powershell
# Whisper (скачается при первом запуске, или явно):
python scripts/download_models.py --whisper --model large-v3

# Qwen3 (~8.5 ГБ):
python scripts/download_models.py --qwen
```

## Запуск

### Графический интерфейс

```powershell
python main.py
```

### Командная строка

```powershell
python scripts/transcribe_cli.py "путь\к\аудио.mp3" -o результат.txt
python scripts/transcribe_cli.py audio.wav --model medium --no-llm
```

## Обучение моделей

### Fine-tuning Whisper на своих данных

Подготовьте датасет:
```
data/train/
  audio/
    rec001.wav
    rec002.wav
  transcripts.csv
```

`transcripts.csv`:
```csv
file,text
rec001.wav,Текст первой записи
rec002.wav,Текст второй записи
```

Запуск обучения:
```powershell
pip install transformers datasets accelerate
python training/train_whisper.py --data data/train --model openai/whisper-small --epochs 5
```

После обучения конвертируйте в CTranslate2 для faster-whisper:
```powershell
pip install ctranslate2
ct2-transformers-converter --model models/whisper_finetuned --output_dir models/whisper_finetuned_ct2
```

Укажите путь в `config/settings.py`:
```python
whisper.model_size = "models/whisper_finetuned_ct2"
```

### Оценка качества (WER/CER)

```powershell
python scripts/evaluate.py --data data/test --model large-v3
```

## Нейросетевые модели в проекте

| Модель | Архитектура | Параметры | Обучение |
|--------|-------------|-----------|----------|
| Whisper large-v3 | Encoder-Decoder Transformer | ~1.5B | Предобучена OpenAI; fine-tune через `train_whisper.py` |
| pyannote 3.1 | CNN + RNN + clustering | — | Предобучена; HF token для загрузки |
| Qwen3-14B-Q4_K_M | Transformer LLM, 4-bit | 14B (Q4) | Предобучена; inference через GGUF |

## Минимальные требования

| Компонент | CPU | GPU (рекомендуется) |
|-----------|-----|---------------------|
| Whisper large-v3 | 8+ ГБ RAM, медленно | 6+ ГБ VRAM |
| pyannote | 4+ ГБ RAM | CUDA |
| Qwen3-14B Q4 | 16+ ГБ RAM | 8+ ГБ VRAM |

Для слабых ПК используйте `medium` или `small` в настройках Whisper и отключите LLM.

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `HF_TOKEN` | Токен Hugging Face для pyannote |
| `CUDA_VISIBLE_DEVICES` | Выбор GPU |
