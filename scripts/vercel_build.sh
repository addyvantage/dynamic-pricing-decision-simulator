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

# Create a temporary virtual environment to avoid PEP 668 errors (externally managed environment)
# This is safe because Vercel builds are ephemeral.
echo "Creating virtual environment..."
python3 -m venv .vercel_venv

# Activate venv
source .vercel_venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install pandas numpy

# 2. Run Simulation Pipeline
echo "Running analytics pipeline..."

PYTHON_COMMAND="python" # Uses the venv python

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
echo "  Artifacts in public/data:"
ls -la public/data
echo "==========================================="
