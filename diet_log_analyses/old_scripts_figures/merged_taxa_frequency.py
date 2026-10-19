"""How often each merged, sequencing-resolvable taxon was logged in the Weeklong diet logs.

Rows are the overlap-merged taxa of diet_stool_confusion.py (--merge-overlapping): all
ingredients rated 'Yes' for sequencing, split into their species (recipes such as kimchi give one
component per species) and merged whenever their compatible ASVs overlap, e.g. one Brassica row
for cabbage, broccoli, bok choy, mustard and kimchi's Brassica. Components with no compatible ASV
(cucumber, corn, apple, ...) form grey rows, merged by the taxon they name.

Bars: subject-days on which any member was logged (each day counts once per taxon). Solid = stated
in the log that day; hatched = only assumed. Components of multi-species recipes (kimchi, feta)
always count as assumed, as in the genus frequency plot.

Outputs (diet_log_analyses/figures_Diet-logs/)
    merged_taxa_frequency_top40.png
    merged_taxa_frequency_all.png
    merged_taxa_frequency.csv

Usage (from the repository root):
    python diet_log_analyses/merged_taxa_frequency.py
"""

from __future__ import annotations

import pandas as pd
from matplotlib.patches import Patch

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import diet_log_ingredients as D
import diet_stool_confusion as CF
import diet_vs_stool_grouped as G
import stool_detection_timeseries as S

OUT = D.OUT


def merged_rows_table(level="genus"):
    """Long table (entry, day, subject, taxon row, stated) plus one info row per merged taxon."""
    entries, lexicon = D.read_coding()
    long = D.split_ingredients(entries)
    informative = lexicon.index[lexicon["informative"] == "Yes"]
    runs = S.load_runs()
    rows, _ = CF.overlap_rows(pd.DataFrame({"ing": list(informative)}), lexicon, runs, level)

    # component (ingredient, species) -> row key; undetectable components keyed by the taxon they name
    comp_row = {}
    asv_owner = {}
    for r in rows.itertuples(index=False):
        for a in r.asvs:
            asv_owner[(r.run, a)] = r.row
    info = {r.row: {"taxon": r.taxon, "level": "species" if " " in r.taxon else "genus",
                    "n_ASVs": len(r.asvs)} for r in rows.itertuples(index=False)}
    for ing in informative:
        marker = lexicon.at[ing, "marker"]
        run = S.RUN_OF_MARKER[next(m.strip() for m in str(marker).split(";") if m.strip() in S.RUN_OF_MARKER)]
        for sp in D.species_list(lexicon.at[ing, "species"]):
            allc, _ = S.compatible_asvs(sp, runs[run].tax)
            if allc:
                key = asv_owner[(run, next(iter(allc)))]
            else:
                key = "none:" + G.undetectable_taxon(sp)
                info.setdefault(key, {"taxon": G.undetectable_taxon(sp), "level": "undetectable", "n_ASVs": 0})
            comp_row.setdefault(ing, []).append(key)

    out = []
    for r in long[long["ing"].isin(informative)].itertuples(index=False):
        keys = list(dict.fromkeys(comp_row[r.ing]))
        recipe = len(D.species_list(lexicon.at[r.ing, "species"])) > 1
        for k in keys:
            out.append({"entry": r.entry, "Day_key": r.Day_key, "Subject_ID": r.Subject_ID, "row": k,
                        "ing": r.ing, "stated": r.stated and not recipe})
    return pd.DataFrame(out), info


def label_for(taxon, members):
    shown = ", ".join(members[:3]) + (f" +{len(members) - 3}" if len(members) > 3 else "")
    name = taxon.replace(" ", "~").replace("/", "/")
    return f"$\\it{{{name}}}$ ({shown})"


LEVEL_COLOUR = {"species": D.GREEN, "genus": D.PURPLE, "undetectable": D.GREY}


def main():
    longrows, info = merged_rows_table()
    freq = D.frequency(longrows, "row")
    ing_days = longrows.drop_duplicates(["ing", "Day_key"]).groupby("ing").size()
    members = (longrows.drop_duplicates(["row", "ing"]).assign(days=lambda d: d["ing"].map(ing_days))
               .sort_values(["row", "days", "ing"], ascending=[True, False, True]).groupby("row")["ing"].agg(list))
    freq["taxon"] = freq["row"].map(lambda k: info[k]["taxon"])
    freq["level"] = freq["row"].map(lambda k: info[k]["level"])
    freq["n_ASVs"] = freq["row"].map(lambda k: info[k]["n_ASVs"])
    freq["ingredients"] = freq["row"].map(lambda k: ", ".join(members[k]))
    freq.drop(columns="row").to_csv(OUT / "merged_taxa_frequency.csv", index=False)

    legend = [Patch(facecolor=D.GREEN, label="Resolves to one species in plants/meat feature_data.txt"),
              Patch(facecolor=D.PURPLE, label="Genus level only (merged or genus-labelled ASVs)"),
              Patch(facecolor=D.GREY, label="No compatible ASV in either run (undetectable)")] + D.hatch_keys()
    note = ("Only ingredients rated 'Yes' for sequencing. Rows merge ingredients (and recipe components) whose "
            "compatible ASVs overlap; parentheses list up to 3 members (+n more).\nRecipe components (kimchi, feta) "
            "count as 'assumed'. Merging follows the ASV labels in feature_data.txt, not proof of detection in "
            "these subjects.")
    for name, df in [("top40", freq.head(40)), ("all", freq)]:
        labels = [label_for(t, members[k]) for t, k in zip(df["taxon"], df["row"])]
        D.frequency_plot(df.reset_index(drop=True), labels, [LEVEL_COLOUR[l] for l in df["level"]],
                         OUT / f"merged_taxa_frequency_{name}.png",
                         f"{'Top 40' if name == 'top40' else 'All'} merged sequencing-resolvable taxa, weeklong diet logs",
                         f"{D.N_SUBJECTS} subjects (subject 11 excluded), {D.N_DAYS} subject-days. Ingredients merged "
                         "when sequencing cannot tell them apart; each day counts once per taxon.",
                         note, f"Subject-days on which the taxon appears (out of {D.N_DAYS})", legend=legend,
                         xmax=215, legend_below=True)
    counts = freq["level"].value_counts().to_dict()
    print(f"{len(freq)} merged taxa logged: {counts}")
    print(freq.head(12)[["taxon", "subject_days", "days_stated", "days_assumed_only", "ingredients"]]
          .to_string(index=False, max_colwidth=70))
    print(f"Figures written to {OUT}")


if __name__ == "__main__":
    main()
