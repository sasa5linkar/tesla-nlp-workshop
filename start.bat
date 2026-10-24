@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo Potreban je uv. Uputstvo: https://docs.astral.sh/uv/getting-started/installation/
  pause
  exit /b 1
)
set GRADIO_ANALYTICS_ENABLED=False
set HF_HUB_DISABLE_TELEMETRY=1
set HF_HUB_DISABLE_IMPLICIT_TOKEN=1
echo Priprema okruzenja. Pri prvom pokretanju potreban je internet.
uv sync --locked
if errorlevel 1 (
  echo Instalacija nije uspela. Proverite internet i slobodan disk.
  pause
  exit /b 1
)
echo Otvorite http://127.0.0.1:7860 u pregledacu. Za kraj pritisnite Ctrl+C.
uv run --locked --no-sync python -m workshop
if errorlevel 1 pause
