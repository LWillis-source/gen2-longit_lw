"""Per-subject confusion matrices: diet log vs stool sequencing, per sequencing-resolvable taxon.

Unit: one subject x one taxon row of the all-informative grouped table (diet_vs_stool_grouped.py:
the 142 ingredients rated 'Yes' for sequencing, merged when sequencing cannot tell them apart).
Taxa with no compatible ASV in either run are left out, since sequencing cannot report them.

    truth (diet log)    the subject logged the taxon on any day (stated or assumed)
    prediction (stool)  compatible ASVs >= 0.1% of reads in at least one of the subject's stool
                        samples (samples with < 500 reads in that run are not used)

    TP logged & detected   FP detected, not logged   FN logged, not detected   TN neither
    precision = TP / (TP + FP)   recall = TP / (TP + FN)   accuracy = (TP + TN) / taxa

Presence is pooled over the whole study, ignoring timing (a stool collected before the diet log
started can still count as a detection).

Outputs (diet_log_analyses/figures_Diet-logs/Confusion/)
    confusion_matrices.png       2x2 matrix per subject
    precision_recall_accuracy.png the three metrics against subject
    confusion_per_subject.csv    counts and metrics per subject
    taxon_calls_per_subject.csv  one row per subject x taxon (logged, detected, call)

Usage (from the repository root):
    python diet_log_analyses/diet_stool_confusion.py                         # detection at >= 0.1% of reads
    python diet_log_analyses/diet_stool_confusion.py --detection-min 0.01    # >= 1%, outputs named *_1pct
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import diet_log_ingredients as D
import diet_log_meal_timeseries as M
import diet_vs_stool_grouped as G
import stool_detection_timeseries as S
from config import plt

OUT = D.OUT / "Confusion"
METRIC_COLOURS = {"precision": "#2878D6", "recall": "#E08A00", "accuracy": "#444444"}
METRIC_MARKERS = {"precision": "o", "recall": "s", "accuracy": "D"}


def taxon_calls():
    """One row per subject x detectable taxon with logged / detected flags."""
    cells, top, entries, _ = M.presence_table(None)
    _, lexicon = D.read_coding()
    runs = S.load_runs()
    det = S.detection_table(runs, top, lexicon)
    groups = G.ingredient_groups(top, lexicon, runs)
    gcells, gdet, gtop, _ = G.grouped_tables(cells, det, top, groups, entries)
    taxa = gtop[gtop["n_compatible_ASVs"] > 0][["ing", "taxon", "members"]]

    subjects = sorted(entries["Subject_ID"].unique())
    rows = []
    for sid in subjects:
        sid_txt = f"{int(sid):02d}"
        d = gdet[(gdet["Subject_ID"] == sid_txt) & ~gdet["low_reads"]]
        if d.empty:
            continue
        logged = set(gcells.loc[gcells["Subject_ID"] == sid, "ingredient"])
        detected = set(d.loc[d["detected"], "ingredient"])
        for t in taxa.itertuples(index=False):
            lo, de = t.ing in logged, t.ing in detected
            rows.append({"Subject_ID": sid_txt, "taxon": t.taxon, "ingredients": ", ".join(t.members),
                         "logged": lo, "detected": de,
                         "call": "TP" if lo and de else "FP" if de else "FN" if lo else "TN",
                         "n_stool_samples": d["Sample_ID"].nunique()})
    return pd.DataFrame(rows)


#######################################
# Genus -> family
#######################################

FAMILY_CACHE = D.C.DATA_DIR / "genus_family_gbif.csv"


def genus_families(genera_by_run, runs):
    """Family of each genus: meat genera from the meat feature_data.txt, plant genera from the GBIF
    backbone (looked up once and cached in 1-data/genus_family_gbif.csv; edit that file to override)."""
    import json
    import urllib.parse
    import urllib.request

    fam = {}
    meat_tax = runs["meat"].tax.dropna(subset=["Genus", "Family"])
    meat_fam = meat_tax.groupby("Genus")["Family"].agg(lambda f: f.value_counts().index[0])
    for g in genera_by_run.get("meat", set()):
        fam[("meat", g)] = meat_fam.get(g, g)

    cache = pd.read_csv(FAMILY_CACHE) if FAMILY_CACHE.exists() else pd.DataFrame(
        columns=["genus", "family", "order", "matchType", "status"])
    known = dict(zip(cache["genus"], cache["family"]))
    new_rows = []
    for g in sorted(genera_by_run.get("plants", set()) - set(known)):
        url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode(
            {"name": g, "rank": "GENUS", "kingdom": "Plantae"})
        with urllib.request.urlopen(url, timeout=20) as r:
            d = json.load(r)
        new_rows.append({"genus": g, "family": d.get("family") or g, "order": d.get("order"),
                         "matchType": d.get("matchType"), "status": d.get("status")})
        known[g] = new_rows[-1]["family"]
    if new_rows:
        pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True).sort_values("genus").to_csv(
            FAMILY_CACHE, index=False)
    for g in genera_by_run.get("plants", set()):
        fam[("plants", g)] = known[g]
    return fam


#######################################
# Option 1: merge rows whose compatible ASVs overlap
#######################################


def overlap_rows(top, lexicon, runs, level="genus"):
    """Rows built by merging ingredient components whose compatible ASV sets overlap.

    level="family" additionally merges components (same run) whose genera belong to the same family,
    e.g. Solanum + Capsicum -> Solanaceae; such rows are named after the family.

    Each ingredient is split into its species (a recipe such as kimchi gives one component per
    species). Components in the same run that share any compatible ASV are merged, transitively
    (union-find), so e.g. all Brassica rows that share unlabelled Brassica ASVs become one row.
    Returns (rows, ing_to_rows): rows has taxon, ASV set, member ingredients; ing_to_rows maps an
    ingredient to the rows its components fall into.
    """
    nodes = []
    for ing in top["ing"]:
        marker = lexicon.at[ing, "marker"]
        run = S.RUN_OF_MARKER[next(m.strip() for m in str(marker).split(";") if m.strip() in S.RUN_OF_MARKER)]
        for sp in D.species_list(lexicon.at[ing, "species"]):
            allc, exact = S.compatible_asvs(sp, runs[run].tax)
            if allc:
                nodes.append({"ing": ing, "species": sp, "run": run, "asvs": allc, "exact": exact})

    parent = list(range(len(nodes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i]["run"] == nodes[j]["run"] and nodes[i]["asvs"] & nodes[j]["asvs"]:
                parent[find(i)] = find(j)

    family = {}
    if level == "family":
        genera_by_run = {}
        for n in nodes:
            genera_by_run.setdefault(n["run"], set()).add(S.parse_species(n["species"])[0])
        family = genus_families(genera_by_run, runs)
        by_family = {}
        for i, n in enumerate(nodes):
            key = (n["run"], family[(n["run"], S.parse_species(n["species"])[0])])
            if key in by_family:
                parent[find(i)] = find(by_family[key])
            else:
                by_family[key] = i

    comps = {}
    for i, n in enumerate(nodes):
        comps.setdefault(find(i), []).append(n)
    rows, ing_to_rows = [], {}
    for k, members in comps.items():
        asvs = set().union(*(m["asvs"] for m in members))
        exact = set().union(*(m["exact"] for m in members))
        genera = {S.parse_species(m["species"])[0] for m in members}
        binomials = {" ".join(D.clean_species(m["species"]).split()[:2]) for m in members}
        overlaps = len(members) > 1 and len(binomials) > 1
        if not overlaps and exact and S.parse_species(members[0]["species"])[1]:
            taxon = binomials.pop()
        elif len(genera) > 1 and family:
            taxon = family[(members[0]["run"], next(iter(genera)))]
        else:
            taxon = "/".join(sorted(genera))
        ings = list(dict.fromkeys(m["ing"] for m in members))
        rows.append({"row": k, "taxon": taxon, "run": members[0]["run"], "asvs": asvs, "exact": exact,
                     "ingredients": ings})
        for ing in ings:
            ing_to_rows.setdefault(ing, set()).add(k)
    return pd.DataFrame(rows), ing_to_rows


def taxon_calls_merged(level="genus"):
    """Like taxon_calls(), with rows from overlap_rows() and detection recomputed per merged row."""
    cells, top, entries, _ = M.presence_table(None)
    _, lexicon = D.read_coding()
    runs = S.load_runs()
    rows, ing_to_rows = overlap_rows(top, lexicon, runs, level)
    stools = {run: S.stool_samples(ps) for run, ps in runs.items()}

    # fraction of each stool sample's reads in each row's ASVs
    frac = {}
    for r in rows.itertuples(index=False):
        ps, st = runs[r.run], stools[r.run]
        st = st[st["total_reads"] >= S.MIN_READS]
        reads = ps.otu.loc[st.index, sorted(r.asvs)].sum(axis=1)
        frac[r.row] = (reads / st["total_reads"]).groupby(st["Subject_ID"]).max()  # best sample per subject

    out = []
    for sid in sorted(entries["Subject_ID"].unique()):
        sid_txt = f"{int(sid):02d}"
        logged_ings = set(cells.loc[cells["Subject_ID"] == sid, "ingredient"])
        logged = set().union(*(ing_to_rows.get(i, set()) for i in logged_ings))
        n_samples = len({s for run in stools for s in
                         stools[run][(stools[run]["Subject_ID"] == sid_txt)
                                     & (stools[run]["total_reads"] >= S.MIN_READS)]["Sample_ID"]})
        if not n_samples:
            continue
        for r in rows.itertuples(index=False):
            lo = r.row in logged
            de = bool(frac[r.row].get(sid_txt, 0) >= S.DETECTION_MIN)
            out.append({"Subject_ID": sid_txt, "taxon": r.taxon, "ingredients": ", ".join(r.ingredients),
                        "logged": lo, "detected": de,
                        "call": "TP" if lo and de else "FP" if de else "FN" if lo else "TN",
                        "n_stool_samples": n_samples})
    return pd.DataFrame(out), rows


def confusion(calls):
    counts = calls.pivot_table(index="Subject_ID", columns="call", values="taxon", aggfunc="count", fill_value=0)
    counts = counts.reindex(columns=["TP", "FP", "FN", "TN"], fill_value=0)
    counts["n_taxa"] = counts.sum(axis=1)
    counts["n_stool_samples"] = calls.groupby("Subject_ID")["n_stool_samples"].first()
    with np.errstate(invalid="ignore", divide="ignore"):
        counts["precision"] = counts["TP"] / (counts["TP"] + counts["FP"])
        counts["recall"] = counts["TP"] / (counts["TP"] + counts["FN"])
    counts["accuracy"] = (counts["TP"] + counts["TN"]) / counts["n_taxa"]
    return counts.reset_index()


def plot_matrices(conf, path):
    n = len(conf)
    ncol = 5
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.1 * ncol, 2.2 * nrow + 0.9), facecolor=D.BACKGROUND)
    fig.subplots_adjust(left=0.05, right=0.98, top=1 - 0.75 / (2.2 * nrow + 0.9), bottom=0.06, wspace=0.45,
                        hspace=0.6)
    vmax = conf[["TP", "FP", "FN", "TN"]].to_numpy().max()
    for ax, r in zip(axes.flat, conf.itertuples(index=False)):
        m = np.array([[r.TP, r.FN], [r.FP, r.TN]])  # rows: diet logged yes/no; cols: stool detected yes/no
        ax.imshow(m, cmap=D.C.GRADIENT_WHITE_BLUE, vmin=0, vmax=vmax)
        for (i, j), v in np.ndenumerate(m):
            name = [["TP", "FN"], ["FP", "TN"]][i][j]
            ax.text(j, i, f"{name}\n{v}", ha="center", va="center", fontsize=8,
                    color="white" if v > 0.6 * vmax else "#222222")
        ax.set_xticks([0, 1], ["detected", "not det."], fontsize=6.5)
        ax.set_yticks([0, 1], ["logged", "not logged"], fontsize=6.5)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(f"Subject {r.Subject_ID}  (n stool = {r.n_stool_samples})", fontsize=7.5)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    fig.text(0.02, 1 - 0.12 / (2.2 * nrow + 0.9),
             f"Diet log vs stool sequencing: confusion matrix per subject ({int(conf['n_taxa'].iloc[0])} detectable "
             "taxa)", fontsize=11, fontweight="bold", va="top")
    fig.text(0.02, 1 - 0.38 / (2.2 * nrow + 0.9),
             "Rows: taxon logged in the diet (any day). Columns: detected in at least one stool sample "
             f"(compatible ASVs ≥ {S.DETECTION_MIN:.1%} of reads).", fontsize=8, color=D.TEXT, va="top")
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


def plot_metrics(conf, path):
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=D.BACKGROUND)
    fig.subplots_adjust(left=0.08, right=0.8, top=0.82, bottom=0.14)
    ax.set_facecolor(D.BACKGROUND)
    x = np.arange(len(conf))
    for k, metric in enumerate(["precision", "recall", "accuracy"]):
        vals = conf[metric].to_numpy()
        ax.plot(x + (k - 1) * 0.12, vals, linestyle="none", marker=METRIC_MARKERS[metric], markersize=6,
                color=METRIC_COLOURS[metric], label=f"{metric.capitalize()}  (mean {np.nanmean(vals):.2f})")
        ax.axhline(np.nanmean(vals), color=METRIC_COLOURS[metric], linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xticks(x, conf["Subject_ID"])
    ax.set_xlabel("Subject", color=D.TEXT)
    ax.set_ylabel("Score", color=D.TEXT)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(-0.6, len(conf) - 0.4)
    ax.grid(axis="y", color="#E3E3E3", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=D.TEXT)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8.5)
    fig.text(0.08, 0.95, "Diet log vs stool sequencing: precision, recall and accuracy per subject",
             fontsize=11, fontweight="bold", va="top")
    fig.text(0.08, 0.89, f"{int(conf['n_taxa'].iloc[0])} detectable taxa per subject; detected = compatible ASVs "
             f"≥ {S.DETECTION_MIN:.1%} of reads in a stool sample; presence pooled over the study. "
             "Dashed lines: mean across subjects.", fontsize=8, color=D.TEXT, va="top")
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--detection-min", type=float, default=S.DETECTION_MIN,
                        help="fraction of a stool sample's reads needed to call a taxon detected "
                             f"(default {S.DETECTION_MIN}); other values add a suffix such as _1pct to the outputs")
    parser.add_argument("--merge-overlapping", action="store_true",
                        help="merge taxon rows whose compatible ASVs overlap (e.g. all Brassica rows), splitting "
                             "recipes such as kimchi into their species; outputs get the suffix _overlap-merged")
    parser.add_argument("--merge-level", choices=["genus", "family"], default="genus",
                        help="with --merge-overlapping: also merge taxa of the same family "
                             "(outputs get the suffix _family-merged)")
    args = parser.parse_args()
    S.DETECTION_MIN = args.detection_min  # read by S.detection_table
    suffix = "" if args.detection_min == 1e-3 else "_" + f"{args.detection_min * 100:g}".replace(".", "p") + "pct"
    if args.merge_overlapping:
        suffix = ("_family-merged" if args.merge_level == "family" else "_overlap-merged") + suffix

    if args.merge_overlapping:
        calls, rows = taxon_calls_merged(args.merge_level)
        OUT.mkdir(parents=True, exist_ok=True)
        (rows.assign(n_ASVs=rows["asvs"].map(len), n_exact_species_ASVs=rows["exact"].map(len),
                     ingredients=rows["ingredients"].map(", ".join))
         .drop(columns=["row", "asvs", "exact"]).to_csv(OUT / f"merged_rows{suffix}.csv", index=False))
    else:
        calls = taxon_calls()
    conf = confusion(calls)
    OUT.mkdir(parents=True, exist_ok=True)
    calls.to_csv(OUT / f"taxon_calls_per_subject{suffix}.csv", index=False)
    conf.to_csv(OUT / f"confusion_per_subject{suffix}.csv", index=False)
    plot_matrices(conf, OUT / f"confusion_matrices{suffix}.png")
    plot_metrics(conf, OUT / f"precision_recall_accuracy{suffix}.png")
    pd.set_option("display.width", 140)
    print(conf.round(2).to_string(index=False))
    print(f"Figures written to {OUT}")


if __name__ == "__main__":
    main()
