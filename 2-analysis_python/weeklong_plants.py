"""Plants longitudinal study: Python translation of 2-analysis/20250402_Weeklong_Plants.Rmd.

Usage (from the repository root):
    python 2-analysis_python/weeklong_plants.py                    # run everything
    python 2-analysis_python/weeklong_plants.py --sections heatmap
    python 2-analysis_python/weeklong_plants.py --list

The chunks are shared with the meat notebook and live in weeklong_food.py.
"""

import weeklong_food as F

if __name__ == "__main__":
    F.main(F.PLANTS, __doc__)
