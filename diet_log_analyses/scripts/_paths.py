"""Make the shared helpers in 2-analysis_python (config.py, weeklong_16s.py, weeklong_food.py) importable.

Use `import _paths` at the top of a script in diet_log_analyses/scripts/ before importing those modules.
"""

import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]  # gen2-longit/ (this file: diet_log_analyses/scripts/)
ANALYSIS_DIR = REPO_DIR / "2-analysis_python"
DIET_DIR = REPO_DIR / "diet_log_analyses"
FIG_DIR = DIET_DIR / "figures"
DIET_CODING = DIET_DIR / "daily_diet_coding.xlsx"

if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))
