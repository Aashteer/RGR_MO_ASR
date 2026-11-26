# Полный цикл подготовки материалов РГР (блок 4, вариант 53)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "== Установка зависимостей РГР ==" -ForegroundColor Cyan
python -m pip install -r requirements-rgr.txt

Write-Host "== Эксперимент: датасет, обучение, метрики ==" -ForegroundColor Cyan
$env:PYTHONUNBUFFERED = "1"
python rgr/run_experiment.py --epochs 15 --batch-size 64 --device cpu

Write-Host "== Сборка пояснительной записки DOCX ==" -ForegroundColor Cyan
python scripts/build_rgr_report.py

Write-Host ""
Write-Host "Готово." -ForegroundColor Green
Write-Host "Отчёт:      РГР_Леонтьев_Вариант53.docx"
Write-Host "Метрики:    output\rgr\"
Write-Host "Модель:     models\rgr_crnn\best_model.pt"
Write-Host "GUI CRNN:   python rgr\gui_demo.py"
Write-Host "Транскрибация ВКР: python main.py"
