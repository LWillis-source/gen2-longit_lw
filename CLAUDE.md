# gen2-longit

Keep this file to durable, repository-wide rules. No counts, results or status here.

Analyses of the Gen2 CapScan longitudinal studies (LONGIT-weeklong, LONGIT-couple): the original R notebooks and their Python translations. Be factual; base statements on verified facts.

## Layout
- `0-config.R`, `2-analysis/*.Rmd`, `3-figures/` — original R analyses and their figures. Reference only: do not edit. `3-figures/` contains stale files from older R runs, so a file there is not proof the current code produces it.
- `2-analysis_python/` — Python translations and shared modules: `config.py` (Python counterpart of `0-config.R`: data loading, phyloseq-like `PS` object, distances, PCoA, plotting helpers), `weeklong_16s.py`, `weeklong_food.py` (with `weeklong_meat.py`, `weeklong_plants.py`). Outputs go to `3-figures_python/`; regenerate with `bash run_all_analyses.sh`.
- `diet_log_analyses/` — diet-log and food-sequencing analyses. **Before working there, read `diet_log_analyses/CLAUDE.md` (rules and workflow), `diet_log_analyses/PROGRESS.md` (status and decisions) and `diet_log_analyses/BEST_PRACTICES_CLAUDE.md`.**
- `1-data/` — input data (DADA2 outputs, sample-info sheets, colour sheets).

## Rules
- All data sources are read-only: `1-data/`, the sample sheet in the sibling repository `gen2_capScan_sanitized00`, and the user's workbooks. Never edit, move or delete them.
- Use `/opt/anaconda3/bin/python`; run scripts from the repository root.
- Sample metadata: `gen2_capScan_sanitized00/data/work-in-progress-meta/LONGITWeeklong-samplesheet-FINAL.xlsx` (path in `config.SAMPLE_SHEET`), loaded only through `weeklong_16s.read_sample_sheet()`, which joins its Sample_ID and Kit_ID sheets.
- Read Excel with `config.read_excel_like_readxl()`, never plain `pd.read_excel`: pandas turns text `"01"` into 1 and `"NA"` into NaN, and both are meaningful in these workbooks.
- phyloseq orders taxa by the tree's tip order, so `OTU` names (`feature_%04d`) differ from the `Feature` column of `feature_data.txt`.
- Changes to the Python translations (when the user allows them) are checked against the R originals; R with phyloseq, Hmisc and compositions is installed (user library `~/Library/R/arm64/4.6/library`) for such cross-checks.
- Ask before deleting anything; never use broad resets or deletions to undo a change.
- Claude may write only to `diet_log_analyses/scripts/`, `diet_log_analyses/figures/` and `diet_log_analyses/PROGRESS.md`, enforced by a hook and the Bash sandbox in `.claude/settings.json` (this folder and `diet_log_analyses/`). If a write is blocked, stop and tell the user; never work around it. Changes elsewhere (including `2-analysis_python/`) are made by the user or after the user lifts the restriction.
