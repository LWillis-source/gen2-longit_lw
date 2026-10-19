"""Detection of the top 60 informative diet ingredients in stool sequencing, per subject over time.

For each subject, one figure: rows = the 60 most frequently logged ingredients rated 'Yes' for
sequencing (same ranking as diet_log_ingredients.py), columns = that subject's stool samples in
collection order (Collection_date + Collection_time from the Sample-ID sheet).

Which run: plant ingredients (marker trnL) are looked up in the plants run, vertebrate
ingredients (12SV5) in the meat run. Both runs sequenced the same stool samples.

Which ASVs belong to an ingredient ("compatible" ASVs): ASVs of the ingredient's genus whose
species label is the ingredient's species (including subspecies/variety labels such as
'oleracea_subsp_var.') or is missing. ASVs labelled as a different species of the genus are not
counted, unless the run never assigns the ingredient's own species (e.g. all Spinacia ASVs are
labelled 'tetrandra'): then the whole genus counts. Ingredients named only to genus
('Vaccinium spp.', hybrids such as 'Citrus x sinensis') accept every ASV of the genus. Recipes
(kimchi, feta) use the union over their species.

Detected = compatible ASVs make up at least DETECTION_MIN of the sample's reads.
    green  = some of those reads come from ASVs labelled with the exact species
    purple = only from genus-level ASVs (compatible with the ingredient, not proof of it)
    grey hatched row = the run has no compatible ASV, so the ingredient cannot be detected
Samples with fewer than MIN_READS reads in the run are shaded and labelled 'low reads'.

Outputs (diet_log_analyses/figures_Diet-logs/Stool-detection/)
    Stool-detection-<subject>.png
    stool_detection_long.csv   one row per subject x stool sample x ingredient

Usage (from the repository root):
    python diet_log_analyses/stool_detection_timeseries.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import config as C
import diet_log_ingredients as D
import weeklong_food as F
from config import plt

OUT = D.OUT / "Stool-detection"
TOP_N = 60
DETECTION_MIN = 1e-3  # 0.1% of reads: the floor below which the R ASV heatmaps show black
MIN_READS = 500  # stool samples below this are unreliable (cut-off of the R stool heatmaps)
RUN_OF_MARKER = {"trnL": "plants", "12SV5": "meat"}

#######################################
# Ingredient -> compatible ASVs
#######################################


def parse_species(sp):
    """'Brassica oleracea var. capitata' -> ('Brassica', 'oleracea'); 'Vaccinium spp.' -> ('Vaccinium', None)."""
    words = D.clean_species(sp).split()
    genus = words[0]
    epithet = words[1] if len(words) > 1 and words[1] not in ("spp.", "x") and words[1][0].islower() else None
    return genus, epithet


def compatible_asvs(species_field, tax):
    """Compatible ASVs of an ingredient in one run: (all compatible, those labelled with the exact species)."""
    allc, exact = set(), set()
    for sp in D.species_list(species_field):
        genus, epithet = parse_species(sp)
        if genus.endswith(("idae", "oideae", "aceae")):  # family name: use a genus given in parentheses
            inner = D.genera_of(sp)
            if not inner:
                continue  # e.g. 'Gadidae (cod/haddock/pollock, unspecified)': no genus, undetectable
            genus, epithet = inner[0], None
        in_genus = tax[tax["Genus"] == genus]
        # plants store only the epithet ('oleracea'), meat the binomial ('Bos taurus')
        epi = in_genus["Species"].astype(str).str.replace(rf"^{genus} ", "", regex=True)
        unlabelled = in_genus["Species"].isna()
        if epithet is None:
            allc |= set(in_genus.index)
            continue
        same = ~unlabelled & ((epi == epithet) | epi.str.startswith(epithet + "_"))
        if not same.any():
            # the run never assigns the food's own species (e.g. every Spinacia ASV is 'tetrandra'):
            # the marker cannot separate the genus, so all its ASVs count as genus-level evidence
            allc |= set(in_genus.index)
            continue
        allc |= set(in_genus.index[same | unlabelled])
        exact |= set(in_genus.index[same])
    return allc, exact


#######################################
# Detection table
#######################################


def load_runs():
    """Plants and meat runs (phyloseq-like objects with the sample sheet joined)."""
    return {"plants": F.standard_setup(F.PLANTS).ps, "meat": F.standard_setup(F.MEAT).ps}


def stool_samples(ps):
    """Stool samples of one run with their collection timing, in collection order."""
    s = ps.sam[ps.sam["Region"] == "Stool"].copy()
    s["total_reads"] = ps.otu.loc[s.index].sum(axis=1)
    # Collection_date is yymmdd text ('250809'); missing dates/times are 'NA', '-' or blank
    raw = s["Collection_date"].astype(str)
    s["date"] = np.where(raw.str.fullmatch(r"\d{6}"), raw.str[2:4] + "-" + raw.str[4:6], None)
    s["time"] = s["Collection_time"].where(s["Collection_time"].astype(str).str.fullmatch(r"\d{1,2}:\d{2}"), None)
    return s


def detection_table(runs, top, lexicon):
    rows = []
    stools = {run: stool_samples(ps) for run, ps in runs.items()}
    for ing in top["ing"]:
        sp_field, marker = lexicon.at[ing, "species"], lexicon.at[ing, "marker"]
        run = RUN_OF_MARKER[next(m.strip() for m in str(marker).split(";") if m.strip() in RUN_OF_MARKER)]
        ps, st = runs[run], stools[run]
        allc, exact = compatible_asvs(sp_field, ps.tax)
        counts = ps.otu.loc[st.index]
        reads_all = counts[sorted(allc)].sum(axis=1) if allc else pd.Series(0.0, index=st.index)
        reads_exact = counts[sorted(exact)].sum(axis=1) if exact else pd.Series(0.0, index=st.index)
        for sample, r in st.iterrows():
            frac = reads_all[sample] / r["total_reads"] if r["total_reads"] else 0.0
            detected = bool(allc) and frac >= DETECTION_MIN
            rows.append({"Subject_ID": r["Subject_ID"], "Sample_ID": r["Sample_ID"], "Sample_origin2": r["Sample_origin2"],
                         "date": r["date"], "time": r["time"], "run": run, "total_reads": int(r["total_reads"]),
                         "low_reads": r["total_reads"] < MIN_READS, "ingredient": ing,
                         "n_compatible_ASVs": len(allc), "n_exact_species_ASVs": len(exact),
                         "reads_compatible": int(reads_all[sample]), "reads_exact_species": int(reads_exact[sample]),
                         "rel_abundance": frac, "detected": detected,
                         "evidence": ("species" if reads_exact[sample] / max(r["total_reads"], 1) > 0 and detected
                                      else "genus" if detected else "")})
    return pd.DataFrame(rows)


#######################################
# Plot
#######################################


def sample_order(samples):
    """Collection order: date, then time; samples without a date or time go last."""
    key = samples.assign(_d=samples["date"].fillna("99-99"), _t=samples["time"].fillna("99:99"))
    return key.sort_values(["_d", "_t", "Sample_ID"]).drop(columns=["_d", "_t"])


COL_IN, CELL_IN = 0.3, 0.16  # stool column width and row height (inches)


def subject_samples(det, sid):
    d = det[det["Subject_ID"] == sid]
    return sample_order(d.drop_duplicates("Sample_ID")[["Sample_ID", "Sample_origin2", "date", "time"]])


def draw_stool_grid(ax, sid, det, top, show_labels=True, labels=None):
    """Draw one subject's ingredient x stool-sample detection grid on `ax`; returns the number of samples."""
    d = det[det["Subject_ID"] == sid]
    samples = subject_samples(det, sid)
    # low-read flag can differ between runs: keep it per (sample, run)
    low = d.drop_duplicates(["Sample_ID", "run"]).set_index(["Sample_ID", "run"])["low_reads"]
    n_rows, n_cols = len(top), len(samples)
    row = {ing: i for i, ing in enumerate(top["ing"])}
    col = {s: j for j, s in enumerate(samples["Sample_ID"])}
    cell_of = d.set_index(["ingredient", "Sample_ID"])

    for ing, i in row.items():
        r0 = cell_of.loc[ing].iloc[0]
        run, undetectable = r0["run"], r0["n_compatible_ASVs"] == 0
        for s, j in col.items():
            lowr = bool(low.get((s, run), False))
            bg = "#E4E4E4" if lowr else "#F2F2F2"
            if undetectable:
                ax.add_patch(Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, facecolor=D.lighten(D.GREY, 0.75),
                                       edgecolor=D.GREY, hatch="////", linewidth=0))
                continue
            ax.add_patch(Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, facecolor=bg, edgecolor="none"))
            c = cell_of.loc[(ing, s)]
            if c["detected"]:
                colour = D.GREEN if c["evidence"] == "species" else D.PURPLE
                ax.add_patch(Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, facecolor=colour, edgecolor=colour))

    for s, j in col.items():
        smp = samples[samples["Sample_ID"] == s].iloc[0]
        date = smp["date"] if isinstance(smp["date"], str) else "date NA"
        time = smp["time"] if isinstance(smp["time"], str) else "time NA"
        ax.text(j + 0.5, -0.4, f"{date} {time}  {smp['Sample_origin2']} ({s})", ha="center", va="bottom",
                fontsize=6, color=D.TEXT, rotation=90)
        if any(bool(low.get((s, r), False)) for r in ("plants", "meat")):
            ax.text(j + 0.5, n_rows + 0.3, "low\nreads", ha="center", va="top", fontsize=5.5, color="#B03030")

    n_det = d[d["detected"]].groupby("ingredient")["Sample_ID"].nunique()
    for ing, i in row.items():
        n = int(n_det.get(ing, 0))
        ax.text(n_cols + 0.3, i + 0.5, f"{n}/{n_cols}" if n else "", ha="left", va="center", fontsize=6.5,
                color=D.TEXT)
    ax.text(n_cols + 0.3, -0.4, "detected", ha="left", va="bottom", fontsize=6.5, color=D.TEXT, rotation=90)

    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)
    if show_labels:
        ax.set_yticks(np.arange(n_rows) + 0.5, labels or D.informative_labels(top), fontsize=7.5)
        for tick in ax.get_yticklabels():
            tick.set_color(D.TEXT)
    else:
        ax.set_yticks([])
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    return n_cols


def stool_legend():
    return [Patch(facecolor=D.GREEN, label="Detected, incl. ASVs labelled with the exact species"),
            Patch(facecolor=D.PURPLE, label="Detected via genus-level ASVs only"),
            Patch(facecolor="#F2F2F2", edgecolor="#BBBBBB", label="Not detected"),
            Patch(facecolor="#E4E4E4", label=f"Sample with < {MIN_READS} reads in that run"),
            Patch(facecolor=D.lighten(D.GREY, 0.75), edgecolor=D.GREY, hatch="////",
                  label="No compatible ASV in the run (undetectable)")]


STOOL_NOTE = ("Compatible ASVs: the ingredient's genus, labelled with its species or with no species label.\n"
              "Marker resolution: e.g. milk, cheese and beef (Bos taurus), or cabbage and broccoli (Brassica oleracea), "
              "cannot be told apart.")


def plot_subject(sid, det, top, path):
    n_rows, n_cols = len(top), len(subject_samples(det, sid))
    label_w, right_w, bottom, top_margin = 2.75, 0.75, 0.95, 2.3
    width = label_w + n_cols * COL_IN + right_w
    height = n_rows * CELL_IN + bottom + top_margin
    W = max(width, 8.5)
    fig = plt.figure(figsize=(W, height), facecolor=D.BACKGROUND)
    ax = fig.add_axes([label_w / W, bottom / height, n_cols * COL_IN / W, n_rows * CELL_IN / height],
                      facecolor=D.BACKGROUND)
    draw_stool_grid(ax, sid, det, top)

    fig.text(0.02, 1 - 0.15 / height, f"Subject {sid}: top {TOP_N} informative ingredients detected in stool sequencing",
             fontsize=11, fontweight="bold", va="top")
    fig.text(0.02, 1 - 0.4 / height,
             f"{n_cols} stool samples in collection order (date, time, sample, Sample_ID). Detected = ASVs compatible "
             f"with the ingredient\nmake up ≥{DETECTION_MIN:.1%} of the sample's reads "
             f"(plants run for trnL ingredients, meat run for 12SV5).",
             fontsize=8, color=D.TEXT, va="top")
    fig.legend(handles=stool_legend(), loc="lower left", bbox_to_anchor=(0.01, 0.32 / height), ncol=2,
               frameon=False, fontsize=7.5)
    fig.text(0.02, 0.06 / height, STOOL_NOTE, fontsize=6.5, color=D.TEXT, va="bottom")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


#######################################
# Run
#######################################


def main():
    entries, lexicon = D.read_coding()
    long = D.split_ingredients(entries)
    species, genus, _ = D.read_labels()
    freq = D.ingredient_table(long, lexicon, species, genus)
    top = freq[freq["informative_for_sequencing"] == "Yes"].head(TOP_N).reset_index(drop=True)

    runs = load_runs()
    det = detection_table(runs, top, lexicon)
    OUT.mkdir(parents=True, exist_ok=True)
    det.to_csv(OUT / "stool_detection_long.csv", index=False)

    diet_subjects = sorted(entries["Subject_ID"].unique())
    for sid in diet_subjects:
        s = f"{int(sid):02d}"
        if (det["Subject_ID"] == s).any():
            plot_subject(s, det, top, OUT / f"Stool-detection-{s}.png")
    no_diet = sorted(set(det["Subject_ID"]) - {f"{int(x):02d}" for x in diet_subjects})
    undetectable = det.drop_duplicates("ingredient").query("n_compatible_ASVs == 0")["ingredient"].tolist()
    print(f"{len(diet_subjects)} subjects plotted to {OUT}; stool samples without a diet log skipped: {no_diet}")
    print(f"Ingredients with no compatible ASV (undetectable): {undetectable}")
    by_ing = det.groupby("ingredient")["detected"].mean().reindex(top["ing"])
    print("Share of stool samples with detection (top 10 ingredients):")
    print((100 * by_ing.head(10)).round(0).astype(int).astype(str).add("%").to_string())


if __name__ == "__main__":
    main()
