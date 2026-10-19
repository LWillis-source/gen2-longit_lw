# Diet-log analyses (LONGIT-weeklong)

Durable rules for this folder. No counts, results or status here: those go in the notebooks or `PROGRESS.md`. The reasons behind the rules are in `BEST_PRACTICES_CLAUDE.md` (section numbers given as §n).

## Project
Analyses of the LONGIT-weeklong study (Gen2 CapScan; saliva, capsule regions R1-R3, stool), one notebook each in `scripts/`:
0. `component0_diet_logs`: what is in the diet logs (descriptive; used by both components).
1. `component1_foodseq_diet`: is the diet log reflected in the food sequencing data (trnL plants run, 12SV5 meat run)? Measures: recall and precision (no specificity).
2. `component2_diet_16S`: does diet (live-microbe foods, fibre variety) relate to 16S community composition?
Within components 1 and 2, stool, capsule and saliva are analysed in turn.

At the start of each session read `PROGRESS.md` (status, decisions, deviations, open questions). Be factual; base statements on verified facts.

## Layout and running code
- `scripts/`: analysis notebooks and `.py` modules (`diet_log.py`, `food_seq.py`; tested in `scripts/tests/test_modules.py`). `figures/`: all outputs (a subfolder per notebook).
- `scripts/profile_inputs.py` writes the input reports to `figures/input_profiles/` (workflow step 0).
- `old_scripts_figures/`: earlier diet-log and food-sequencing scripts and figures. Reference only; copy ideas or code into `scripts/`, never run or edit in place.
- `scripts_daily_diet_coding/`: scripts that built `daily_diet_coding.xlsx`. Run only by the user.
- `.claude/`: `settings.json` (write hook, Bash sandbox) and `agents/reviewer.md` (the read-only reviewer for workflow step 8). Edited only by the user.
- Python: `/opt/anaconda3/bin/python`, run from the repository root (`python diet_log_analyses/scripts/<script>.py`).
- Shared modules live in `2-analysis_python/` (`config.py`, `weeklong_16s.py`, `weeklong_food.py`). Import them through `scripts/_paths.py` (`import _paths` first; a notebook first adds `diet_log_analyses/scripts` to `sys.path`). `_paths` defines `FIG_DIR` and `DIET_CODING`. Do not copy the shared modules here.

## Writing files (§11)
- Claude may write only to `scripts/`, `figures/` and `PROGRESS.md`. A PreToolUse hook and the Bash sandbox (`.claude/settings.json`) enforce this. If a write is blocked, stop and tell the user what was to be written and why; never work around the block.
- All data sources are read-only: `1-data/`, the sample sheet in the sibling repository, `daily_diet_coding.xlsx` and any other workbook of the user's. So are `2-analysis_python/`, the R originals and the `CLAUDE.md` files.
- Ask before deleting anything, even inside `figures/`.

## Workflow for each notebook section
One section at a time (§6). Steps 1, 7 and 8 are stopping points for the user.
0. **Inputs (§4, §5).** At the start of each session, and whenever an input may have changed, run `scripts/profile_inputs.py`. Read `figures/input_profiles/changes.md` and `joins.md`, and use the per-input reports to learn a file's structure instead of opening the workbook. If an input changed: compare its report with the one in `previous/`, classify every difference (correction vs change of meaning), rerun `scripts/tests/`, and record the change in `PROGRESS.md` before any analysis. Never copy counts from the reports into `CLAUDE.md`.
1. **Plan (§1).** Propose the question, data, method, parameters, lag window and the checks with their expected results. Wait for approval before running anything. The notebook's first section is the overall plan; changes after approval are recorded as dated deviations in the notebook and `PROGRESS.md`.
2. **Load and join (§4).** State which input versions are used (checksums in `figures/input_profiles/manifest.json`). Print row counts at every step; report any unexpected drop or duplicate.
3. **Check (§2).** State each expected result before running the check; a mismatch is a bug to find, not a rounding difference. Every section includes:
   - property checks: sample order or subject labels change nothing; shuffled exposures, or diet after sampling, give no effect;
   - positive and negative controls in the real data, including blanks;
   - a by-hand trace of 3-4 random samples from the workbook row to the analysis table.
4. **Analyse.** Write outputs to `figures/<notebook name>/` (see "Notebook style").
5. **Look (§6).** Open and inspect every new figure before describing it.
6. **Rerun (§12).** Run the whole notebook from scratch (`jupyter nbconvert --to notebook --execute --inplace <nb>.ipynb`); report only results from that run. Never rely on kernel state; the user may have run cells interactively.
7. **Report (§3).** Give the cell or table each number comes from and show the evidence (check output, command and result) rather than stating that a check passed. Label analyses outside the approved plan as exploratory.
8. **Review (§8).** Run the `reviewer` subagent (`.claude/agents/reviewer.md`, read-only) on every finished section before its results are treated as final. Give it the notebook path, the section and where the approved plan is; do not pass it your own reasoning. Show the user its findings in full. Fix findings that affect correctness or the plan (then rerun from step 6); list the rest as optional. The `mycelium:review` skill is an alternative when the user asks for it.
9. **Record (§10).** Update `PROGRESS.md`: status, decisions, deviations, open questions.

## Testing new statistical methods (§2)
Before a new model, permutation scheme or transform is used on real data:
- simulated data shaped like the real data, with a planted effect (must be recovered) and with no effect (about 5% of p-values below 0.05, roughly uniform p-values);
- a tiny case computed by hand;
- a second implementation where one exists (R `vegan::adonis2`, `nlme`, `compositions`; Python `statsmodels`);
- one deliberate break of the code (e.g. shuffled subject labels) to confirm the tests fail.
Save these as `pytest` tests in `scripts/tests/` and rerun them whenever the code changes. Explain tests and results in chat. 

## Statistics (§7)
- Every number comes from code and is traceable to a notebook cell or output table; never report a value read off a table or plot.
- Repeated measures: samples from one subject are not independent.
  - Models: mixed models with a random intercept per subject.
  - Composition, within-subject questions: PERMANOVA with permutations restricted within subject.
  - Between-subject questions (e.g. habitual intake): one value per subject (the subject's mean), so the sample size is the number of subjects.
- Separate within- from between-subject effects by splitting each exposure into the subject's mean and the deviation from it; never let one coefficient mix the two.
- Tests are primary (named in the plan, few), secondary (reported as a set with FDR) or exploratory (labelled as such). FDR across taxa x exposures; effect sizes with confidence intervals.
- Compositional data: CLR / Aitchison distance as the primary approach. Before CLR, filter rare taxa by prevalence and add a pseudocount, both stated in the plan, with a sensitivity analysis on the choice. Other distances (Bray-Curtis, Canberra, Jaccard, UniFrac) may be secondary, using the shared `config.distance()`.
- Rarefy (fixed seed) only for richness and presence/absence measures (Jaccard, unweighted UniFrac, Canberra); never for abundance-based measures.
- Differential abundance: one pre-specified method, other methods as a sensitivity analysis.
- Covariates are chosen in the plan for each sample type, from read depth, study day, Bristol score, transit time (capsules only) and region. A covariate that could lie on the path from diet to microbiome (e.g. Bristol score) goes in a sensitivity analysis, not the primary model.
- Small n: a few pre-specified tests; lag windows fixed in the plan. Report a null result with the smallest effect the design could detect (from the simulation tests).
- Fixed, exposed seeds for permutations and any stochastic method; one parameters cell near the top of each notebook (paths via `_paths`, cut-offs, windows, seeds).
- State in each section: data files and versions, join path, exclusions with reasons (never silent), parameters.

## Notebook style (§12)
Write notebooks so the user can follow every output without reading the code closely:
- Before each code cell, a short markdown cell says what the cell does and what its output should show (e.g. "one row per subject-day; fewer rows than in the previous step means the join dropped days").
- Inside cells, comment each step that is not obvious: why a filter, join, transform or parameter is used, and which CLAUDE.md rule it follows.
- Label every printed number and table: what it counts, its unit, and which step it comes from. Never print bare numbers.
- Every figure has a title, labelled axes with units, and a markdown note below it saying how to read it.
- Every figure shown in a notebook is also saved, from the same code, to `figures/<notebook name>/` (one subfolder per notebook; a further subfolder per section if there are many). Save each as PNG at 300 dpi for slides and as PDF for editing, with a descriptive file name that starts with the section number (e.g. `02_richness_vs_fermented_dose.png`). Also save the table the figure was drawn from as CSV next to it.

## Communication (§9)
Ask when a request or decision has more than one reasonable reading (definitions, exclusions, windows, models); otherwise state the reading used.

## Data sources (§4)
- Sample metadata: `gen2_capScan_sanitized00/data/work-in-progress-meta/LONGITWeeklong-samplesheet-FINAL.xlsx` (sibling repository). Load only through `weeklong_16s.read_sample_sheet()`: Sample_ID sheet -> `Kit_ID` -> Kit_ID sheet (Subject_ID, ingestion/collection date and time, Transit_time_h, BSS, Sampling_no). The workbook also holds the questionnaires (e.g. Pre-ingestion-Lifestyle) and Daily-Nutrient.
- Diet logs: `daily_diet_coding.xlsx`. Tabs: `daily_diet_coding` (one row per food entry; `"(assumed)"` marks inferred ingredients), `source_diet_text`, `ingredient_lexicon`, `needs_review`, `collapse_groups`, `informative_changes`, `README`.
  - Ingredient lists come from `Ingredients` in the `daily_diet_coding` sheet.
  - Species come from the lexicon's `Species (scientific name)`, looked up by `Ingredient` name. The `daily_diet_coding` sheet also has a `Species (scientific name)` column: it is a de-duplicated per-entry summary with rank tags (`"(species)"`, `"(variety)"`) in its own order, not aligned with `Ingredients`. Never match the two by position.
  - Food classifications come only from columns in the `ingredient_lexicon` sheet, by exact name: `Informative for sequencing? (Yes / Uncertain / No)`, `Fermented? (Yes / No / Variable / Unknown)`, `Fibrous? (Yes / No / Variable / Unknown)`, `Likely live microbes? (Yes / Variable / No / Unknown)`, `Dairy? (Yes / No / Variable / Unknown)`, plus the taxonomy and collapse-group columns. Never hard-code food lists.
- Subject 11 has no coded diet log: omit them from every analysis that uses the diet log. Tables or figures that do not use it (e.g. read depth, detection rates, 16S overviews) may include subject 11, and must say whether they do.
- 16S: `1-data/DADA2-weeklong/`. Food sequencing: `1-data/DADA2-weeklong-plants/` (trnL), `1-data/DADA2-weeklong-meat/` (12SV5). In each, the count table is `seqtab_all.rds`, which matches `feature_data.txt` and `dsvs_msa.tree`; read it through `config.py`. The plants folder's `seqtab.rds` has extra ASVs with no taxonomy: do not use it.
- Plant families: the lexicon's `Family` column, matched by genus (plants feature_data has no Family). `1-data/genus_family_gbif.csv` is an earlier GBIF lookup for a subset of these genera; it agrees with the lexicon on all of them and is a cross-check only. A plant genus in neither source is not a lexicon food: look up its family only if an analysis needs it, and record the source. Meat families: meat feature_data (blank for ASVs not assigned to a genus).
- When an input changes (§5), compare old and new versions, classify every difference (correction vs change of meaning), and rerun everything that depends on it.

## Join rules (§4)
Diet log -> subject/day -> sample -> sequencing run -> taxon. Check row counts before and after every join.

**Subjects and days**
- `Subject_ID` is an integer in `daily_diet_coding` / `source_diet_text` but zero-padded text elsewhere (`read_sample_sheet()`, Daily-Nutrient, questionnaires: `"01"`). Convert the diet side with `f"{int(s):02d}"`.
- Diet days are `Date (MM-DD)` text in 2025. `Day_key` = `f"{Subject_ID}_{MM-DD}"`, unpadded subject (`"1_08-03"`). Study day: `source_diet_text.Event_name`, read as the number after "Day" (`"Day 01 ingestion "` -> 1, `"Day 08"` -> 8). Days 01-07 end in "ingestion" (Day 01 with a trailing space); Days 08-10 do not.
- Sample-sheet dates are `yymmdd` text; `read_sample_sheet()` adds `Collection_date_reformat` (`"MM-DD"`). Datetimes = 2025-MM-DD + `HH:MM`; `"NR"` or blank time means unknown, not midnight.
- Daily-Nutrient (`Subject_ID` text, `Date_reformat` `"MM-DD"`) mostly covers days before the diet log started; check overlap with the diet days before using it as a daily exposure.

**Samples**
- Sample type comes from `read_sample_sheet()`: `Sample_origin3` = `Stool` / `Saliva` / `Capscan`; for capsules, `Region` gives the region (`R1`, `R2`, `R3`). Never infer the type from library or sample names.
- Saliva is collected at capsule ingestion: its time is the kit's Ingestion_date/time.
- A stool can list several kits (`"LS114, LS115"`): same subject and collection time; session labels from the first kit; no single transit time.
- `"NR"` = not recorded, `"NM"` = not measured: real tokens, not blanks.
- Libraries -> `Sample_ID` through the `1-data` info sheets, not the sample sheet's `16S_filename`. In every run the library (count-table row) name is the info sheet's `Sample` without its `"sample_"` prefix.
  - 16S: `1-data/Weeklong-sample-info.xlsx`. Count-table rows with no info-sheet row have no `Sample_ID` and are not used (mostly blanks; see `PROGRESS.md` for 4 study samples among them).
  - Food runs: `1-data/Weeklong-meat-plants-sample-info.xlsx` (`group` = Meat / Plant; `Group` = LONGIT / Blank / IBD / gen3: keep LONGIT, Blank only as controls; blanks have no `Sample_ID`). 5 meat-run blanks have no row in the count table: treat them as zero reads.
  - The plants and meat runs sequenced the same samples: join them on `Sample_ID`, never on library name.

**Food entries and exposure windows**
- A food entry is (`Day_key`, `Entry_no`). `Ingredients` is `;`-separated; strip only a trailing `" (assumed)"` to get the lexicon `Ingredient` (exact match) and keep a stated/assumed flag. Other brackets are part of the name: `"beans (unspecified) (assumed)"` -> `"beans (unspecified)"`, assumed. Count presence once per subject-day (or meal) per ingredient unless entries are the unit.
- Meal timing only from `Time/meal as logged`: meal word (breakfast/brunch, lunch, dinner) first, else clock time (<11:00 breakfast, 11:00-15:59 lunch, >=16:00 dinner), else "not recorded". Never infer a meal from an entry's position alone (e.g. first entry = breakfast). Reading clock times:
  - the first time in the text counts; a range (`"6-7:30pm"`) is read at its start, with any am/pm written after the range applied to it;
  - a time with am/pm, or an hour of 13 or more, is taken as written;
  - a bare 1:00-5:59 is pm;
  - any other bare time before 12:00 is am or pm, whichever keeps that day's entries (in `Entry_no` order) in time order. Each entry that has a time sets the reference for the next, even if a meal word decided its own meal.

  Reference: `old_scripts_figures/diet_log_meal_timeseries.py::assign_meals`.
- Link diet to a sample by time before collection (lag window), within subject, and only when the window lies entirely inside the subject's logged days; otherwise unlogged eating counts as absence.

**Ingredients to taxa**
- Lexicon `Marker that can detect it`: `trnL` = plants run, `12SV5` = meat run, `none` = not amplified (never "absent"). Three other values occur (`trnL / 12SV5`, `12SV5 (fish part only)`, `unknown`), one ingredient each; their species are unspecified, so they cannot be matched to ASVs and are treated as undetectable.
- Lexicon `Species (scientific name)` formats (parse each case explicitly):
  - one binomial, or several `;`-separated species; any may carry `"(assumed)"`;
  - `var.`/`subsp.` names (`"Brassica oleracea var. capitata"`);
  - `"Genus spp."`; hybrids `"Citrus x sinensis"` and two-parent `"Musa acuminata x balbisiana"`;
  - a family with a genus in parentheses (`"Bambusoideae (Phyllostachys spp.)"`) or a family only (`"Gadidae (...)"`);
  - a higher taxon with a description (`"Actinopterygii (unspecified fish)"`, `"Teuthida (squid)"`): undetectable at ingredient level;
  - a slash list of genera (`"Triticum / Zea / Avena / Oryza (unspecified)"`): undetectable (too unspecific to test);
  - a description with no taxon (`"unspecified fruit"`, `"mixed botanicals (unspecified)"`, `"none (no food DNA)"`, `"unknown"`): undetectable.
- Ingredient -> compatible ASVs in one run, for each species in the lexicon field:
  - parse genus and epithet; `var.`/`subsp.` parts are ignored (`"Brassica oleracea var. capitata"` -> *Brassica oleracea*);
  - `"Genus spp."` or a hybrid (`"Genus x epithet"`, or two-parent `"Genus a x b"`) has no epithet: all ASVs of the genus count;
  - a family with a genus in parentheses uses that genus with no epithet; a family alone matches nothing (undetectable, not absent);
  - with an epithet: the genus's ASVs labelled with that epithet (plants: the epithet, or the epithet followed by `_…`; meat: the binomial) plus its unlabelled ASVs. Congener-labelled ASVs are excluded, and so are hybrid labels such as `"Bos grunniens x Bos taurus"`;
  - congener fallback: if no ASV in that run carries the epithet (e.g. every *Spinacia* ASV is *S. tetrandra*), all ASVs of the genus count;
  - ASVs labelled with the exact epithet are species-level evidence; the rest are genus-level.
- `feature_data.txt` `Species` is the epithet only in the plants run (`"max"`) but the binomial in the meat run; quoted `"NA"` is missing. The plants colour sheet has a genus row literally named `"NA"`.

## Gotchas
- Read Excel with `config.read_excel_like_readxl()`, never plain `pd.read_excel` (it turns `"01"` into 1 and `"NA"` into NaN).
- phyloseq orders taxa by tree tip order: `OTU` names (`feature_%04d`) differ from `Feature` in `feature_data.txt`. Label by `Feature`.
- Plant ASVs are mostly labelled only to genus, sometimes to a congener of the food (rule above). Food taxa: match each species an ingredient lists to its compatible ASVs, and merge species whose ASVs overlap (`food_seq.food_taxa`); a recipe (e.g. kimchi) belongs to each of its species' taxa and must never glue taxa together.
- The markers cannot separate some foods (milk, cheese and beef are all *Bos taurus*): compare per sequencing-resolvable taxon, not per ingredient.
- Food DNA appears in stool ~12 h to ~5 days after eating; one stool sample detects only a fraction of recent foods, so per-sample and per-subject recall are not comparable.
