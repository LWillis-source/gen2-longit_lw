"""Diet log vs stool detection per subject, with ingredients merged when sequencing cannot tell them apart.

Same figure as diet_vs_stool_timeseries.py, but the top 60 informative ingredients are collapsed
into one row per sequencing-resolvable taxon: ingredients are merged when they map to exactly the
same set of compatible ASVs in the same run (see stool_detection_timeseries.py), e.g. cow milk,
cheese, beef and yogurt (Bos taurus), or cabbage, broccoli, cauliflower and kale (Brassica
oleracea). Ingredients with no compatible ASV keep their own row.

Merged rows:
    diet panel   filled if any member ingredient is logged in that meal; solid if any member is stated
    stool panel  identical for all members (same ASVs); green if reads come from ASVs labelled with
                 the exact species of any member
    order        subject-days on which any member was logged (all subjects), most first

Row names are the taxon sequencing resolves the row to: the species when the run has ASVs labelled
with it, otherwise the genus (e.g. Capsicum, Theobroma).

Outputs (diet_log_analyses/figures_Diet-logs/Diet-vs-stool-grouped/)
    Diet-vs-stool-grouped-<subject>.png
    ingredient_groups.csv          group -> member ingredients, run, number of compatible ASVs

Usage (from the repository root):
    python diet_log_analyses/diet_vs_stool_grouped.py                    # top 60 informative ingredients
    python diet_log_analyses/diet_vs_stool_grouped.py --all-informative  # all 142 'Yes' ingredients; per subject,
                                                                       # only rows logged or detected
                                                                       # (-> Diet-vs-stool-grouped-all-informative/)
"""

from __future__ import annotations

import argparse

import pandas as pd

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import diet_log_ingredients as D
import diet_log_meal_timeseries as M
import diet_vs_stool_timeseries as V
import stool_detection_timeseries as S
from config import plt

OUT = D.OUT / "Diet-vs-stool-grouped"


#######################################
# Grouping
#######################################


def undetectable_taxon(species_field):
    """Taxon named by an ingredient with no compatible ASV: binomial, genus, or family ('Gadidae')."""
    parts = D.species_list(species_field)
    if len(parts) > 1:
        return D.display_species(species_field)
    words = D.clean_species(parts[0]).split()
    if words[0].endswith(("idae", "oideae", "aceae")):
        return words[0]
    if len(words) > 1 and words[1] not in ("spp.", "x") and words[1][0].islower():
        return f"{words[0]} {words[1]}"
    return f"{words[0]} spp."


def group_name(members, lexicon, n_exact, n_compatible):
    """Taxon a row resolves to: the species if the run has ASVs labelled with it, else the genus.

    Recipes (several species, e.g. kimchi) keep 'first species et al.'; undetectable ingredients
    (no compatible ASV) keep their own species name.
    """
    species = [D.species_list(lexicon.at[m, "species"]) for m in members]
    if n_compatible == 0:
        return undetectable_taxon(lexicon.at[members[0], "species"])
    if len(members) == 1 and len(species[0]) > 1:
        return D.display_species(lexicon.at[members[0], "species"])
    genus = S.parse_species(species[0][0])[0]
    binomials = {" ".join(D.clean_species(sp[0]).split()[:2]) for sp in species}
    if n_exact and len(binomials) == 1 and S.parse_species(species[0][0])[1]:
        return binomials.pop()
    return genus


def ingredient_groups(top, lexicon, runs):
    """Ingredient -> group, where a group is the set of ingredients with identical compatible ASVs."""
    keys, info = {}, {}
    for ing in top["ing"]:
        marker = lexicon.at[ing, "marker"]
        run = S.RUN_OF_MARKER[next(m.strip() for m in str(marker).split(";") if m.strip() in S.RUN_OF_MARKER)]
        allc, exact = S.compatible_asvs(lexicon.at[ing, "species"], runs[run].tax)
        # no compatible ASV: still merge ingredients naming the same taxon (squash, zucchini: Cucurbita pepo)
        key = (run, frozenset(allc)) if allc else ("none", undetectable_taxon(lexicon.at[ing, "species"]))
        keys.setdefault(key, []).append(ing)
        info[key] = (run, len(allc), max(len(exact), info.get(key, (0, 0, 0))[2]))  # members share ASVs
    rows = []
    for key, members in keys.items():
        name = group_name(members, lexicon, info[key][2], info[key][1])
        gid = members[0]  # group id = first member (most frequent), unique
        for m in members:
            rows.append({"ingredient": m, "group": gid, "taxon": name, "members": members,
                         "run": info[key][0], "n_compatible_ASVs": info[key][1],
                         "n_exact_species_ASVs": info[key][2]})
    return pd.DataFrame(rows)


def group_label(taxon, members):
    shown = ", ".join(members[:3]) + (f" +{len(members) - 3}" if len(members) > 3 else "")
    return f"$\\it{{{taxon.replace(' ', '~')}}}$ ({shown})"


def grouped_tables(cells, det, top, groups, entries):
    """Diet cells, stool detections and row table re-keyed from ingredient to group."""
    g_of = dict(zip(groups["ingredient"], groups["group"]))
    gcells = (cells.assign(ingredient=cells["ingredient"].map(g_of))
              .groupby(["Subject_ID", "Date", "meal", "ingredient"])["stated"].any().reset_index())
    gdet = det.assign(ingredient=det["ingredient"].map(g_of), species_ev=det["evidence"] == "species")
    agg = gdet.groupby(["Subject_ID", "Sample_ID", "ingredient"]).agg(detected=("detected", "any"),
                                                                       species_ev=("species_ev", "any"))
    first = gdet.drop_duplicates(["Subject_ID", "Sample_ID", "ingredient"]).set_index(
        ["Subject_ID", "Sample_ID", "ingredient"])
    gdet = first.drop(columns=["detected", "species_ev", "evidence"]).join(agg).reset_index()
    gdet["evidence"] = [("species" if s else "genus") if d else "" for d, s in zip(gdet["detected"], gdet["species_ev"])]

    # row order: subject-days on which any member was logged (all subjects)
    long = D.split_ingredients(entries)
    long = long[long["ing"].isin(g_of)]
    days = long.assign(group=long["ing"].map(g_of)).drop_duplicates(["group", "Day_key"]).groupby("group").size()
    first_rank = {g: i for i, g in enumerate(dict.fromkeys(groups["group"]))}
    gtop = groups.drop_duplicates("group").copy()
    gtop["subject_days"] = gtop["group"].map(days)
    gtop["_rank"] = gtop["group"].map(first_rank)
    level = dict(zip(top["ing"], top["label_level"]))
    gtop["label_level"] = [max(level[m] for m in ms) for ms in gtop["members"]]
    gtop = gtop.sort_values(["subject_days", "_rank"], ascending=[False, True]).reset_index(drop=True)
    gtop = gtop.rename(columns={"group": "ing"})
    labels = [group_label(t, ms) for t, ms in zip(gtop["taxon"], gtop["members"])]
    return gcells, gdet, gtop, labels


#######################################
# Run
#######################################


def subject_rows(sid_txt, sid, gcells, gdet, gtop, labels):
    """Rows the subject logged (any meal) or had detected in stool, in the global row order."""
    eaten = set(gcells.loc[gcells["Subject_ID"] == sid, "ingredient"])
    detected = set(gdet.loc[(gdet["Subject_ID"] == sid_txt) & gdet["detected"], "ingredient"])
    keep = gtop["ing"].isin(eaten | detected).to_numpy()
    return gtop[keep].reset_index(drop=True), [l for l, k in zip(labels, keep) if k]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all-informative", action="store_true",
                        help="use all ingredients rated 'Yes' (not only the top 60) and show, per subject, only "
                             "rows that were logged or detected")
    args = parser.parse_args()
    top_n = None if args.all_informative else M.TOP_N
    out = OUT.with_name(OUT.name + "-all-informative") if args.all_informative else OUT
    prefix = "Diet-vs-stool-grouped-all" if args.all_informative else "Diet-vs-stool-grouped"

    cells, top, entries, _ = M.presence_table(top_n)
    days = M.study_days(entries)
    _, lexicon = D.read_coding()
    runs = S.load_runs()
    det = S.detection_table(runs, top, lexicon)
    groups = ingredient_groups(top, lexicon, runs)
    gcells, gdet, gtop, labels = grouped_tables(cells, det, top, groups, entries)
    which = "all informative ingredients" if args.all_informative else f"top {M.TOP_N} informative ingredients"

    out.mkdir(parents=True, exist_ok=True)
    (groups.assign(members=groups["members"].map(", ".join)).drop_duplicates("group")
     .drop(columns="ingredient").to_csv(out / "ingredient_groups.csv", index=False))
    n = 0
    for sid in sorted(days):
        sid_txt = f"{int(sid):02d}"
        if not (gdet["Subject_ID"] == sid_txt).any():
            continue
        rows, row_labels = gtop, labels
        if args.all_informative:
            rows, row_labels = subject_rows(sid_txt, sid, gcells, gdet, gtop, labels)
        title = (f"{len(rows)} of {len(gtop)} sequencing-resolvable taxa logged or detected ({which} merged)"
                 if args.all_informative else f"{len(gtop)} sequencing-resolvable taxa ({which} merged)")
        V.plot_subject(sid, days[sid], gcells, gdet, rows, out / f"{prefix}-{sid_txt}.png", labels=row_labels,
                       title_rows=title)
        n += 1
    merged = groups.drop_duplicates("group")
    print(f"{len(top)} ingredients -> {len(gtop)} rows; merged groups: {sum(len(m) > 1 for m in merged['members'])}")
    for t, ms in zip(merged["taxon"], merged["members"]):
        if len(ms) > 1:
            print(f"  {t}: {', '.join(ms)}")
    print(f"{n} subjects plotted to {out}")


if __name__ == "__main__":
    main()
