"""Does timing help? Diet log vs stool sequencing with a 12 h - 3 day transit window.

Rows: the genus-level merged taxa of diet_stool_confusion.py --merge-overlapping (ingredients rated
'Yes' for sequencing, split into species, merged when their compatible ASVs overlap).

Unit: one stool sample x one taxon.
    detected        compatible ASVs >= the cutoff share of the sample's reads
    eaten (timed)   the taxon was logged between WINDOW_MAX and WINDOW_MIN before collection
    eaten (pooled)  the taxon was logged at any time in the subject's diet log (the earlier analysis,
                    re-scored on the same stool samples so that only the timing differs)

When food was eaten:
    a logged clock time ('6:30pm') as parsed in diet_log_meal_timeseries.py; else a meal word at a
    typical time (breakfast 08:00, lunch 12:30, dinner 19:00); else 12:00 on the logged day.
Stool samples used: collection date known (time missing -> 12:00), >= 500 reads in that run, and the
whole window inside the subject's logged days (00:00 of the first day to 24:00 of the last), so that
nothing eaten in the window can be missing from the log.

Outputs (diet_log_analyses/figures_Diet-logs/Timing/)
    timing_vs_pooled_per_subject[_1pct].png   precision, recall, accuracy per subject, both truths
    timing_windows[_1pct].png                 detection vs time since last eaten; scores for other windows
                                              (samples with 5 days of log before them)
    timing_confusion_per_subject[_1pct].csv
    timing_calls[_1pct].csv                   one row per stool sample x taxon

Usage (from the repository root):
    python diet_log_analyses/diet_stool_timing.py                       # detection at >= 0.1% of reads
    python diet_log_analyses/diet_stool_timing.py --detection-min 0.01  # >= 1%
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import diet_log_ingredients as D
import diet_log_meal_timeseries as M
import diet_stool_confusion as CF
import stool_detection_timeseries as S
from config import plt

OUT = D.OUT / "Timing"
WINDOW_MIN, WINDOW_MAX = pd.Timedelta(hours=12), pd.Timedelta(days=3)
YEAR = 2025
MEAL_TIME = {"Breakfast": 8 * 60, "Lunch": 12 * 60 + 30, "Dinner": 19 * 60}
DEFAULT_MINUTES = 12 * 60


def to_datetime(mmdd, minutes):
    return pd.Timestamp(f"{YEAR}-{mmdd}") + pd.Timedelta(minutes=float(minutes))


def diet_events(entries, top, lexicon, ing_to_rows):
    """One row per (subject, eaten-at time, taxon row) from the coded food entries."""
    meals, _ = M.assign_meals(entries)
    long = D.split_ingredients(entries)
    long["Entry_no"] = long["entry"].map(lambda e: e[1])
    long = long.merge(meals, on=["Day_key", "Entry_no"], how="left")
    long = long[long["ing"].isin(set(top["ing"]))]
    minutes = long["minutes"].where(long["minutes"].notna(), long["meal"].map(MEAL_TIME)).fillna(DEFAULT_MINUTES)
    long["eaten_at"] = [to_datetime(dk.split("_")[1], m) for dk, m in zip(long["Day_key"], minutes)]
    long["timing"] = np.where(long["minutes"].notna(), "clock time",
                              np.where(long["meal"].isin(MEAL_TIME), "meal word", "day only"))
    rows = [{"Subject_ID": f"{int(r.Subject_ID):02d}", "eaten_at": r.eaten_at, "row": k, "timing": r.timing}
            for r in long.itertuples(index=False) for k in ing_to_rows.get(r.ing, ())]
    return pd.DataFrame(rows)


def timed_calls(lookback=WINDOW_MAX, window=(WINDOW_MIN, WINDOW_MAX)):
    """Stool sample x taxon calls. Samples are kept only if `lookback` before collection is inside the log;
    'eaten_window' uses `window` = (min, max) time before collection; 'hours' lists every logged
    consumption of the taxon before collection (hours before), for other windows."""
    cells, top, entries, _ = M.presence_table(None)
    _, lexicon = D.read_coding()
    runs = S.load_runs()
    rows, ing_to_rows = CF.overlap_rows(top, lexicon, runs)
    events = diet_events(entries, top, lexicon, ing_to_rows)
    days = M.study_days(entries)
    span = {f"{int(sid):02d}": (to_datetime(ds[0][0], 0), to_datetime(ds[-1][0], 24 * 60)) for sid, ds in days.items()}

    out, skipped = [], []
    for run, ps in runs.items():
        st = S.stool_samples(ps)
        st = st[st["total_reads"] >= S.MIN_READS]
        run_rows = rows[rows["run"] == run]
        for sample, smp in st.iterrows():
            sid = smp["Subject_ID"]
            if sid not in span:
                continue
            if not isinstance(smp["date"], str):
                skipped.append((sid, smp["Sample_ID"], "no collection date"))
                continue
            t = to_datetime(smp["date"], int(smp["time"][:2]) * 60 + int(smp["time"][3:]) if isinstance(
                smp["time"], str) else DEFAULT_MINUTES)
            lo, hi = t - window[1], t - window[0]
            if t - lookback < span[sid][0] or hi > span[sid][1]:
                skipped.append((sid, smp["Sample_ID"], "window outside logged days"))
                continue
            ev = events[events["Subject_ID"] == sid]
            in_window = set(ev.loc[(ev["eaten_at"] >= lo) & (ev["eaten_at"] <= hi), "row"])
            ever = set(ev["row"])
            before = ev[ev["eaten_at"] <= t]
            hours = ((t - before["eaten_at"]).dt.total_seconds() / 3600).groupby(before["row"]).agg(list)
            counts = ps.otu.loc[sample]
            for r in run_rows.itertuples(index=False):
                frac = counts[sorted(r.asvs)].sum() / smp["total_reads"]
                out.append({"Subject_ID": sid, "Sample_ID": smp["Sample_ID"], "collected": t, "run": run,
                            "taxon": r.taxon, "detected": frac >= S.DETECTION_MIN, "rel_abundance": frac,
                            "eaten_window": r.row in in_window, "eaten_any": r.row in ever,
                            "hours_before": hours.get(r.row, [])})
    calls = pd.DataFrame(out)
    for truth in ["window", "any"]:
        e, d = calls[f"eaten_{truth}"], calls["detected"]
        calls[f"call_{truth}"] = np.select([e & d, d, e], ["TP", "FP", "FN"], "TN")
    sk = pd.DataFrame(skipped, columns=["Subject_ID", "Sample_ID", "reason"]).drop_duplicates()
    return calls, sk, events


def confusion_by(calls, truth, by="Subject_ID"):
    c = calls.pivot_table(index=by, columns=f"call_{truth}", values="taxon", aggfunc="count", fill_value=0)
    c = c.reindex(columns=["TP", "FP", "FN", "TN"], fill_value=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        c["precision"] = c["TP"] / (c["TP"] + c["FP"])
        c["recall"] = c["TP"] / (c["TP"] + c["FN"])
    c["accuracy"] = (c["TP"] + c["TN"]) / c[["TP", "FP", "FN", "TN"]].sum(axis=1)
    c["n_stool_samples"] = calls.groupby(by)["Sample_ID"].nunique()
    return c


def plot(conf_w, conf_a, path, n_samples, n_subjects):
    subjects = conf_w.index.tolist()
    x = np.arange(len(subjects))
    fig, axes = plt.subplots(3, 1, figsize=(10, 8.2), sharex=True, facecolor=D.BACKGROUND)
    fig.subplots_adjust(left=0.08, right=0.7, top=0.86, bottom=0.08, hspace=0.18)
    for ax, metric in zip(axes, ["precision", "recall", "accuracy"]):
        ax.set_facecolor(D.BACKGROUND)
        col = CF.METRIC_COLOURS[metric]
        a, w = conf_a[metric].to_numpy(), conf_w[metric].to_numpy()
        for xi, ai, wi in zip(x, a, w):
            ax.plot([xi, xi], [ai, wi], color="#BBBBBB", linewidth=1, zorder=1)
        ax.plot(x, a, linestyle="none", marker=CF.METRIC_MARKERS[metric], markersize=6, markerfacecolor="white",
                markeredgecolor=col, label=f"any time in log (mean {np.nanmean(a):.2f})", zorder=2)
        ax.plot(x, w, linestyle="none", marker=CF.METRIC_MARKERS[metric], markersize=6, color=col,
                label=f"12 h - 3 d before stool (mean {np.nanmean(w):.2f})", zorder=3)
        ax.set_ylim(0, 1.02)
        ax.set_ylabel(metric.capitalize(), color=D.TEXT)
        ax.grid(axis="y", color="#E3E3E3", linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(colors=D.TEXT)
        ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8)
    labels = [f"{s}\n(n={int(n)})" for s, n in zip(subjects, conf_w["n_stool_samples"])]
    axes[-1].set_xticks(x, labels, fontsize=8)
    axes[-1].set_xlabel("Subject (n = stool samples used)", color=D.TEXT)
    fig.text(0.08, 0.97, "Does timing help? Diet log vs stool sequencing per subject", fontsize=12,
             fontweight="bold", va="top")
    fig.text(0.08, 0.935,
             f"Unit: stool sample x taxon ({n_samples} stool samples, {n_subjects} subjects). Detected = compatible ASVs "
             f"≥ {S.DETECTION_MIN:.1%} of reads. Filled: eaten 12 h - 3 d before collection; open: eaten at any\n"
             "time in the log (same samples). Untimed entries placed at a typical meal time or 12:00.",
             fontsize=8, color=D.TEXT, va="top")
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


#######################################
# Detection vs time since eaten, and window comparison
#######################################

SINCE_BINS = [(0, 12, "0-12 h"), (12, 24, "12-24 h"), (24, 48, "1-2 d"), (48, 72, "2-3 d"), (72, 120, "3-5 d"),
              (120, 1e9, "> 5 d")]
WINDOWS = [(0, 12, "0-12 h"), (12, 24, "12 h-1 d"), (12, 48, "12 h-2 d"), (12, 72, "12 h-3 d"), (12, 120, "12 h-5 d"),
           (0, 120, "0-5 d"), (0, 1e9, "any time")]


def detection_by_time_since(calls):
    since = calls["hours_before"].map(lambda h: min(h) if h else np.nan)
    lab = pd.Series("not eaten before", index=calls.index)
    for lo, hi, name in SINCE_BINS:
        lab[(since >= lo) & (since < hi)] = name
    order = [b[2] for b in SINCE_BINS] + ["not eaten before"]
    return calls.groupby(lab)["detected"].agg(n="size", rate="mean").reindex(order)


def window_scores(calls):
    rows = []
    for lo, hi, name in WINDOWS:
        eaten = calls["hours_before"].map(lambda h: any(lo <= x <= hi for x in h))
        d = calls["detected"]
        tp, fp, fn = (eaten & d).sum(), (~eaten & d).sum(), (eaten & ~d).sum()
        tn = len(calls) - tp - fp - fn
        per = pd.DataFrame({"s": calls["Subject_ID"], "e": eaten, "d": d}).groupby("s").apply(
            lambda g: pd.Series({"p": (g.e & g.d).sum() / max(g.d.sum(), 1) if g.d.sum() else np.nan,
                                 "r": (g.e & g.d).sum() / g.e.sum() if g.e.sum() else np.nan,
                                 "a": ((g.e & g.d) | (~g.e & ~g.d)).mean()}), include_groups=False)
        rows.append({"window": name, "TP": tp, "FP": fp, "FN": fn, "TN": tn,
                     "precision": tp / (tp + fp), "recall": tp / (tp + fn), "accuracy": (tp + tn) / len(calls),
                     "precision_subject_mean": per["p"].mean(), "recall_subject_mean": per["r"].mean(),
                     "accuracy_subject_mean": per["a"].mean()})
    return pd.DataFrame(rows)


def plot_time_and_windows(since, scores, path, n_samples):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=D.BACKGROUND,
                                 gridspec_kw={"width_ratios": [1, 1.25]})
    fig.subplots_adjust(left=0.06, right=0.98, top=0.8, bottom=0.2, wspace=0.25)
    for ax in (a1, a2):
        ax.set_facecolor(D.BACKGROUND)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(axis="y", color="#E3E3E3", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors=D.TEXT)
    x = np.arange(len(since))
    colours = [D.GREEN] * (len(since) - 1) + [D.GREY]
    a1.bar(x, since["rate"], color=colours, width=0.7)
    for xi, (n, r) in zip(x, since[["n", "rate"]].to_numpy()):
        a1.text(xi, r + 0.006, f"{r:.0%}\nn={int(n)}", ha="center", va="bottom", fontsize=7, color=D.TEXT)
    a1.axhline(since["rate"].iloc[-1], color=D.GREY, linestyle="--", linewidth=0.8)
    a1.set_xticks(x, since.index, rotation=30, ha="right", fontsize=8)
    a1.set_ylabel("Share of stool sample x taxon detected", color=D.TEXT)
    a1.set_ylim(0, max(since["rate"]) * 1.35)
    a1.set_title("Detection vs time since the taxon was last eaten", fontsize=9.5, color=D.TEXT, loc="left")

    x = np.arange(len(scores))
    for k, metric in enumerate(["precision", "recall", "accuracy"]):
        a2.bar(x + (k - 1) * 0.26, scores[metric], width=0.26, color=CF.METRIC_COLOURS[metric],
               label=metric.capitalize())
    a2.set_xticks(x, scores["window"], rotation=30, ha="right", fontsize=8)
    a2.set_ylim(0, 1)
    a2.set_ylabel("Score (all stool sample x taxon pairs)", color=D.TEXT)
    a2.legend(loc="upper left", frameon=False, fontsize=8, ncol=3)
    a2.set_title("'Eaten' = logged within this window before the stool", fontsize=9.5, color=D.TEXT, loc="left")
    fig.text(0.06, 0.96, "Timing of meals vs detection in stool sequencing", fontsize=12, fontweight="bold", va="top")
    fig.text(0.06, 0.905, f"{n_samples} stool samples whose previous 5 days are fully covered by the diet log; "
             f"detected = compatible ASVs \u2265 {S.DETECTION_MIN:.1%} of reads; genus-level merged taxa. "
             "Grey: taxon not eaten before the stool.", fontsize=8, color=D.TEXT, va="top")
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--detection-min", type=float, default=S.DETECTION_MIN)
    args = parser.parse_args()
    S.DETECTION_MIN = args.detection_min
    suffix = "" if args.detection_min == 1e-3 else "_" + f"{args.detection_min * 100:g}".replace(".", "p") + "pct"

    calls, skipped, events = timed_calls()
    conf_w, conf_a = confusion_by(calls, "window"), confusion_by(calls, "any")
    OUT.mkdir(parents=True, exist_ok=True)
    calls.to_csv(OUT / f"timing_calls{suffix}.csv", index=False)
    pd.concat({"window_12h_3d": conf_w, "any_time": conf_a}, axis=1).to_csv(
        OUT / f"timing_confusion_per_subject{suffix}.csv")
    n_samples = calls["Sample_ID"].nunique()
    plot(conf_w, conf_a, OUT / f"timing_vs_pooled_per_subject{suffix}.png", n_samples, len(conf_w))

    # time-since-eaten and window comparison on samples whose last 5 days are inside the log
    calls5, _, _ = timed_calls(lookback=pd.Timedelta(days=5))
    since = detection_by_time_since(calls5)
    scores = window_scores(calls5)
    since.to_csv(OUT / f"detection_vs_time_since_eaten{suffix}.csv")
    scores.to_csv(OUT / f"window_comparison{suffix}.csv", index=False)
    plot_time_and_windows(since, scores, OUT / f"timing_windows{suffix}.png", calls5["Sample_ID"].nunique())
    print(f"Window comparison on {calls5['Sample_ID'].nunique()} stool samples with 5 days of log before them:")
    print(scores[["window", "precision", "recall", "accuracy", "precision_subject_mean", "recall_subject_mean"]]
          .round(2).to_string(index=False))
    print(f"Diet events by timing source: {events['timing'].value_counts().to_dict()}")
    print(f"Stool samples used: {n_samples} of {n_samples + skipped['Sample_ID'].nunique()} "
          f"(skipped: {skipped.drop_duplicates('Sample_ID')['reason'].value_counts().to_dict()})")
    for name, c in [("12 h - 3 d window", conf_w), ("any time in log", conf_a)]:
        tot = c[["TP", "FP", "FN", "TN"]].sum()
        print(f"{name:18s} mean precision {c['precision'].mean():.2f}  recall {c['recall'].mean():.2f}  "
              f"accuracy {c['accuracy'].mean():.2f} | pooled TP/FP/FN/TN {tot.tolist()}")


if __name__ == "__main__":
    main()
