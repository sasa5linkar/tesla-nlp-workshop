#!/usr/bin/env sh
set -eu
cd -- "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo 'Install uv: https://docs.astral.sh/uv/getting-started/installation/' >&2
  exit 1
fi
export GRADIO_ANALYTICS_ENABLED=False HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
uv sync --locked
printf '%s\n' 'Otvorite http://127.0.0.1:7860 u pregledacu. Za kraj: Ctrl+C.'
exec uv run --locked --no-sync python -m workshop
