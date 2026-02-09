#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

cd "${REPO_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but was not found on PATH." >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  log "Creating local Python virtual environment at .venv"
  python3 -m venv "${VENV_DIR}"
else
  log "Using existing local Python virtual environment at .venv"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

log "Installing Python dependencies (pandas, numpy)"
python -m pip install --disable-pip-version-check --upgrade pip
python -m pip install --disable-pip-version-check --upgrade pandas numpy

PIPELINE_STEPS=(
  "data_design/generate_synthetic_data.py"
  "forecasting/forecasting_pipeline.py"
  "decision_policy/pricing_rules.py"
  "simulation_engine/scenario_runner.py"
  "evaluation_metrics/scorecards.py"
)

for step in "${PIPELINE_STEPS[@]}"; do
  log "Running ${step}"
  python "${step}"
done

log "Backend analytics pipeline completed successfully"
