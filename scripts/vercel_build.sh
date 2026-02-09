#!/usr/bin/env bash
set -euo pipefail

echo "==========================================="
echo "  VERCEL BUILD PREPARATION"
echo "==========================================="

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# 1. Setup Python Environment
if command -v python3 &> /dev/null; then
  echo "Using system python3: $(python3 --version)"
else
  echo "Error: python3 not found."
  exit 1
fi

# Install dependencies into a local venv or just user install if on Vercel
# On Vercel, we can try to install to the user space or use a venv. 
# Simpler: install to current environment since it's ephemeral/containerized.
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pandas numpy

# 2. Run Simulation Pipeline
echo "Running analytics pipeline..."
# We reuse the logic from run_pipeline.sh but bypass the venv check if needed, 
# or just run the python scripts directly since we just installed deps.

PYTHON_COMMAND="python3"

# Steps from run_pipeline.sh
PIPELINE_STEPS=(
  "data_design/generate_synthetic_data.py"
  "forecasting/forecasting_pipeline.py"
  "decision_policy/pricing_rules.py"
  "simulation_engine/scenario_runner.py"
  "evaluation_metrics/scorecards.py"
)

for step in "${PIPELINE_STEPS[@]}"; do
  echo "Running ${step}..."
  $PYTHON_COMMAND "${step}"
done

# 3. Move Artifacts to Public
echo "Preparing artifacts for build..."
mkdir -p public/data

# Defined outputs
echo "Copying artifacts..."
cp simulation_engine/output/scenario_outcomes.csv public/data/
cp evaluation_metrics/output/strategy_scorecard.csv public/data/

echo "==========================================="
echo "  BUILD PREPARATION COMPLETE"
echo "==========================================="
