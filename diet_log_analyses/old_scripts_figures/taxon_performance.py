"""Precision, recall and accuracy per taxon: diet log vs stool sequencing, across subjects.

Rows are the overlap-merged, sequencing-resolvable taxa (diet_stool_confusion.py
--merge-overlapping). For each taxon every subject is one case:
    TP logged & detected   FP detected, not logged   FN logged, not detected   TN neither
    (logged = any day of the diet log; detected = compatible ASVs >= the cutoff share of reads in at
    least one of the subject's stool samples)
    precision = TP / (TP + FP)   recall = TP / (TP + FN)   accuracy = (TP + TN) / subjects

Taxa shown: the 60 most frequently logged detectable taxa (subject-days, merged_taxa_frequency.py);
taxa with no compatible ASV are left out because sequencing cannot report them.

Outputs (diet_log_analyses/figures_Diet-logs/Confusion/)
    taxon_performance_top60_overlap-merged[_1pct].png
    taxon_performance_overlap-merged[_1pct].csv     all detectable taxa

Usage (from the repository root):
    python diet_log_analyses/taxon_performance.py                       # detection at >= 0.1% of reads
    python diet_log_analyses/taxon_performance.py --detection-min 0.01  # >= 1%
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import diet_log_ingredients as D
import diet_stool_confusion as CF
import merged_taxa_frequency as MF
import stool_detection_timeseries as S
from config import plt

TOP_N = 60


def per_taxon(calls):
    c = calls.pivot_table(index="taxon", columns="call", values="Subject_ID", aggfunc="count", fill_value=0)
    c = c.reindex(columns=["TP", "FP", "FN", "TN"], fill_value=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        c["precision"] = c["TP"] / (c["TP"] + c["FP"])
        c["recall"] = c["TP"] / (c["TP"] + c["FN"])
    c["accuracy"] = (c["TP"] + c["TN"]) / c[["TP", "FP", "FN", "TN"]].sum(axis=1)
    c["subjects_logged"] = c["TP"] + c["FN"]
    c["subjects_detected"] = c["TP"] + c["FP"]
    return c.reset_index()


def plot(perf, labels, path):
    n = len(perf)
    height = 0.24 * n + 2.6
    fig = plt.figure(figsize=(10, height), facecolor=D.BACKGROUND)
    left = 0.04 + max(len(l) for l in labels) * 0.0062
    ax = fig.add_axes([left, 1.3 / height, 0.78 - left, 1 - 2.25 / height], facecolor=D.BACKGROUND)
    y = np.arange(n)
    for k, metric in enumerate(["precision", "recall", "accuracy"]):
        ax.plot(perf[metric], y + (k - 1) * 0.22, linestyle="none", marker=CF.METRIC_MARKERS[metric],
                markersize=5, color=CF.METRIC_COLOURS[metric],
                label=f"{metric.capitalize()}  (mean {np.nanmean(perf[metric]):.2f})")
    for i, r in enumerate(perf.itertuples(index=False)):
        ax.text(1.06, i, f"{r.subjects_logged} logged / {r.subjects_detected} detected  (TP {r.TP})",
                va="center", fontsize=7, color=D.TEXT, transform=ax.get_yaxis_transform())
    ax.set_yticks(y, labels, fontsize=8)
    for tick in ax.get_yticklabels():
        tick.set_color(D.TEXT)
    ax.invert_yaxis()
    ax.set_ylim(n - 0.4, -0.6)
    ax.set_xlim(-0.04, 1.04)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xlabel("Score (across 19 subjects)", color=D.TEXT)
    ax.grid(axis="x", color="#E3E3E3", linewidth=0.8)
    for i in range(0, n, 2):
        ax.axhspan(i - 0.5, i + 0.5, color="#F3F3F0", zorder=0)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=D.TEXT)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -1.0 / (height - 2.25)), ncol=3, frameon=False, fontsize=8.5)
    fig.text(0.02, 1 - 0.2 / height,
             f"Diet log vs stool sequencing per taxon: top {n} most frequently logged detectable taxa",
             fontsize=12, fontweight="bold", va="top")
    fig.text(0.02, 1 - 0.48 / height,
             "Each subject is one case per taxon: logged on any day vs detected in any stool sample (compatible ASVs "
             f"≥ {S.DETECTION_MIN:.1%} of reads).\nRows ordered by subject-days logged; taxa merged when their "
             "ASVs overlap. No precision dot = never detected (precision undefined).", fontsize=8, color=D.TEXT, va="top")
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--detection-min", type=float, default=S.DETECTION_MIN)
    parser.add_argument("--merge-level", choices=["genus", "family"], default="genus",
                        help="also merge taxa of the same family (outputs named *_family-merged*)")
    args = parser.parse_args()
    S.DETECTION_MIN = args.detection_min
    suffix = ("_family-merged" if args.merge_level == "family" else "_overlap-merged") + ("" if args.detection_min == 1e-3
                                  else "_" + f"{args.detection_min * 100:g}".replace(".", "p") + "pct")

    calls, _ = CF.taxon_calls_merged(args.merge_level)
    perf = per_taxon(calls)

    # frequency order and member lists from the merged-taxa frequency table
    longrows, info = MF.merged_rows_table(args.merge_level)
    freq = D.frequency(longrows, "row")
    freq["taxon"] = freq["row"].map(lambda k: info[k]["taxon"])
    assert freq["taxon"].is_unique, "merged taxon names must be unique to join the tables"
    ing_days = longrows.drop_duplicates(["ing", "Day_key"]).groupby("ing").size()
    members = (longrows.drop_duplicates(["row", "ing"]).assign(days=lambda d: d["ing"].map(ing_days))
               .sort_values(["row", "days", "ing"], ascending=[True, False, True]).groupby("row")["ing"].agg(list))
    freq["members"] = freq["row"].map(members)

    perf = freq[["taxon", "subject_days", "members"]].merge(perf, on="taxon", how="inner")  # detectable only
    perf.assign(members=perf["members"].map(", ".join)).to_csv(CF.OUT / f"taxon_performance{suffix}.csv",
                                                              index=False)
    top = perf.head(TOP_N).reset_index(drop=True)
    labels = [MF.label_for(t, m) for t, m in zip(top["taxon"], top["members"])]
    plot(top, labels, CF.OUT / f"taxon_performance_top{TOP_N}{suffix}.png")
    print(top[["taxon", "subject_days", "TP", "FP", "FN", "TN", "precision", "recall", "accuracy"]]
          .round(2).head(15).to_string(index=False))
    print(f"Means over top {TOP_N}: " + ", ".join(f"{m} {np.nanmean(top[m]):.2f}" for m in
                                                  ["precision", "recall", "accuracy"]))


if __name__ == "__main__":
    main()
