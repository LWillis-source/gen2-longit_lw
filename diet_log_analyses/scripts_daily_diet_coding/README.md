# diet_log_analyses/scripts_daily_diet_coding

Scripts and inputs behind `diet_log_analyses/daily_diet_coding.xlsx`.

## What can and cannot be rebuilt

`build_workbook.py` reproduces the **first version** of the workbook (15 Oct 2026): tabs README,
daily_diet_coding, source_diet_text, ingredient_lexicon, needs_review. It writes to
`daily_diet_coding_rebuilt.xlsx` in this folder, never over the working file.

These later changes were made with one-off commands and are **not** scripted here:
species-column rank labels, needs_review taxonomy columns, lexicon Genus/Family/Order/Class,
collapse_groups and informative_changes tabs and the 17 Oct "Informative" re-check.
The workbook itself, and its README tab, are the record of those. A rebuild will therefore differ
from the current file.

## Files

| File | Role |
|---|---|
| `build_workbook.py` | Builds the first-version workbook from the inputs below |
| `informative.py` | Rules for "Informative for sequencing?" (imported by build_workbook.py; original rules, before the 17 Oct re-check) |
| `data/lexicon.tsv` | Ingredient, species, marker, note (hand-assigned, general taxonomy knowledge) |
| `data/coding_part1-3.txt` | Hand-coded diet entries: `## subject|date`, then `time|food|ingredients` |
| `data/d4fo02656j2_suppl.xlsx` | Petrone 2025 supplementary tables (Table S5 is used for the cross-check) |
| `add_fermented_fibrous_labels.py` | Adds Fermented? and Fibrous? + reasoning (cols X-AA) to the working workbook |
| `add_live_microbes_labels.py` | Adds Likely live microbes? + reasoning (cols AB-AC); run after the previous one |
| `verify_lexicon_taxonomy_gbif.py` | Checks Genus/Family/Order/Class against GBIF. Needs internet. Never run |
| `check_lexicon_species_consistency.py` | Read-only check that lexicon Species agrees with the Species column of daily_diet_coding (writes `lexicon_vs_diet_species_check.csv`, header only if no differences) |

Also read from the repo: `1-data/Weeklong-Redcap-export.xlsx` (Daily-Diet tab) and
`1-data/DADA2-weeklong-{plants,meat}/feature_data.txt`.

## Running

```
python build_workbook.py            # writes daily_diet_coding_rebuilt.xlsx here
python build_workbook.py out.xlsx   # or choose the output name
```

The `add_*` scripts edit `diet_log_analyses/daily_diet_coding.xlsx` in place and assert the
expected column layout first. Back the workbook up before running them, and close it in Excel.
Re-running on a workbook that already has the columns stops at the assertion; it does not duplicate them.
