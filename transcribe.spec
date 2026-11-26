# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: Система автоматической транскрибации (ВКР)
# Сборка: scripts\build_exe.ps1

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

project_datas = []
for rel in ("config", "audio", "speech", "llm", "export", "ui"):
    src = ROOT / rel
    if src.is_dir():
        project_datas.append((str(src), rel))

ffmpeg_dir = ROOT / "tools" / "ffmpeg"
if ffmpeg_dir.exists():
    project_datas.append((str(ffmpeg_dir), "tools/ffmpeg"))

hiddenimports = [
    "pipeline",
    "config.settings",
    "config.user_config",
    "audio.converter",
    "audio.file_loader",
    "audio.preprocessing",
    "audio.vocal_isolation",
    "speech.transcription",
    "speech.diarization",
    "speech.merge_segments",
    "speech.hallucination_filter",
    "speech.text_cleanup",
    "llm.qwen_processor",
    "llm.formatter",
    "llm.summarizer",
    "llm.sanitize",
    "export.txt_export",
    "ui.main_window",
    "ui.styles",
    "ui.widgets",
    "ui.dialogs",
    "faster_whisper",
    "faster_whisper.audio",
    "faster_whisper.feature_extractor",
    "faster_whisper.tokenizer",
    "faster_whisper.vad",
    "ctranslate2",
    "av",
    "docx",
    "fpdf",
    "huggingface_hub",
    "llama_cpp",
    "torch",
    "torchaudio",
    "librosa",
    "soundfile",
    "pyannote.audio",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=project_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "tkinter", "pytest", "IPython", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Transcription",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Transcription",
)
