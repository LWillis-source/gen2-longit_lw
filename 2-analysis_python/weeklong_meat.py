"""Meat longitudinal study: Python translation of 2-analysis/20250402_Weeklong_Meat.Rmd.

Usage (from the repository root):
    python 2-analysis_python/weeklong_meat.py                      # run everything
    python 2-analysis_python/weeklong_meat.py --sections heatmap
    python 2-analysis_python/weeklong_meat.py --list

The chunks are shared with the plants notebook and live in weeklong_food.py.
"""

import weeklong_food as F

if __name__ == "__main__":
    F.main(F.MEAT, __doc__)
