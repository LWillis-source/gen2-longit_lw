# Best practices for diet-microbiome analyses with Claude

*A guide to using Claude (Claude Code) for computational analyses of diet and microbiome data: planning, verifying, and reporting analyses whose code is written largely by an AI assistant. The recommendations come from Anthropic's Claude Code documentation, from the literature on reproducible scientific computing and software testing, and from methodological papers on microbiome statistics. References are numbered and listed at the end.*

---

## 1. Write the analysis plan before looking at results

Decide in writing what the question is and how it will be answered **before** running the models: exposures, outcomes, sample types, time window, statistical model, covariates, multiple-testing control, and what result would count as an effect. Record any later change as a dated deviation with its reason.

**Why:** an analysis has many defensible choices (exclusions, transforms, covariates, cut-offs). If the choices are made after seeing the data, the false-positive rate can rise far above the nominal 5%, even without deliberate fishing [1, 2]. Fixing the plan in advance keeps hypothesis testing separate from hypothesis generation [3]. For Claude, a written plan is also a fixed target: the Claude Code documentation recommends exploring and planning before implementing, so that the code does not solve the wrong problem [4].

**In practice:** ask Claude to draft the plan, edit it yourself, and only then let it write analysis code. Label anything outside the plan as exploratory.

## 2. Give Claude something it can check its own work against

Without a check it can run, Claude stops when the work *looks* done; with a pass/fail check, it can test and fix its own work [4]. In analysis code this matters more than elsewhere, because a wrong answer rarely crashes. It usually produces a plausible number. Software testing calls this the *oracle problem*: there is often no independent way to know the correct output [5]. The following checks work without a reference implementation. Write down the expected result before running each one.

1. **Simulated data with a known answer.** Generate data that resemble the real data (number of subjects, samples per subject, sparsity), with the truth set by you. With a planted effect, the method must recover it with roughly the right size. With no effect, about 5% of tests should fall below p = 0.05 and p-values should be roughly uniform. A higher rate means the test is anti-conservative, as happens when repeated samples from one person are treated as independent. Simulation is the standard way to evaluate a statistical method's bias, coverage and error rates, and it is the only check that tests the design rather than the arithmetic [6]. Simulation benchmarks have shown that some widely used microbiome differential-abundance tools have inflated false-positive rates [7].
2. **The same statistic from a second implementation.** Standard statistics usually exist in more than one package (e.g. PERMANOVA in R `vegan::adonis2` [8]; mixed models in Python `statsmodels` and R `nlme`). Agreement rules out implementation errors, not design errors.
3. **Tiny cases checkable by hand.** A few samples with made-up counts, for which a transform, a distance or a test statistic can be worked out directly. Keep them as automated tests so they rerun whenever the code changes [9, 10].
4. **Properties that must hold (metamorphic tests).** When the correct output is unknown, test relations between outputs instead: reordering samples or relabelling subjects changes nothing; adding taxa that are zero everywhere leaves distances unchanged; shuffling the exposure removes the effect; an exposure measured *after* the outcome predicts nothing [11, 12].
5. **Positive and negative controls in the real data.** Effects that must appear (e.g. large differences between body sites or between individuals), a relationship already known to hold that passes through the same data joins, and negative controls (extraction and PCR blanks) that must show little signal. Blanks are essential in low-biomass samples, where contaminant DNA can dominate [13].
6. **End-to-end traces.** Follow a few randomly chosen records by hand from the raw file to the final analysis table. Join and timing errors that leave totals plausible show up here.
7. **An independent second implementation or review.** A fresh Claude session or subagent that has not seen the reasoning behind the code either reimplements the step from the written plan or reviews it. A fresh context is not biased towards code it just wrote [4].
8. **Make the checks fail on purpose.** Deliberately break the code (shuffle labels, shift dates, swap columns) and confirm each check notices. A check that still passes protects nothing. This is the idea behind mutation testing [14].

**In practice:** checks 4-6 in every analysis step; checks 1-3 once for each new statistical method, saved as tests; check 7 for results that conclusions rest on. Ask Claude to show the evidence (the test output, the command and what it returned) rather than to state that the check passed [4].

## 3. Every number comes from code, not from Claude reading the data

Claude writes, runs and debugs the code; the code computes every number. Claude should not read a value off a spreadsheet or a plot and report it, or state a conclusion beyond what the code computed. Each reported number should be traceable to the script and table that produced it.

**Why:** reproducibility requires recording how every result was produced and avoiding manual data manipulation [10]. A language model can also lose or misremember details as its context fills during a long session [4]; code that is rerun cannot.

## 4. Pin down data sources, versions and joins; read files faithfully

State which files, sheets and versions an analysis uses and how they are joined. Keep raw data read-only and derive everything from it with scripts [9, 10]. Read spreadsheets so that their content survives: some readers silently convert codes such as `"NA"` (which may be a real category) to missing values, or text identifiers such as `"01"` to numbers.

**Ask Claude to:** print row counts before and after every join, and report rows that are dropped or duplicated rather than absorb them silently.

## 5. When inputs change, look for what changed silently

A changed input breaks an analysis loudly (a crash) or silently (different results with no error). The silent kind needs an explicit comparison: old vs new values, outputs that were not regenerated, rows that no longer join. Record intermediate results and keep outputs regenerable from scripts, so that any figure can be traced to the inputs and code that produced it [10].

## 6. Work in small steps and look at every figure

Build one step at a time and check its output before the next: load, describe, one model, one figure. Feedback loops are most effective when they are short, and early correction is cheaper than late [4]. Look at every figure: plots expose problems that summary numbers hide. Ask Claude to open each figure and compare it with what you expected before describing it.

## 7. Statistical guardrails for diet-microbiome data

Ask Claude to respect these, and to say explicitly when an analysis does not:

- **Repeated measures.** Several samples per person are not independent. Use subject-level random effects, or permutations restricted within subject. PERMANOVA assumes exchangeable samples under the null hypothesis, so free permutation across repeated measures is invalid [8].
- **Between- vs within-person effects.** Habitual intake varies only between people; daily intake also varies within a person. The two answer different questions and should be estimated separately, not merged into one coefficient [15].
- **Personalised and lagged responses.** Diet-microbiome associations can be highly individual and depend on several preceding days of intake [16, 17]. Choose the lag window in advance.
- **Compositional data.** Sequencing counts carry only relative information. Use log-ratio methods (e.g. CLR, Aitchison distance) and treat zeros explicitly [18]. Normalisation choices change results [19].
- **Method dependence.** Differential-abundance methods give very different results on the same data; prefer a pre-specified method and, as a sensitivity analysis, check agreement across methods [7].
- **Confounders and technical variables.** Sequencing depth, sample handling and stool consistency, sample type, and time in the study [20, 21].
- **Multiple testing and effect sizes.** Control the false discovery rate across taxa × exposures [22]. Report effect sizes with confidence intervals, not only p-values [23].
- **Small samples.** Prefer a few pre-specified tests over many exploratory ones, and label exploratory results as such [1, 3].
- **Reporting.** Follow the STORMS checklist for human microbiome studies [21].

## 8. Ask for a sceptical second pass

When a step is finished, have it reviewed as a referee would: wrong joins, wrong denominators, leakage between exposure and outcome, confounding, over-claiming. A reviewer in a fresh context (a separate session or subagent) sees only the work and the criteria, not the reasoning that produced it [4]. Ask the reviewer to flag only problems that affect correctness or the stated plan: a reviewer asked to find gaps will usually report some, and chasing every one leads to over-engineering [4].

## 9. Say what you mean, and expect Claude to ask

Give Claude specific context: which files, which constraints, what "done" looks like [4]. Supply what only you know: biological expectations, what reviewers will ask, which result would change a conclusion. Claude should ask when a request has more than one reasonable reading and should state the reading it chose. For larger pieces of work, ask Claude to interview you before writing a plan [4].

## 10. Keep project memory in files, not in the conversation

Long conversations are summarised, and a new session starts without the previous one's memory. Durable rules belong in `CLAUDE.md`, which Claude reads at the start of every session. Keep it short and specific: for each line, ask whether removing it would cause mistakes, because important rules get lost in a long file, and specific, concise instructions are followed more consistently [4, 24]. The plan, decisions and status belong in the notebook or a progress file. Start a fresh session between unrelated tasks, and after repeated failed corrections [4].

## 11. Be careful with anything that cannot be undone

Raw data are read-only; outputs are regenerable from code [9, 10]. Use version control and keep backups before editing any hand-maintained file [9, 10]. Claude Code's checkpoints undo Claude's own file edits but not the effects of shell commands, so they are no substitute for version control [4]. Rules that must hold every time (e.g. never write to the data folder) can be enforced with hooks, which, unlike `CLAUDE.md` instructions, are deterministic [4].

## 12. Notebooks with Claude

- A notebook is trustworthy only if it runs top to bottom from a fresh kernel. Interactive editing can leave hidden state that the saved code no longer reproduces [25]. Claude cannot see your live kernel: it should rerun the whole notebook (e.g. `jupyter nbconvert --to notebook --execute`) before reporting results.
- Keep reusable logic in modules and use the notebook for the narrative, figures and decisions [25].
- Put file paths, cut-offs and random seeds in one parameters cell near the top, and record software versions [10, 25].
- Document each step as you go, explaining why as well as what [25].

---

## Quick reference

| Risk | Practice | Sources |
|---|---|---|
| Chance findings from many choices | Pre-specified plan (§1), FDR control (§7) | [1, 2, 3, 22] |
| Plausible but wrong code | Pass/fail checks with expected results stated first (§2) | [4, 5, 6, 11, 14] |
| Misread or misremembered values | Numbers come from code (§3) | [4, 10] |
| Silent input changes | Explicit comparisons, regenerable outputs (§4, §5) | [9, 10] |
| Errors visible only in plots | Look at every figure (§6) | [4] |
| Person effects mistaken for diet effects | Repeated-measures models, within/between separation (§7) | [8, 15, 16] |
| Compositional artefacts | Log-ratio methods, method sensitivity (§7) | [7, 18, 19] |
| Lost context between sessions | Memory in files (§10) | [4, 24] |
| Irreversible mistakes | Read-only inputs, version control, hooks (§11) | [4, 9, 10] |
| Hidden notebook state | Run from scratch before reporting (§12) | [25] |

---

## References

1. Simmons JP, Nelson LD, Simonsohn U. False-positive psychology: undisclosed flexibility in data collection and analysis allows presenting anything as significant. *Psychological Science* 2011;22(11):1359–1366. doi:10.1177/0956797611417632
2. Gelman A, Loken E. The statistical crisis in science. *American Scientist* 2014;102(6):460–465.
3. Nosek BA, Ebersole CR, DeHaven AC, Mellor DT. The preregistration revolution. *PNAS* 2018;115(11):2600–2606. doi:10.1073/pnas.1708274114
4. Anthropic. Best practices for Claude Code. Claude Code documentation. https://code.claude.com/docs/en/best-practices (accessed 2026-10-17).
5. Barr ET, Harman M, McMinn P, Shahbaz M, Yoo S. The oracle problem in software testing: a survey. *IEEE Transactions on Software Engineering* 2015;41(5):507–525. doi:10.1109/TSE.2014.2372785
6. Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Statistics in Medicine* 2019;38(11):2074–2102. doi:10.1002/sim.8086
7. Nearing JT, Douglas GM, Hayes MG, et al. Microbiome differential abundance methods produce different results across 38 datasets. *Nature Communications* 2022;13:342. doi:10.1038/s41467-022-28034-z
8. Anderson MJ. A new method for non-parametric multivariate analysis of variance. *Austral Ecology* 2001;26(1):32–46. doi:10.1111/j.1442-9993.2001.01070.pp.x
9. Wilson G, Bryan J, Cranston K, Kitzes J, Nederbragt L, Teal TK. Good enough practices in scientific computing. *PLOS Computational Biology* 2017;13(6):e1005510. doi:10.1371/journal.pcbi.1005510
10. Sandve GK, Nekrutenko A, Taylor J, Hovig E. Ten simple rules for reproducible computational research. *PLOS Computational Biology* 2013;9(10):e1003285. doi:10.1371/journal.pcbi.1003285
11. Chen TY, Kuo F-C, Liu H, et al. Metamorphic testing: a review of challenges and opportunities. *ACM Computing Surveys* 2018;51(1):4. doi:10.1145/3143561
12. Claessen K, Hughes J. QuickCheck: a lightweight tool for random testing of Haskell programs. *Proceedings of ICFP* 2000:268–279. doi:10.1145/351240.351266
13. Eisenhofer R, Minich JJ, Marotz C, Cooper A, Knight R, Weyrich LS. Contamination in low microbial biomass microbiome studies: issues and recommendations. *Trends in Microbiology* 2019;27(2):105–117. doi:10.1016/j.tim.2018.11.003
14. Jia Y, Harman M. An analysis and survey of the development of mutation testing. *IEEE Transactions on Software Engineering* 2011;37(5):649–678. doi:10.1109/TSE.2010.62
15. Curran PJ, Bauer DJ. The disaggregation of within-person and between-person effects in longitudinal models of change. *Annual Review of Psychology* 2011;62:583–619. doi:10.1146/annurev.psych.093008.100356
16. Johnson AJ, Vangay P, Al-Ghalith GA, et al. Daily sampling reveals personalized diet-microbiome associations in humans. *Cell Host & Microbe* 2019;25(6):789–802.e5. doi:10.1016/j.chom.2019.05.005
17. David LA, Maurice CF, Carmody RN, et al. Diet rapidly and reproducibly alters the human gut microbiome. *Nature* 2014;505:559–563. doi:10.1038/nature12820
18. Gloor GB, Macklaim JM, Pawlowsky-Glahn V, Egozcue JJ. Microbiome datasets are compositional: and this is not optional. *Frontiers in Microbiology* 2017;8:2224. doi:10.3389/fmicb.2017.02224
19. Weiss S, Xu ZZ, Peddada S, et al. Normalization and microbial differential abundance strategies depend upon data characteristics. *Microbiome* 2017;5:27. doi:10.1186/s40168-017-0237-y
20. Knight R, Vrbanac A, Taylor BC, et al. Best practices for analysing microbiomes. *Nature Reviews Microbiology* 2018;16:410–422. doi:10.1038/s41579-018-0029-9
21. Mirzayi C, Renson A, Genomic Standards Consortium, et al. Reporting guidelines for human microbiome research: the STORMS checklist. *Nature Medicine* 2021;27:1885–1892. doi:10.1038/s41591-021-01552-x
22. Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 1995;57(1):289–300. doi:10.1111/j.2517-6161.1995.tb02031.x
23. Wasserstein RL, Lazar NA. The ASA statement on p-values: context, process, and purpose. *The American Statistician* 2016;70(2):129–133. doi:10.1080/00031305.2016.1154108
24. Anthropic. How Claude remembers your project. Claude Code documentation. https://code.claude.com/docs/en/memory (accessed 2026-10-17).
25. Rule A, Birmingham A, Zuniga C, et al. Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks. *PLOS Computational Biology* 2019;15(7):e1007007. doi:10.1371/journal.pcbi.1007007
