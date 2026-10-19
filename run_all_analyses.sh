#!/usr/bin/env bash
# Regenerate the Python 16S, meat and plants analyses (figures in 3-figures_python/) from the repository root.
#   bash run_all_analyses.sh
# The diet-log and food-sequencing analyses in diet_log_analyses/ are not run from here.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python}

$PY 2-analysis_python/weeklong_16s.py
$PY 2-analysis_python/weeklong_meat.py
$PY 2-analysis_python/weeklong_plants.py
echo "done"
