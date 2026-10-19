"""Weeklong 16S analysis: Python translation of 2-analysis/20250319_Weeklong-16S.Rmd.

Each R chunk is one function below, in the same order and with the same name. Figures
go to 3-figures_python/ using the same sub-folder and file names as 3-figures/.

Usage (from the repository root):
    python 2-analysis_python/weeklong_16s.py                       # run everything
    python 2-analysis_python/weeklong_16s.py --sections alpha pcoa_all
    python 2-analysis_python/weeklong_16s.py --list                # show section names

Differences from the R notebook are marked "NOTE (R difference)" in the code.
"""

from __future__ import annotations

import argparse
import itertools
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.spatial.distance import pdist, squareform

import config as C
from config import plt

FIG = C.FIG_DIR

#######################################
# Variables to change
#######################################

colors_pH = {"<5.5": "#F4C2C2", "5.5": "#d2c119", "5.8": "#bdb016", "6": "#b0a515", "6.2": "#97971d",
             "6.4": "#82881c", "6.6": "#747a18", "6.8": "#5c741e", "7": "#4c681b", "7.2": "#2e5617",
             "7.4": "#354e15", "7.6": "#00463b", "8.0": "#102332", "NM": "#CCCCCC"}

colors_origin = {"Saliva": "#A2FC3C", "Capscan": "#A31301", "R1": "#A31301", "R2": "#D96A57", "R3": "#EDA192",
                 "R4": "#EDA192", "Stool": "#3E378F", "Plasma": "#FE932A", "Nasal": "#1FC9DD"}

_seq13 = ["#A31301", "#D23105", "#F05B12", "#FE932A", "#F6C33A", "#D3E835", "#A2FC3C", "#5EFC6E", "#20EAAB",
          "#1FC9DD", "#3E9BFE", "#466BE3", "#3E378F"]
_suffix13 = ["0", "1", "2", "3E", "3", "4E", "4", "5E", "5", "6E", "6", "7", "8"]
saliva_colors = {f"Saliva{s}": c for s, c in zip(_suffix13, _seq13)}
capscan_colors = {f"Capscan{s}": c for s, c in zip(_suffix13, _seq13)}
stool_colors = {f"Stool{s}": c for s, c in zip(_suffix13, _seq13)}
kit_colors = {**dict(zip(_suffix13, _seq13)), "Extra": "#CCCCCC"}

region_order = ["Blood", "Saliva", "Nasal", "R1", "R2", "R3", "R4", "Stool"]

cutoff_SI = 0.001  # Supplementary Info ASV cutoff
cutoff_MT = 0.01  # Main Text ASV cutoff (to minimize legend)

METRICS = ["wunifrac", "unifrac", "bray", "canberra", "binary"]
ORIGIN3_LEVELS = ["Saliva", "Capscan", "Stool"]
PREDICTION_LEVELS = ["SI_light", "SI", "SI_dark", "AC", "NA"]
colors_prediction = dict(zip(PREDICTION_LEVELS, C.hue_pal(5)))

REGION_LEVELS = ["NA", "Saliva", "R1", "R2", "R3", "Stool"]
SAMPLE_ORIGIN_LEVELS = [
    "Capscan0", "Capscan1", "Capscan2", "Capscan3", "Capscan3E", "Capscan4", "Capscan4E", "Capscan5", "Capscan5E",
    "Capscan6", "Capscan6E", "Capscan7", "Capscan8", "CapscanExtra1", "CapscanExtra2", "CapscanExtra3",
    "ExtraSaliva", "Saliva0", "Saliva1", "Saliva2", "Saliva3", "Saliva3E", "Saliva4", "Saliva4E", "Saliva5",
    "Saliva5E", "Saliva6", "Saliva6E", "Saliva7", "Saliva8", "Stool0", "Stool1", "Stool2", "Stool3", "Stool3E",
    "Stool4", "Stool5", "Stool5E", "Stool6", "Stool6E", "Stool7", "Stool8", "StoolExtra1", "StoolExtra2",
    "StoolNoCapscan"]
SAMPLE_ORIGIN2_LEVELS = [
    "Cap0", "Cap1", "Cap2", "Cap3", "CapE1", "Cap4", "Cap5", "CapE2", "Cap6", "Cap7", "Cap8", "CapEx1", "CapEx2",
    "CapEx3", "SalivaX", "Saliva0", "Saliva1", "Saliva2", "Saliva3", "Saliva3E", "Saliva4", "Saliva4E", "Saliva5",
    "Saliva5E", "Saliva6", "Saliva6E", "Saliva7", "Saliva8", "Stool0", "Stool1", "Stool2", "Stool3", "Stool3E",
    "Stool4", "Stool5", "Stool5E", "Stool6", "Stool6E", "Stool7", "Stool8", "StoolExtra1", "StoolExtra2",
    "StoolNoCapscan"]
KIT_SET_LEVELS = ["0", "1", "2", "3E", "3", "4E", "4", "5E", "5", "6E", "6", "7", "8", "Extra"]


def set_ordered_factors(df2plot):
    """Set default ordered factors in a dataframe (R: set_ordered_factors)."""
    df2plot = df2plot.copy()
    df2plot["Region"] = C.ordered_categorical(df2plot["Region"], REGION_LEVELS)
    df2plot["Sample_origin"] = C.ordered_categorical(df2plot["Sample_origin"], SAMPLE_ORIGIN_LEVELS)
    df2plot["Sample_origin2"] = C.ordered_categorical(df2plot["Sample_origin2"], SAMPLE_ORIGIN2_LEVELS)
    df2plot["Sample_origin3"] = C.ordered_categorical(df2plot["Sample_origin3"], ORIGIN3_LEVELS)
    df2plot["Kit_set"] = pd.Categorical(df2plot["Kit_set"], categories=KIT_SET_LEVELS)
    # R turns total_reads into a factor so it can be a discrete axis; here it stays numeric and
    # the plotting helpers treat it as a category sorted numerically (same order as the factor).
    return df2plot


#######################################
# Standard Setup
#######################################


@dataclass
class Context:
    """What the R global environment holds after the setup chunk."""

    ps: C.PS
    samdf: pd.DataFrame
    taxa_order: pd.DataFrame
    kits: pd.DataFrame
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(100))
    cache: dict = field(default_factory=dict)


def _session_label(n):
    """Sampling_no -> session label: '3' -> '3', '3.5' (extra session) -> '3E', extras unchanged."""
    s = str(n)
    if s.replace(".", "", 1).isdigit():
        x = float(s)
        return f"{int(x)}E" if x % 1 else str(int(x))
    return s


def _origin_labels(origin, sampling_no):
    """(Sample_origin, Sample_origin2, Kit_set) in the labels the analyses use, e.g.
    ('capscan', '3.5') -> ('Capscan3E', 'CapE1', '3E'); ('stool', 'StoolExtra1') -> ('StoolExtra1', ...)."""
    if pd.isna(sampling_no):
        return np.nan, np.nan, np.nan
    lab = _session_label(sampling_no)
    numeric = lab[0].isdigit()
    kit_set = lab if numeric else "Extra"
    word = {"capscan": "Capscan", "saliva": "Saliva", "stool": "Stool"}.get(str(origin).lower(), str(origin))
    if not numeric:  # 'CapscanExtra1', 'ExtraSaliva', 'StoolExtra2', 'StoolNoCapscan'
        o2 = {"ExtraSaliva": "SalivaX"}.get(lab, lab.replace("CapscanExtra", "CapEx"))
        return lab, o2, kit_set
    if word == "Capscan" and lab.endswith("E"):
        o2 = "CapE1" if lab in ("3E", "4E") else "CapE2"  # extra capsule sessions as labelled in the R notebook
    else:
        o2 = ("Cap" if word == "Capscan" else word) + lab
    return word + lab, o2, kit_set


def read_sample_sheet(path):
    """Per-sample metadata from LONGITWeeklong-samplesheet-FINAL.xlsx (corrected sheet).

    The corrected workbook keeps per-sample fields on the Sample_ID sheet and per-kit fields
    (subject, ingestion/collection date and time, transit time, Bristol score, session number)
    on the Kit_ID sheet. This joins the two and rebuilds the columns the analyses use:
        Subject_ID ('01'), Sample_origin ('Capscan3E'), Sample_origin2 ('CapE1'),
        Sample_origin3 ('Capscan'), Region ('R1', 'Saliva', 'Stool'), Kit_set ('3E'),
        Collection_date ('250809'), Collection_date_reformat ('08-09'), Collection_time,
        Ingestion_date_reformat, Ingestion_time, Transit_time_h, Bristol_score.
    A stool that passed several capsules lists several kits ('LS114, LS115'): its subject and
    collection time are shared by those kits; session labels come from the first kit, and
    Transit_time_h is left empty (each capsule has its own). Cells are read like readxl does.
    """
    kits = C.read_excel_like_readxl(path, sheet_name="Kit_ID")
    samples = C.read_excel_like_readxl(path, sheet_name="Sample_ID")
    kit = kits.drop_duplicates("Kit_ID").set_index("Kit_ID")
    kit_lists = samples["Kit_ID"].astype(str).str.split(",").map(lambda ks: [k.strip() for k in ks])
    first = kit_lists.str[0]
    multi = kit_lists.str.len() > 1
    for ks in kit_lists[multi]:
        shared = kit.reindex(ks)[["Subject_ID", "Collection_date", "Collection_time"]].astype(str).drop_duplicates()
        assert len(shared) == 1, f"kits {ks} disagree on subject or collection time"

    k = kit.reindex(first.to_numpy())
    k.index = samples.index
    subj = k["Subject_ID"].map(C.r_num_str)
    samples["Subject_ID"] = subj.map(lambda v: f"{int(v):02d}" if isinstance(v, str) and v.isdigit() else v)
    labels = [_origin_labels(o, n) for o, n in zip(samples["Sample_origin"], k["Sampling_no"])]
    samples["Sample_origin"] = [l[0] for l in labels]
    samples["Sample_origin2"] = [l[1] for l in labels]
    samples["Kit_set"] = [l[2] for l in labels]
    samples["Sample_origin3"] = [o if pd.isna(o) else o[:7] if o.startswith("Capscan") else
                                 "Saliva" if "Saliva" in o else "Stool" for o in samples["Sample_origin"]]
    samples["Region"] = samples["Region"].replace({"saliva": "Saliva", "stool": "Stool"})

    def reformat(raw):  # '250809' -> '08-09'; 'NR' / blank -> NaN
        ok = raw.where(raw.astype(str).str.fullmatch(r"\d{6}"), np.nan)
        return ok.str[2:4] + "-" + ok.str[4:6]

    # Saliva is taken when the capsule is swallowed, so its collection time is the kit's ingestion
    # time; capsule and stool samples are collected at the kit's collection time.
    saliva = samples["Sample_origin3"] == "Saliva"
    capsule = samples["Sample_origin3"] == "Capscan"
    coll_date = k["Collection_date"].map(C.r_num_str).where(~saliva, k["Ingestion_date"].map(C.r_num_str))
    coll_time = k["Collection_time"].map(C.r_num_str).where(~saliva, k["Ingestion_time"].map(C.r_num_str))
    samples["Collection_date"], samples["Collection_date_reformat"] = coll_date, reformat(coll_date)
    samples["Collection_time"] = coll_time
    # capsule-specific fields only on capsule samples, as in the earlier sheet
    ing_date = k["Ingestion_date"].map(C.r_num_str).where(capsule)
    samples["Ingestion_date"], samples["Ingestion_date_reformat"] = ing_date, reformat(ing_date)
    samples["Ingestion_time"] = k["Ingestion_time"].map(C.r_num_str).where(capsule)
    samples["Transit_time_h"] = pd.to_numeric(k["Transit_time_h"], errors="coerce").where(capsule & ~multi)  # as.numeric()
    samples["Bristol_score"] = k["BSS"].map(C.r_num_str).where(samples["Sample_origin3"] == "Stool")
    return kits, samples


def standard_setup(setup_fn=C.setup_tables, data_dir="DADA2-weeklong", sample_info="Weeklong-sample-info.xlsx",
                   groups=None):
    """Standard Setup chunk. The defaults are the Weeklong 16S data; the meat/plants notebooks
    pass their own setup function and data, and keep only some sample Groups in ps."""
    ps, taxa_order, samdf = setup_fn(C.DATA_DIR / data_dir, C.DATA_DIR / sample_info)
    kits, samples = read_sample_sheet(C.SAMPLE_SHEET)

    # Add read counts and sample info
    samdf = samdf.copy()
    samdf["Sample"] = samdf.index
    samdf["total_reads"] = samdf.index.map(ps.sample_sums()).fillna(0)
    n = len(samdf)
    samdf = samdf.merge(samples, on="Sample_ID", how="left")
    assert len(samdf) == n, "Sample_ID join duplicated rows"
    samdf.index = samdf.pop("Sample")

    # update sample data of the phyloseq object
    ps.sam = samdf.loc[ps.otu.index].copy()
    if groups is not None:  # ps <- ps %>% subset_samples(Group %in% groups)
        ps = ps.subset_samples(ps.sam["Group"].isin(groups))

    # The R sequencer chunk turns samdf$Prediction into a factor; every later chunk that uses
    # samdf (not sample_data(ps)) sees that factor, so do it once here.
    samdf["Prediction"] = pd.Categorical(samdf["Prediction"], categories=PREDICTION_LEVELS)
    return Context(ps=ps, samdf=samdf, taxa_order=taxa_order, kits=kits)


def subjects(ctx):
    """unique(samdf$Subject_ID), in order of appearance (NA and "NA" skipped)."""
    return [s for s in dict.fromkeys(ctx.samdf["Subject_ID"].dropna()) if s != "NA"]


def red_if_small_discrete(label):
    """make text red if total reads is less than 10 K"""
    v = pd.to_numeric(label, errors="coerce")
    return label, ("red" if not np.isnan(v) and v < 10000 else "black")


def red_if_small_discrete_cap(label):
    """label '12345.R1': red if the read count (before the period) is < 10K"""
    parts = str(label).split(".")
    v = pd.to_numeric(parts[0], errors="coerce") if len(parts) > 1 else np.nan
    return label, ("red" if not np.isnan(v) and v < 10000 else "black")


def red_if_small_discrete_reads_only(label):
    """label '12345.R1.3': show only the read count, red if < 10K"""
    parts = str(label).split(".")
    v = pd.to_numeric(parts[0], errors="coerce") if len(parts) > 1 else np.nan
    text = "NA" if np.isnan(v) else str(int(v))
    return text, ("red" if not np.isnan(v) and v < 10000 else "black")


def relabund_pruned(ps, cutoff, renormalize=True):
    """ps -> relative abundance -> keep taxa > cutoff in any sample -> (renormalize)."""
    rel = ps.relative()
    keep = rel.taxa_above(cutoff)
    if renormalize:
        return ps.prune_taxa(keep).relative(), keep
    return rel.prune_taxa(keep), keep


def drop_sparse_samples(ps):
    """The R 'clean' step before ordination.

    NOTE (R behaviour kept): the comments in R say 'remove OTUs present in < 3 samples', but the
    OTU table has samples as rows (taxa_are_rows = FALSE), so rowSums() acts on samples: this
    removes samples with zero reads or fewer than 3 detected ASVs, and keeps every taxon.
    """
    otu = ps.otu
    keep = (otu.sum(axis=1) > 0) & ((otu > 0).sum(axis=1) >= 3)
    return ps.subset_samples(keep)


#######################################
# Sequencer statistics
#######################################


def sequencer_stats(ctx, prefix=""):
    """Read-count histograms. prefix ('Meat-', 'Plants-') is prepended to the file names."""
    samdf = ctx.samdf
    out = FIG / "Weeklong-Sequencer"
    num_zeros = int((samdf["total_reads"] == 0).sum())
    num_samples = int((samdf["total_reads"] >= 0).sum())
    df = samdf.assign(log_reads=np.log10(samdf["total_reads"].replace(0, np.nan)))
    sub = f"{num_zeros} of {num_samples} samples have 0 reads."
    common = dict(x="log_reads", xlabel="log10(reads)", xlim_low=0, xbreaks=range(7))

    C.histogram(df, fill="Region", palette=colors_origin, path=out / f"{prefix}Read-counts-region.pdf", figsize=(4, 4),
                title="Read distribution", subtitle=sub, aspect=1, **common)
    C.histogram(df, fill="Region", palette=colors_origin, path=out / f"{prefix}Read-counts-region-subject.pdf",
                figsize=(5, 8), title="Read distribution", subtitle=sub, aspect=1, wrap="Subject_ID", ncol=4,
                **common)
    cap = df[df["Sample_origin3"] == "Capscan"]
    C.histogram(cap, fill="Region", palette=colors_origin, path=out / f"{prefix}Read-counts-capscan.pdf", figsize=(5, 2),
                aspect=0.5, **common)
    C.histogram(cap, fill="pH", palette=colors_pH, path=out / f"{prefix}Read-counts-capscan-pH.pdf", figsize=(5, 2),
                aspect=0.5, **common)
    pred_levels = [l for l in PREDICTION_LEVELS if (cap["Prediction"] == l).any()]
    C.histogram(cap, fill="Prediction", palette=C.default_palette(pred_levels), levels=pred_levels,
                path=out / f"{prefix}Read-counts-capscan-prediction.pdf", figsize=(5, 2), aspect=0.5, **common)
    # The R chunk ends with a Prediction x pH bar chart that is never saved; it is skipped here.


#######################################
# Composition 0 read cutoff, highlight <10k reads
#######################################


def _composition_df(ctx, ps2plot):
    ps2plot, _ = relabund_pruned(ps2plot, cutoff_MT)
    df2plot = ps2plot.psmelt()
    df2plot = C.set_family_order(df2plot, ctx.taxa_order)
    df2plot = set_ordered_factors(df2plot)
    return df2plot, C.get_color_mapping(df2plot)


def _width(df):
    return 0.5 * df["No"].nunique() + 1


def composition_by_sample_origin(ctx):
    ps = ctx.ps
    base = FIG / "Weeklong-composition-0p01"
    facets = ["Collection_date", "Collection_time", "Sample_origin2"]
    groups = [
        ("Saliva", ps.sam["Region"] == "Saliva", ["total_reads"], red_if_small_discrete, 12),
        ("Stool", ps.sam["Region"] == "Stool", ["total_reads"], red_if_small_discrete, 5),
        ("Capscan", ~ps.sam["Region"].isin(["Stool", "Saliva"]), ["total_reads", "Region"],
         red_if_small_discrete_cap, 12),
    ]
    for name, mask, xcols, labeller, legend_h in groups:
        df2plot, scale = _composition_df(ctx, ps.subset_samples(mask))
        folder = base / f"{name}-collection"
        for sid in subjects(ctx):
            d = df2plot[df2plot["Subject_ID"] == sid]
            if d.empty:
                continue
            C.composition_plot(d, xcols, facets, scale, folder / f"Composition-{name.lower()}-{sid}.pdf",
                               _width(d), 4, labeller)
        C.legend_figure(scale, folder / f"Composition-{name.lower()}-legend.pdf", 6, legend_h, ncol=1)


def composition_paired_cap_stool(ctx):
    ps = ctx.ps
    folder = FIG / "Weeklong-composition-0p01" / "Paired-collection"
    df2plot, scale = _composition_df(ctx, ps.subset_samples(ps.sam["Region"] != "Saliva"))
    for sid in subjects(ctx):
        d = df2plot[df2plot["Subject_ID"] == sid]
        if d.empty:
            continue
        C.composition_plot(d, ["total_reads", "Region"], ["Collection_date", "Collection_time", "Sample_origin2"],
                           scale, folder / f"Composition-cap-stool-{sid}.pdf", _width(d), 4,
                           red_if_small_discrete_cap)
    C.legend_figure(scale, folder / "Composition-cap-stool-legend.pdf", 6, 5, ncol=3)


def composition_all_by_kit_set(ctx):
    folder = FIG / "Weeklong-composition-0p01"
    df2plot, scale = _composition_df(ctx, ctx.ps)
    for origin in ctx.samdf["Sample_origin3"].dropna().unique():
        d = df2plot[df2plot["Sample_origin3"] == origin]
        C.composition_plot(d, ["total_reads", "Region", "Kit_set"], None, scale,
                           folder / f"Composition-all-{origin}.pdf", 20, 12, red_if_small_discrete_reads_only,
                           wrap="Subject_ID", hide_y_text=True)
    C.legend_figure(scale, folder / "Composition-all-legend.pdf", 5, 2.5, ncol=3)


def composition_capscan_clustering(ctx):
    ps = ctx.ps
    folder = FIG / "Weeklong-composition-0p01"
    ps2plot = ps.subset_samples((ps.sam["Sample_origin3"] == "Capscan") & (ps.sam["total_reads"] > 10000))
    ps2plot, _ = relabund_pruned(ps2plot, cutoff_MT)
    df2plot = set_ordered_factors(C.set_family_order(ps2plot.psmelt(), ctx.taxa_order))
    scale = C.get_color_mapping(df2plot)
    colours = dict(zip(scale["breaks"], scale["values"]))
    fam_rank = {f: i for i, f in enumerate(df2plot["Family2"].cat.categories)}

    colors_subject = dict(zip(subjects(ctx), C.hue_pal(20)))
    annot_colors = {**colors_subject, **colors_origin, **colors_prediction}

    for d_metric in METRICS:
        dist_mat = C.distance(ps2plot, d_metric, ctx.rng)
        hc = linkage(squareform(dist_mat.to_numpy(), checks=False), method="average")
        sample_order = list(dist_mat.index[leaves_list(hc)])
        xpos = {s: i for i, s in enumerate(sample_order)}

        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_axes([0.06, 0.24, 0.92, 0.72])
        C.theme_blank(ax)
        xs, hs, bs, cs = [], [], [], []
        for s, rows in df2plot[df2plot["Abundance"] > 0].groupby("Sample", sort=False):
            rank = rows["Family2"].map(lambda f: fam_rank.get(f, len(fam_rank))).to_numpy()
            rows = rows.iloc[np.lexsort((np.arange(len(rows)), -rank))]
            bottom = np.concatenate([[0], np.cumsum(rows["Abundance"].to_numpy())[:-1]])
            xs += [xpos[s]] * len(rows); hs += list(rows["Abundance"]); bs += list(bottom)
            cs += [colours.get(f, C.GREY50) for f in rows["Family2"]]
        ax.bar(xs, hs, bottom=bs, width=1, color=cs, edgecolor="black", linewidth=0.1)
        ax.set_xlim(-0.5, len(sample_order) - 0.5)
        ax.set_xticks([])
        ax.set_ylabel("Abundance")
        ax.tick_params(axis="y", length=0)

        # annotation tiles: Subject_ID (bottom), Region, Prediction (top)
        sam = ps2plot.sam.loc[sample_order]
        ax2 = fig.add_axes([0.06, 0.08, 0.92, 0.12])
        for j, col in enumerate(["Subject_ID", "Region", "Prediction"]):
            for i, v in enumerate(sam[col]):
                c = C.GREY50 if pd.isna(v) else annot_colors.get(str(v), C.GREY50)
                ax2.add_patch(plt.Rectangle((i - 0.5, j - 0.5), 1, 1, facecolor=c, edgecolor="black", linewidth=0.2))
        ax2.set_xlim(-0.5, len(sample_order) - 0.5)
        ax2.set_ylim(-0.5, 2.5)
        ax2.set_yticks([0, 1, 2], ["Subject_ID", "Region", "Prediction"])
        ax2.set_xticks([])
        for sp in ax2.spines.values():
            sp.set_visible(False)
        ax2.tick_params(length=0)
        C.save(fig, folder / f"Composition-all-Capscan-clustered-{d_metric}.pdf")


#######################################
# ASV heatmap 10,000 read cutoff
#######################################


def _asv_heatmaps(ctx, cutoff, folder_name):
    ps = ctx.ps
    base = FIG / folder_name
    groups = [
        ("Saliva", lambda s: s["Region"] == "Saliva", 10000, ["Sample_origin2", "Sample_ID"], "saliva"),
        ("Capscan", lambda s: ~s["Region"].isin(["Saliva", "Stool"]), 10000,
         ["Sample_origin2", "Region", "Sample_ID"], "capscan"),
        ("Stool", lambda s: s["Region"] == "Stool", 500, ["Sample_origin2", "Sample_ID"], "stool"),
    ]
    for name, sel, min_reads, xcols, short in groups:
        for sid in subjects(ctx):
            s = ps.sam
            ps2plot = ps.subset_samples(sel(s) & (s["total_reads"] > min_reads) & (s["Subject_ID"] == sid))
            if ps2plot.nsamples() == 0:
                continue
            ps2plot, _ = relabund_pruned(ps2plot, cutoff)
            df2plot = set_ordered_factors(ps2plot.psmelt())
            nfeat = df2plot["Feature"].nunique()
            C.nested_heatmap(df2plot, xcols, ["Feature", "Taxon"], ["Collection_date", "Collection_time"],
                             base / f"{name}-collection" / f"ASV-{short}-{sid}.pdf", 10, 0.15 * (nfeat + 3))


def asv_heatmap_0p01(ctx):
    _asv_heatmaps(ctx, cutoff_MT, "Weeklong-ASV-heatmap-0p01")


def asv_heatmap_0p001(ctx):
    _asv_heatmaps(ctx, cutoff_SI, "Weeklong-ASV-heatmap-0p001")


#######################################
# Alpha diversity
#######################################


def alpha_diversity(ctx):
    out = FIG / "Weeklong-Alpha-diversity"
    alpha_df = C.estimate_richness(ctx.ps.otu)
    df2plot = ctx.samdf.join(alpha_df, how="left")
    df2plot["Shannon"] = df2plot["Shannon"].fillna(0)
    df2plot = df2plot[df2plot["total_reads"] > 10000]
    df2plot = set_ordered_factors(df2plot)

    def summarise(by):
        g = df2plot.groupby(by, observed=True, dropna=False)["Shannon"]
        return pd.DataFrame({"mean_shannon": g.mean(), "sd_shannon": g.std(), "n": g.size()})

    summ = summarise("Sample_origin3")
    summ["range"] = df2plot.groupby("Sample_origin3", observed=True)["Shannon"].agg(
        lambda v: f"{v.min():.2f} - {v.max():.2f}")
    print("\nShannon summary by Sample_origin3:\n", summ.round(3))
    means = df2plot.groupby("Sample_origin3", observed=True)["Shannon"].mean()

    hist = dict(x="Shannon", xlabel="Shannon diversity", xlim_low=0, xbreaks=range(7), key_cm=0.2,
                legend_fontsize=5)
    C.histogram(df2plot, fill="Region", palette=colors_origin, path=out / "Weeklong-Shannon.pdf", figsize=(2.5, 2),
                rows="Sample_origin3", vlines={(k, None): v for k, v in means.items()}, **hist)
    cap = df2plot[df2plot["Sample_origin3"] == "Capscan"]
    C.histogram(cap, fill="Region", palette=colors_origin, path=out / "Weeklong-Shannon-Capscan.pdf",
                figsize=(2.5, 1), aspect=0.5, **hist)
    pred_levels = [l for l in PREDICTION_LEVELS if (cap["Prediction"] == l).any()]
    C.histogram(cap, fill="Prediction", palette=C.default_palette(pred_levels), levels=pred_levels,
                path=out / "Weeklong-Shannon-Capscan-prediction.pdf", figsize=(2.5, 1), aspect=0.5, **hist)
    print("\nShannon by Prediction:\n", summarise("Prediction").round(3))
    C.histogram(cap, fill="pH", palette=colors_pH, path=out / "Weeklong-Shannon-Capscan-pH.pdf", figsize=(2.5, 1),
                aspect=0.5, **hist)

    labels = ["0-20", "20-40", "40-60", "60-80", "80-100", "100-120", "120-140"]
    df2plot["Transit_time_cat"] = pd.cut(df2plot["Transit_time_h"].astype(float), bins=range(0, 141, 20),
                                         labels=labels, include_lowest=True)
    transit_colors = dict(zip(labels, ["#FFFFFF", "#D4D4FF", "#A8A8FF", "#7D7DFF", "#5151FF", "#2626FF", "#0000FF"]))
    print("\nShannon by transit time:\n", summarise("Transit_time_cat").round(3))
    cap = df2plot[df2plot["Sample_origin3"] == "Capscan"]
    C.histogram(cap, fill="Transit_time_cat", palette=transit_colors, levels=labels, legend_title="Transit Time (h)",
                path=out / "Weeklong-Shannon-Capscan-transit-time.pdf", figsize=(2.5, 1), aspect=0.5, **hist)
    C.histogram(df2plot, fill="Region", palette=colors_origin, path=out / "Weeklong-Shannon-subj.pdf", figsize=(5, 4),
                wrap="Subject_ID", ncol=5, **hist)


#######################################
# PCoA analyses 10,000 read cutoff
#######################################


def ordinate(ps_clean, d_metric, samdf, rng):
    """ordinate(method = 'MDS') + merge(vectors, samdf, by = 'row.names') + get_evals."""
    vectors, evals = C.pcoa(C.distance(ps_clean, d_metric, rng))
    ordination_data = vectors[["Axis.1", "Axis.2"]].join(samdf, how="inner")
    return set_ordered_factors(ordination_data), C.get_evals(evals)


def pcoa_plot(ordination_data, var_exp, d_metric, fill, palette, path, figsize, shape_by_region=False,
              ellipses=False, legend=True, levels=None):
    """PCoA scatter: points filled by `fill`, optional stat_ellipse(level = 0.68), 5 cm square panel."""
    fig = plt.figure(figsize=figsize)
    ax = C.scatter_panel(fig, 5.0, left_in=0.55, bottom_in=0.45)
    C.theme_grey(ax)
    d = ordination_data
    levels = levels if levels is not None else C.level_order(d[fill])
    keyed = d[fill].astype(object)
    fills = [C.GREY50 if pd.isna(v) else palette.get(v, C.GREY50) for v in keyed]
    if ellipses:
        for lev in list(levels) + ([np.nan] if keyed.isna().any() else []):
            sel = keyed.isna() if pd.isna(lev) else keyed == lev
            pts = C.stat_ellipse_points(d.loc[sel, "Axis.1"], d.loc[sel, "Axis.2"])
            if pts is not None:
                col = C.GREY50 if pd.isna(lev) else palette.get(lev, C.GREY50)
                ax.fill(pts[:, 0], pts[:, 1], facecolor=C.to_rgba(col, 0.1), edgecolor=col, linewidth=0.5)
    markers = [C.REGION_SHAPES.get(r, 21) for r in d["Region"].astype(object)] if shape_by_region else [21] * len(d)
    C.points(ax, d["Axis.1"], d["Axis.2"], fills, markers)
    ax.set_title(d_metric, fontsize=6)
    ax.set_xlabel(f"PCo1 {var_exp[0]:.2f}%")
    ax.set_ylabel(f"PCo2 {var_exp[1]:.2f}%")
    if legend:
        present = [l for l in levels if (keyed == l).any()] + (["NA"] if keyed.isna().any() else [])
        handles = [plt.Line2D([], [], marker="o", linestyle="", markerfacecolor=palette.get(l, C.GREY50),
                              markeredgecolor="black", markeredgewidth=0.5, markersize=4, label=str(l))
                   for l in present]
        if shape_by_region:
            regs = [r for r in C.level_order(d["Region"]) if (d["Region"] == r).any()]
            handles += [plt.Line2D([], [], linestyle="", label="")] + [
                plt.Line2D([], [], marker=C.MARKERS[C.REGION_SHAPES.get(r, 21)], linestyle="", markerfacecolor="black",
                           markeredgecolor="black", markersize=3.5, label=str(r)) for r in regs]
        ax.legend(handles=handles, title=fill, loc="center left", bbox_to_anchor=(1.03, 0.5), fontsize=6,
                  title_fontsize=6, frameon=False)
    C.save(fig, path)


def pcoa_by_sample_origin(ctx):
    ps, samdf = ctx.ps, ctx.samdf
    rng = np.random.default_rng(100)  # set.seed(100) # Consistent pcoa
    # NOTE (R difference): R also ordinates Saliva and Stool here, but every plot for them is
    # commented out, so only Capscan is computed.
    for region in ["Capscan"]:
        s = ps.sam
        ps_clean = drop_sparse_samples(ps.subset_samples((s["Sample_origin3"] == region) & (s["total_reads"] > 10000)))
        for d_metric in METRICS:
            od, var_exp = ordinate(ps_clean, d_metric, samdf, rng)
            pred_levels = [l for l in PREDICTION_LEVELS if (od["Prediction"] == l).any()]
            pcoa_plot(od, var_exp, d_metric, "Prediction", C.default_palette(pred_levels),
                      FIG / "Weeklong-PCoA" / region / "SI-prediction" / f"PCoA-{d_metric}-{region}.pdf", (9, 7),
                      ellipses=True, levels=pred_levels)
            subj_levels = C.level_order(od["Subject_ID"])
            pcoa_plot(od, var_exp, d_metric, "Subject_ID", C.default_palette(subj_levels),
                      FIG / "Weeklong-PCoA" / region / "Subject_ID" / f"PCoA-{d_metric}-{region}.pdf", (9, 7),
                      ellipses=True, levels=subj_levels)


def pcoa_all_samples(ctx):
    ps = ctx.ps
    rng = np.random.default_rng(100)
    ps_clean = drop_sparse_samples(ps.subset_samples(ps.sam["total_reads"] > 10000))
    for d_metric in METRICS:
        od, var_exp = ordinate(ps_clean, d_metric, ctx.samdf, rng)
        pcoa_plot(od, var_exp, d_metric, "Region", colors_origin,
                  FIG / "Weeklong-PCoA" / "All" / f"PCoA-{d_metric}-all.pdf", (3, 3), shape_by_region=True,
                  legend=False)


def weird_unifrac(ctx):
    ps = ctx.ps
    folder = FIG / "Weeklong-PCoA" / "All" / "Weird-unifrac"
    for read_filter in [10000, 20000, 30000, 40000, 50000]:
        rng = np.random.default_rng(100)
        ps_clean = drop_sparse_samples(ps.subset_samples(ps.sam["total_reads"] > read_filter))
        od, var_exp = ordinate(ps_clean, "unifrac", ctx.samdf, rng)
        pcoa_plot(od, var_exp, "unifrac", "Region", colors_origin, folder / f"PCoA-{read_filter}-reads-all.pdf",
                  (5, 4), shape_by_region=True)

    # file labels are gsub('\\.', 'p', as.character(abund)); R prints 1e-04 in scientific notation
    for abund, label in [(0.1, "0p1"), (0.01, "0p01"), (0.001, "0p001"), (0.0001, "1e-04")]:
        rng = np.random.default_rng(100)

        def zero_rare(x, abund=abund):
            x = x.copy()
            x[x / x.sum() < abund] = 0  # set to 0 if relative abundance < threshold; keep counts
            return x

        ps2 = ps.subset_samples(ps.sam["total_reads"] > 10000).transform_sample_counts(zero_rare)
        ps_clean = drop_sparse_samples(ps2)
        od, var_exp = ordinate(ps_clean, "unifrac", ctx.samdf, rng)
        pcoa_plot(od, var_exp, "unifrac", "Region", colors_origin, folder / f"PCoA-{label}-abundance-all.pdf",
                  (5, 4), shape_by_region=True)


#######################################
# Distances between paired samples
#######################################


def distances_paired_cap_stool(ctx):
    ps = ctx.ps
    ps_filtered = ps.subset_samples((ps.sam["total_reads"] > 10000) & ps.sam["Sample_origin3"].isin(["Capscan", "Stool"]))
    sample_info = ps_filtered.sam.rename_axis("Sample").reset_index()
    capscan = sample_info[sample_info["Sample_origin3"] == "Capscan"]
    stool = sample_info[sample_info["Sample_origin3"] == "Stool"]
    pairs = capscan.merge(stool, on="Kit_ID", suffixes=("_Capscan", "_Stool"))

    results = []
    for d_metric in METRICS:
        dist_df = C.distance(ps_filtered, d_metric, ctx.rng)
        r = pairs[["Kit_ID", "Subject_ID_Capscan", "Sample_Capscan", "Region_Capscan", "Prediction_Capscan",
                   "Sample_Stool"]].copy()
        r["distance"] = [dist_df.at[a, b] for a, b in zip(pairs["Sample_Capscan"], pairs["Sample_Stool"])]
        r["metric"] = d_metric
        results.append(r)
    allp = pd.concat(results, ignore_index=True)
    allp["Prediction_Capscan"] = pd.Categorical(allp["Prediction_Capscan"], categories=PREDICTION_LEVELS)

    def violins(xcol, levels, palette, path, width):
        metrics = sorted(allp["metric"].unique())
        fig, axes = plt.subplots(len(metrics), 1, figsize=(width, 5), sharex=True)
        fig.subplots_adjust(left=0.2, right=0.9, top=0.93, bottom=0.12, hspace=0.12)
        xl = [l for l in levels if (allp[xcol] == l).any()] + (["NA"] if allp[xcol].isna().any() else [])
        jitter = np.random.default_rng(1)
        for ax, m in zip(axes, metrics):
            C.theme_grey(ax)
            d = allp[allp["metric"] == m]
            groups = [(l, d.loc[d[xcol].isna() if l == "NA" else d[xcol] == l, "distance"]) for l in xl]
            C.draw_violins(ax, groups, palette)
            for i, (_, v) in enumerate(groups):
                ax.scatter(i + jitter.uniform(-0.2, 0.2, len(v)), v, s=0.3, color="black", zorder=3, linewidths=0)
            C.strip(ax, m, side="right")
        axes[-1].set_xticks(range(len(xl)), xl)
        fig.supxlabel("Distance Metric", fontsize=7)
        fig.supylabel("Distance", fontsize=7)
        fig.suptitle("Capscan vs Stool Distances by Metric", fontsize=6, x=0.2, ha="left")
        C.save(fig, path)

    pred_levels = [l for l in PREDICTION_LEVELS if (allp["Prediction_Capscan"] == l).any()]
    violins("Prediction_Capscan", pred_levels, {**C.default_palette(pred_levels), "NA": C.GREY50},
            FIG / "Weeklong-PCoA" / "Distances-betw-cap-stool-prediction.pdf", 4)
    violins("Region_Capscan", C.level_order(allp["Region_Capscan"]), colors_origin,
            FIG / "Weeklong-PCoA" / "Distances-betw-cap-stool-region.pdf", 3)

    for by in ["Prediction_Capscan", "Region_Capscan"]:
        g = allp.groupby(["metric", by], observed=True, dropna=False)["distance"]
        summ = pd.DataFrame({"mean_dist": g.mean(), "sd_dist": g.std(), "n": g.size()})
        summ["summary"] = [f"{m:.2f} ± {s:.2f} (n={n})" for m, s, n in zip(summ.mean_dist, summ.sd_dist, summ.n)]
        print(f"\nPaired capscan-stool distances by {by}:\n", summ)


#######################################
# Total number of ASVs, 10000 read cutoff
#######################################


def cutoff_label(cutoff, percent=True):
    """gsub('\\.', 'p', paste0(cutoff * 100, '%')): 0.01 -> '1%', 0.001 -> '0p1%', 1e-4 -> '0p01%'."""
    s = f"{round(cutoff * 100, 10):g}".replace(".", "p")
    return s + "%" if percent else s


def total_asvs(ctx):
    ps = ctx.ps
    cutoffs = [0.01, 0.001, 0.0001]
    counts = {}
    for cutoff in cutoffs:
        ps2plot, _ = relabund_pruned(ps.subset_samples(ps.sam["total_reads"] > 10000), cutoff)

        def drop_below(x, cutoff=cutoff):
            x = x.copy()
            x[x < cutoff] = 0
            return x / x.sum()  # renormalize again so remaining abundances sum to 1

        ps2plot = ps2plot.transform_sample_counts(drop_below)
        counts[cutoff_label(cutoff)] = (ps2plot.otu > 0).sum(axis=1)
    nonzero_per_sample = pd.DataFrame(counts)
    nonzero_lf = nonzero_per_sample.rename_axis("Sample").reset_index().melt(
        id_vars="Sample", var_name="cutoff", value_name="num_ASVs")
    nonzero_lf = nonzero_lf.merge(ctx.samdf, left_on="Sample", right_index=True, how="left")
    nonzero_lf = set_ordered_factors(nonzero_lf)

    for by in ["Sample_origin3", "Region", "Prediction"]:
        g = nonzero_lf.groupby([by, "cutoff"], observed=True, dropna=False)["num_ASVs"]
        summ = pd.DataFrame({"mean_ASVs": g.mean(), "sd_ASVs": g.std(), "median_ASVs": g.median(),
                             "min_ASVs": g.min(), "max_ASVs": g.max(), "n": g.size()})
        print(f"\nNumber of ASVs by {by}:\n", summ.round(2))

    out = FIG / "Weeklong-Number-ASVs"
    hist = dict(x="num_ASVs", fill="Region", palette=colors_origin, figsize=(4, 4), xlabel="num_ASVs",
                ylabel="count", rows="Sample_origin3", cols="cutoff", aspect=1)
    C.histogram(nonzero_lf, path=out / "Number-ASVs-region.pdf", **hist)
    for sid in subjects(ctx):
        d = nonzero_lf[nonzero_lf["Subject_ID"] == sid]
        if not d.empty:
            C.histogram(d, path=out / f"Number-ASVs-region-{sid}.pdf", **hist)


#######################################
# Shared ASVs
#######################################


def _subject_tiles(df, value, path, figsize, title, legend_title, vmin=None, vmax=None, xlabel="Subject1",
                   ylabel="Subject2"):
    """geom_tile(Subject1 x Subject2) + facet_grid(Sample_origin3 ~ cutoff) + coord_fixed()."""
    rows = [o for o in ORIGIN3_LEVELS if (df["Sample_origin3"] == o).any()]
    cols = sorted(df["cutoff"].unique())
    subj = sorted(set(df["Subject1"]) | set(df["Subject2"]))
    vmin = df[value].min() if vmin is None else vmin
    vmax = df[value].max() if vmax is None else vmax
    fig, axes = plt.subplots(len(rows), len(cols), figsize=figsize, squeeze=False)
    fig.subplots_adjust(left=0.08, right=0.85, top=0.92, bottom=0.08, wspace=0.05, hspace=0.05)
    mesh = None
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            ax = axes[i, j]
            C.theme_blank(ax)
            d = df[(df["Sample_origin3"] == r) & (df["cutoff"] == c)]
            M = d.pivot(index="Subject2", columns="Subject1", values=value).reindex(index=subj, columns=subj)
            cm = C.GRADIENT_WHITE_BLUE.copy()
            cm.set_bad((0, 0, 0, 0))  # no tile on the diagonal
            mesh = ax.pcolormesh(np.arange(len(subj) + 1) - 0.5, np.arange(len(subj) + 1) - 0.5,
                                 np.ma.masked_invalid(M.to_numpy(float)), cmap=cm, vmin=vmin, vmax=vmax,
                                 edgecolors="black", linewidth=0.3)
            ax.set_aspect("equal")
            ax.set_xticks(range(len(subj)), subj if i == len(rows) - 1 else [], fontsize=6, rotation=90)
            ax.set_yticks(range(len(subj)), subj if j == 0 else [], fontsize=6)
            ax.tick_params(length=0)
            if i == 0:
                C.strip(ax, c)
            if j == len(cols) - 1:
                C.strip(ax, r, side="right")
    fig.supxlabel(xlabel, fontsize=7)
    fig.supylabel(ylabel, fontsize=7)
    fig.suptitle(title, fontsize=6, x=0.08, ha="left")
    C.black_framed_colorbar(fig, mesh, [0.9, 0.4, 0.015, 0.2], legend_title)
    C.save(fig, path)


def shared_number_of_asvs(ctx):
    ps = ctx.ps
    results = []
    for cutoff in [0.01, 0.001, 0.0001]:
        rel = ps.subset_samples(ps.sam["total_reads"] > 10000).relative()
        rel = rel.prune_taxa(rel.taxa_above(cutoff))
        present = rel.otu > cutoff  # ASVs per sample above the cutoff
        has_any = present.any(axis=1)
        present = present[has_any]
        sam = rel.sam.loc[present.index]
        for origin, idx in sam.groupby("Sample_origin3").groups.items():
            P = present.loc[idx].to_numpy(float)
            shared = P @ P.T  # number of ASVs shared by each pair of samples
            subj = sam.loc[idx, "Subject_ID"].to_numpy()
            i1, i2 = np.where(subj[:, None] != subj[None, :])  # pairs of samples from different subjects
            results.append(pd.DataFrame({"Sample_origin3": origin, "Subject1": subj[i1], "Subject2": subj[i2],
                                         "n_shared": shared[i1, i2], "cutoff": cutoff_label(cutoff, False)}))
    all_results = pd.concat(results, ignore_index=True)
    g = all_results.groupby(["Subject1", "Subject2", "Sample_origin3", "cutoff"])["n_shared"]
    summary_by_subject_pair = pd.DataFrame({"mean_shared": g.mean(), "sd_shared": g.std(),
                                            "n_comparisons": g.size()}).reset_index()
    g = all_results.groupby(["Sample_origin3", "cutoff"])["n_shared"]
    print("\nShared ASVs between samples of different subjects:\n",
          pd.DataFrame({"mean_shared": g.mean(), "median_shared": g.median(), "sd_shared": g.std(),
                        "n_comparisons": g.size()}).round(2))

    folder = FIG / "Weeklong-Shared-ASVs" / "No"
    _subject_tiles(summary_by_subject_pair, "mean_shared", folder / "All-subjects.pdf", (10, 9),
                   "Shared ASVs Between All Subject Pairs", "# Shared\nASVs")
    for region in ctx.samdf["Sample_origin3"].dropna().unique():
        for cutoff_val in all_results["cutoff"].unique():
            d = summary_by_subject_pair[(summary_by_subject_pair["Sample_origin3"] == region)
                                        & (summary_by_subject_pair["cutoff"] == cutoff_val)]
            _subject_tiles(d, "mean_shared", folder / f"All-subjects-{region}-{cutoff_val}.pdf", (9, 7),
                           "Shared ASVs Between All Subject Pairs", "# Shared\nASVs", vmin=0)


def shared_abundance_of_asvs(ctx):
    ps = ctx.ps
    results = []
    for cutoff in [0.01, 0.001, 0.0001]:
        rel = ps.subset_samples(ps.sam["total_reads"] > 10000).relative()
        sam = rel.sam
        for origin, idx in sam.groupby("Sample_origin3").groups.items():
            RA = rel.otu.loc[idx]
            subj = sam.loc[idx, "Subject_ID"]
            subj_list = list(dict.fromkeys(subj))
            # ASVs above the cutoff in any sample of each subject
            U = pd.DataFrame({s: (RA[subj == s] > cutoff).any(axis=0) for s in subj_list}).T
            # total abundance, in every sample, of each subject's ASV set
            S = pd.DataFrame(RA.to_numpy() @ U.T.to_numpy(float), index=RA.index, columns=subj_list)
            for s1, s2 in itertools.permutations(subj_list, 2):
                in_s2 = S.loc[subj[subj == s2].index, s1]
                results.append({"Subject1": s1, "Subject2": s2, "Sample_origin3": origin,
                                "n_asvs_subject1": int(U.loc[s1].sum()),
                                "avg_abundance_in_subject2": in_s2.mean() if U.loc[s1].any() else 0.0,
                                "n_samples_subject2": len(in_s2), "cutoff": cutoff_label(cutoff, False)})
    all_results = pd.DataFrame(results)
    all_results["pct"] = 100 * all_results["avg_abundance_in_subject2"]
    folder = FIG / "Weeklong-Shared-ASVs" / "Abundance"
    labels = dict(title="Percent shared ASVs between all subject pairs", legend_title="% Shared\nASVs",
                  vmin=0, vmax=100, xlabel="ASVs in Subject 1 at X cutoff", ylabel="% abundance of ASVs in Subject 2")
    _subject_tiles(all_results, "pct", folder / "All-subjects.pdf", (10, 9), **labels)
    for region in ctx.samdf["Sample_origin3"].dropna().unique():
        for cutoff_val in all_results["cutoff"].unique():
            d = all_results[(all_results["Sample_origin3"] == region) & (all_results["cutoff"] == cutoff_val)]
            _subject_tiles(d, "pct", folder / f"All-subjects-{region}-{cutoff_val}.pdf", (9, 7), **labels)


def most_prevalent_asvs(ctx):
    ps = ctx.ps
    df = ps.subset_samples(ps.sam["total_reads"] > 10000).relative()
    df = df.prune_taxa(df.taxa_above(cutoff_MT)).psmelt()
    df = df[df["Abundance"] > cutoff_MT]
    # ASVs detectable at >1% for each subject and sample type
    detectable_asvs = (df.groupby(["Subject_ID", "Sample_origin3", "Feature"])
                       .agg(n_samples_detected=("Sample", "size"), Taxon=("Taxon", "first")).reset_index())
    # prevalence = number of subjects with each ASV
    asv_prevalence = (detectable_asvs.groupby(["Sample_origin3", "Feature", "Taxon"])
                      .agg(n_subjects=("Subject_ID", "nunique"),
                           subjects_list=("Subject_ID", lambda s: ", ".join(sorted(s.unique()))),
                           mean_samples_detected=("n_samples_detected", "mean"),
                           total_samples=("n_samples_detected", "sum")).reset_index())
    asv_prevalence = asv_prevalence.sort_values(["Sample_origin3", "n_subjects", "mean_samples_detected"],
                                                ascending=[True, False, False], kind="stable")
    folder = FIG / "Weeklong-Shared-ASVs"
    origins = ctx.samdf["Sample_origin3"].dropna().unique()

    for origin in origins:
        prev = asv_prevalence[asv_prevalence["Sample_origin3"] == origin]
        features_to_keep = prev.loc[prev["n_subjects"] >= 2, "Feature"]
        temp = detectable_asvs[(detectable_asvs["Sample_origin3"] == origin)
                               & detectable_asvs["Feature"].isin(features_to_keep)]
        mat = temp.assign(feature_taxon=temp["Feature"] + "." + temp["Taxon"]).pivot_table(
            index="feature_taxon", columns="Subject_ID", values="n_samples_detected", fill_value=0)
        pheatmap(mat, folder / f"All-subjects-{origin}.pdf", 8, 0.1 * temp["Feature"].nunique() + 2)

    for origin in origins:
        prev = asv_prevalence[asv_prevalence["Sample_origin3"] == origin]
        # NOTE (R difference): the R chunk uses `top10_features` without defining it. The saved
        # R figures show the 10 most prevalent ASVs of each sample type, i.e. the first 10 rows of
        # asv_prevalence (sorted by n_subjects, then mean_samples_detected) for that origin.
        top10_features = prev["Feature"].head(10)
        temp = detectable_asvs[(detectable_asvs["Sample_origin3"] == origin)
                               & detectable_asvs["Feature"].isin(top10_features)]
        # complete(Subject_ID, nesting(Feature, Taxon)): every subject x ASV, NA if not detected
        grid = pd.MultiIndex.from_product([sorted(temp["Subject_ID"].unique()),
                                           list(temp[["Feature", "Taxon"]].drop_duplicates().itertuples(index=False))])
        full = pd.DataFrame([(s, f, t) for s, (f, t) in grid], columns=["Subject_ID", "Feature", "Taxon"])
        full = full.merge(temp, on=["Subject_ID", "Feature", "Taxon"], how="left")
        full = full.merge(prev[["Feature", "Taxon", "n_subjects"]].drop_duplicates(), on=["Feature", "Taxon"])
        ycols = ["Feature", "Taxon", "n_subjects"]
        order = C.r_interaction_order(full, ycols)
        ylabels = list(dict.fromkeys(C.interaction_labels(full, ycols).iloc[order]))
        xlabels = sorted(full["Subject_ID"].unique())
        full["y"] = C.interaction_labels(full, ycols)
        M = full.pivot(index="y", columns="Subject_ID", values="n_samples_detected").reindex(index=ylabels,
                                                                                            columns=xlabels)
        h = 0.2 * full["Feature"].nunique()
        fig = plt.figure(figsize=(6, max(h, 1)))
        ax = fig.add_axes([0.42, 0.12, 0.42, 0.85])
        C.theme_grey(ax, grid=False)
        mesh = C.tile_heatmap(ax, M.to_numpy(float), xlabels, ylabels, C.GRADIENT_WHITE_BLUE, 0,
                              np.nanmax(M.to_numpy(float)), lw=0.4)
        C.black_framed_colorbar(fig, mesh, [0.87, 0.3, 0.025, 0.5], "n_samples\n_detected")
        C.save(fig, folder / f"All-subjects-{origin}-top.pdf")


def pheatmap(mat, path, width, height):
    """pheatmap(cluster_rows/cols = TRUE, euclidean, complete; 0 = black, else white -> blue)."""
    data = mat.to_numpy(float)
    fig = plt.figure(figsize=(width, height))
    W, H = width, height
    dend_w, dend_h, label_w = 0.6, 0.6, 2.2
    heat_w = W - dend_w - label_w - 1.0
    heat_h = H - dend_h - 0.5
    row_order, col_order = np.arange(data.shape[0]), np.arange(data.shape[1])
    if data.shape[0] > 1:
        Z = linkage(pdist(data, "euclidean"), "complete")
        axd = fig.add_axes([0.1 / W, 0.3 / H, dend_w / W, heat_h / H])
        dn = dendrogram(Z, orientation="left", ax=axd, no_labels=True, color_threshold=0,
                        above_threshold_color="black")
        row_order = np.array(dn["leaves"])
        axd.invert_yaxis()
        axd.axis("off")
    if data.shape[1] > 1:
        Z = linkage(pdist(data.T, "euclidean"), "complete")
        axc = fig.add_axes([(0.1 + dend_w) / W, (0.3 + heat_h) / H, heat_w / W, dend_h / H])
        dn = dendrogram(Z, ax=axc, no_labels=True, color_threshold=0, above_threshold_color="black")
        col_order = np.array(dn["leaves"])
        axc.axis("off")
    ax = fig.add_axes([(0.1 + dend_w) / W, 0.3 / H, heat_w / W, heat_h / H])
    vmax = max(data.max(), 0.01)
    cmap = C.GRADIENT_WHITE_BLUE.copy()
    cmap.set_under("black")
    D = data[np.ix_(row_order, col_order)]
    mesh = ax.pcolormesh(D, cmap=cmap, vmin=0.01, vmax=vmax, edgecolors="black", linewidth=0.3)
    ax.set_xlim(0, D.shape[1])
    ax.set_ylim(D.shape[0], 0)
    ax.yaxis.tick_right()
    ax.set_yticks(np.arange(D.shape[0]) + 0.5, mat.index[row_order], fontsize=6)
    ax.set_xticks(np.arange(D.shape[1]) + 0.5, mat.columns[col_order], fontsize=6, rotation=0)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cax = fig.add_axes([(W - 0.6) / W, (H - 1.6) / H, 0.12 / W, 1.0 / H])
    cb = fig.colorbar(mesh, cax=cax, extend="min", extendfrac=0.02)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6, length=0)
    C.save(fig, path)


#######################################
# ASV fluctuations
#######################################


def _subset_origin_subject(ctx, sid, origin):
    s = ctx.ps.sam
    return ctx.ps.subset_samples((s["Subject_ID"] == sid) & (s["Sample_origin3"] == origin) & (s["total_reads"] > 10000))


def _time_axis(df):
    """x = interaction(Collection_time, Collection_date_reformat, Sample_ID): sorted by Sample_ID."""
    cols = ["Collection_time", "Collection_date_reformat", "Sample_ID"]
    order = C.r_interaction_order(df, cols)
    keys = C.interaction_labels(df, cols)
    cats = list(dict.fromkeys(keys.iloc[order]))
    return keys.map({k: i for i, k in enumerate(cats)}), cats


def _log_y(values, lo):
    """Values on a log10 axis with lower limit lo: zeros sit on the panel edge (-Inf), small ones are dropped."""
    v = np.asarray(values, float)
    out = v.copy()
    out[(v > 0) & (v < lo)] = np.nan
    out[v == 0] = lo
    return out


def _kit_points(ax, x, y, kit_sets, size=1.0, marker="o"):
    fills = [C.GREY50 if pd.isna(k) else kit_colors.get(k, C.GREY50) for k in kit_sets]
    C.points(ax, x, y, fills, [21 if marker == "o" else marker] * len(x), size=size, stroke=0.5)


def fluctuation_table(ctx, plot=True):
    """ASV fluctuations (0.01 cutoff): per-feature plots + mean/variance table for Taylor's law."""
    if "ASV_fluctuation" in ctx.cache and not plot:
        return ctx.cache["ASV_fluctuation"]
    rows = []
    base = FIG / "Weeklong-ASV-Fluctuation-0p01"
    for origin in ctx.samdf["Sample_origin3"].dropna().unique():
        for sid in subjects(ctx):
            ps2plot = _subset_origin_subject(ctx, sid, origin)
            if ps2plot.nsamples() == 0:
                continue
            ps2plot, keep = relabund_pruned(ps2plot, cutoff_MT, renormalize=False)  # normalize (NO PRUNING)
            df2plot = set_ordered_factors(C.set_family_order(ps2plot.psmelt(), ctx.taxa_order))
            df2plot["xpos"], cats = _time_axis(df2plot)
            features = list(dict.fromkeys(df2plot.loc[df2plot["Abundance"] > cutoff_MT, "Feature"]))
            if plot:
                _fluctuation_grid(df2plot, features, base / sid / f"ASV-fluctuation-{sid}-{origin}.pdf")
            for otu in features:
                d = df2plot[df2plot["Feature"] == otu].sort_values("xpos")
                if plot:
                    W = max(0.3 * d["Sample_ID"].nunique(), 1.2)
                    fig = plt.figure(figsize=(W, 2))
                    label_in = 0.15 + 0.05 * max(len(c) for c in cats)  # room for rotated labels
                    ph = max(2 - label_in - 0.25, 0.3)
                    ax = fig.add_axes([0.45 / W, label_in / 2, max(W - 1.1, 0.3) / W, ph / 2])
                    C.theme_grey(ax)
                    y = _log_y(d["Abundance"], 1e-7)
                    ax.plot(d["xpos"], y, color="black", linewidth=0.2)
                    _kit_points(ax, d["xpos"], y, d["Kit_set"].astype(object))
                    ax.set_yscale("log")
                    ax.set_ylim(1e-7, 1)
                    C.log_ticks(ax, "y", -6, 0, step=2)
                    ax.set_xticks(range(len(cats)), cats, rotation=90, fontsize=6)
                    ax.tick_params(axis="x", length=0)
                    ax.set_xlim(-0.6, len(cats) - 0.4)
                    ax.set_ylabel("Abundance")
                    ax.set_title(f"{otu}: {d['Taxon'].iloc[0]}", fontsize=6)
                    _kit_legend(ax, d["Kit_set"])
                    C.save(fig, base / sid / origin / f"{origin}-{otu}.pdf")
                rows.append({"Subject": sid, "Color": d["Color"].iloc[0], "Feature": otu,
                             "Mean": d["Abundance"].mean(), "Variance": d["Abundance"].var(),
                             "Sample_origin": origin})
    table = pd.DataFrame(rows)
    ctx.cache["ASV_fluctuation"] = table
    return table


def _kit_legend(ax, kit_sets):
    present = [k for k in KIT_SET_LEVELS if (kit_sets.astype(object) == k).any()]
    handles = [plt.Line2D([], [], marker="o", linestyle="", markerfacecolor=kit_colors[k], markeredgecolor="black",
                          markeredgewidth=0.4, markersize=3.5, label=k) for k in present]
    ax.legend(handles=handles, title="Kit_set", loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=6,
              title_fontsize=6, frameon=False, handletextpad=0.2)


def _fluctuation_grid(df2plot, features, path):
    """All features of one subject/origin: facet_wrap(~Feature, ncol = 12), 16 x 8 in."""
    feats = sorted(features, key=C.r_sort_key)
    if not feats:
        return
    nrow = int(np.ceil(len(feats) / 12))
    fig, axes = plt.subplots(nrow, 12, figsize=(16, 8), sharex=True, sharey=True, squeeze=False)
    fig.subplots_adjust(left=0.05, right=0.94, top=0.96, bottom=0.05, wspace=0.08, hspace=0.35)
    for ax in axes.flat[len(feats):]:
        ax.set_visible(False)
    for ax, f in zip(axes.flat, feats):
        C.theme_grey(ax)
        d = df2plot[df2plot["Feature"] == f].sort_values("xpos")
        y = _log_y(d["Abundance"], 1e-7)
        ax.plot(d["xpos"], y, color="black", linewidth=0.2)
        _kit_points(ax, d["xpos"], y, d["Kit_set"].astype(object))
        ax.set_yscale("log")
        ax.set_ylim(1e-7, 1)
        ax.tick_params(axis="x", labelbottom=False, length=0)
        C.strip(ax, f)
    C.log_ticks(axes[0, 0], "y", -6, 0, step=2)
    fig.supylabel("Abundance", fontsize=7)
    _kit_legend(axes[0, min(len(feats), 12) - 1], df2plot["Kit_set"])
    C.save(fig, path)


def asv_fluctuations(ctx):
    fluctuation_table(ctx, plot=True)


def fluctuation_variance(ctx):
    """Taylor's law: log10(variance) vs log10(mean) of each feature's relative abundance."""
    table = fluctuation_table(ctx, plot=False)
    table["Sample_origin"] = pd.Categorical(table["Sample_origin"], categories=ORIGIN3_LEVELS)
    base = FIG / "Weeklong-ASV-Fluctuation-0p01"
    all_slopes = []
    for sid in subjects(ctx):
        t = table[table["Subject"] == sid]
        if t.empty:
            continue
        origins = [o for o in ORIGIN3_LEVELS if (t["Sample_origin"] == o).any()]
        fig, axes = plt.subplots(1, len(origins), figsize=(6, 3), sharey=True, squeeze=False)
        fig.subplots_adjust(left=0.1, right=0.97, top=0.82, bottom=0.18, wspace=0.08)
        for ax, origin in zip(axes[0], origins):
            d = t[t["Sample_origin"] == origin]
            ok = (d["Mean"] > 0) & (d["Variance"] > 0)
            lx, ly = np.log10(d.loc[ok, "Mean"]), np.log10(d.loc[ok, "Variance"])
            slope = np.polyfit(lx, ly, 1)[0] if len(lx) >= 2 else np.nan  # lm(log10(Variance) ~ log10(Mean))
            all_slopes.append({"Sample_origin": origin, "slope": slope, "Subject": sid})
            C.theme_grey(ax)
            ax.set_box_aspect(1)
            ax.scatter(d["Mean"], d["Variance"], s=(2 * C.PT_PER_MM) ** 2 * 0.6,
                       c=[c if isinstance(c, str) else C.GREY50 for c in d["Color"]], edgecolors="black",
                       linewidths=0.5, zorder=3)
            # geom_smooth(method = 'lm') only sees points inside the x-axis limits (1e-4 to 1)
            inside = ok & (d["Mean"] >= 1e-4) & (d["Mean"] <= 1)
            if inside.sum() >= 2:
                fx, fy = np.log10(d.loc[inside, "Mean"]), np.log10(d.loc[inside, "Variance"])
                b, a = np.polyfit(fx, fy, 1)
                xx = np.array([fx.min(), fx.max()])
                ax.plot(10 ** xx, 10 ** (a + b * xx), color="red", linestyle="--", linewidth=0.2)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlim(1e-4, 1)
            C.log_ticks(ax, "x", -4, 0)
            ax.text(5e-4, 5e-3, f"  β = {slope:.2f}", color="red", fontsize=8, ha="left", va="top")
            C.strip(ax, origin)
        fig.supxlabel("Mean relative abundance", fontsize=7)
        fig.supylabel("Relative abundance variance", fontsize=7)
        fig.suptitle("Scatterplot of mean vs variance of each feature's relative abundance", fontsize=6, x=0.1,
                     ha="left")
        C.save(fig, base / "Taylors-law" / f"Mean-vs-var-{sid}.pdf")

    s = pd.DataFrame(all_slopes)
    ys = sorted(s["Subject"].unique())
    xs = [o for o in ORIGIN3_LEVELS if (s["Sample_origin"] == o).any()]
    M = s.pivot(index="Subject", columns="Sample_origin", values="slope").reindex(index=ys, columns=xs)
    fig = plt.figure(figsize=(2.5, 4))
    ax = fig.add_axes([0.15, 0.08, 0.5, 0.88])
    C.theme_grey(ax, grid=False)
    mesh = C.tile_heatmap(ax, M.to_numpy(float), xs, ys, C.GRADIENT_WHITE_BLUE, np.nanmin(M.to_numpy()),
                          np.nanmax(M.to_numpy()), lw=0.5)
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            if not np.isnan(M.iat[i, j]):
                ax.text(j, i, f"{M.iat[i, j]:.2f}", ha="center", va="center", fontsize=5.7)
    C.black_framed_colorbar(fig, mesh, [0.75, 0.4, 0.05, 0.2], "slope")
    C.save(fig, base / "Fluctuation-slopes-all-subjects.pdf")


#######################################
# Co-correlated ASVs
#######################################


def _correlations(ps2plot, cutoff):
    """CLR-transform relative abundances (pseudocount 1e-7) and correlate ASVs (Hmisc::rcorr)."""
    ps2plot, keep = relabund_pruned(ps2plot, cutoff, renormalize=False)  # normalize (NO PRUNING)
    otu = ps2plot.otu
    r, p = C.rcorr(C.clr(otu.to_numpy() + 1e-7))
    padj = C.fdr_matrix(p)
    i, j = np.triu_indices(len(keep), 1)
    detected = (otu.to_numpy() > 1e-7).astype(float)
    n_obs = (detected.T @ detected)[i, j]  # samples where both features are actually detected
    return otu, detected, pd.DataFrame({"feature1": otu.columns[i], "feature2": otu.columns[j], "r": r[i, j],
                                        "fdr_p": padj[i, j], "n_obs": n_obs})


def _all_samples_long(ctx):
    """psmelt of all >10k samples, relative abundance, taxa >1% anywhere (otu_map source)."""
    ps = ctx.ps
    ps2plot, _ = relabund_pruned(ps.subset_samples(ps.sam["total_reads"] > 10000), cutoff_MT, renormalize=False)
    df2plot = set_ordered_factors(C.set_family_order(ps2plot.psmelt(), ctx.taxa_order))
    otu_map = df2plot[["Feature", "OTU", "Taxon"]].drop_duplicates()
    return df2plot, otu_map.set_index("OTU")


def _pair_plot(df, f1, f2, fill, palette, title, path):
    """Scatter of two features' abundances on log axes (1e-4 to 1), lm line, shapes by Region."""
    id_cols = ["Sample_ID", "Kit_ID", "Kit_set", "Region", "Prediction", "Sample_origin3", "Ingestion_time",
               "Ingestion_date_reformat", "Collection_time", "Collection_date_reformat", "Transit_time_h", "Subject_ID"]
    d = df[df["Feature"].isin([f1, f2])].copy()
    d["which"] = np.where(d["Feature"] == f1, "Feature1_abund", "Feature2_abund")
    keys = d[id_cols].astype(object).fillna("<NA>")
    wide = d.assign(**{c: keys[c] for c in id_cols}).pivot_table(index=id_cols, columns="which", values="Abundance",
                                                                aggfunc="mean", fill_value=0).reset_index()
    for c in ["Feature1_abund", "Feature2_abund"]:
        if c not in wide:
            wide[c] = 0.0
    fig = plt.figure(figsize=(3, 3))
    ax = C.scatter_panel(fig, 5.0, left_in=0.6, bottom_in=0.5)
    C.theme_grey(ax)
    x, y = _log_y(wide["Feature1_abund"], 1e-4), _log_y(wide["Feature2_abund"], 1e-4)
    vals = wide[fill].replace("<NA>", np.nan)
    fills = [C.GREY50 if pd.isna(v) else palette.get(v, C.GREY50) for v in vals]
    C.points(ax, x, y, fills, [C.REGION_SHAPES.get(r, 21) for r in wide["Region"]], size=2)
    # stat_smooth drops non-finite values (zeros on a log axis) and values outside the limits
    a, b = wide["Feature1_abund"].to_numpy(float), wide["Feature2_abund"].to_numpy(float)
    ok = (a >= 1e-4) & (b >= 1e-4)
    if ok.sum() >= 2:
        slope, icpt = np.polyfit(np.log10(a[ok]), np.log10(b[ok]), 1)
        xx = np.log10([a[ok].min(), a[ok].max()])
        ax.plot(10 ** xx, 10 ** (icpt + slope * xx), color="black", linestyle="--", linewidth=0.2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-4, 1)
    ax.set_ylim(1e-4, 1)
    C.log_ticks(ax, "x", -4, 0)
    C.log_ticks(ax, "y", -4, 0)
    ax.set_xlabel(f1)
    ax.set_ylabel(f2)
    ax.set_title(title, fontsize=6)
    C.save(fig, path)


def cocorrelated_asvs_individual(ctx):
    cor_long = []
    for origin in ctx.samdf["Sample_origin3"].dropna().unique():
        for sid in subjects(ctx):
            ps2plot = _subset_origin_subject(ctx, sid, origin)
            if ps2plot.nsamples() <= 4:  # Skip if not enough samples
                print(f"Skipping {sid} - {origin}: only {ps2plot.nsamples()} samples")
                continue
            _, _, temp = _correlations(ps2plot, cutoff_MT)
            cor_long.append(temp.assign(Subject_ID=sid, Sample_origin=origin))
    cor_long = pd.concat(cor_long, ignore_index=True)
    df2plot, otu_map = _all_samples_long(ctx)
    cor_long_filter = cor_long[(cor_long["r"].abs() > 0.95) & (cor_long["n_obs"] > 4)]
    print("\nStrong within-subject correlations (|r| > 0.95, n_obs > 4):\n",
          cor_long_filter.groupby(["Subject_ID", "Sample_origin"]).size().rename("n_correlations"))
    base = FIG / "Weeklong-ASV-Fluctuation-0p01"
    for row in cor_long_filter.itertuples(index=False):
        f1, f2 = otu_map.at[row.feature1, "Feature"], otu_map.at[row.feature2, "Feature"]
        sid, origin = row.Subject_ID, row.Sample_origin
        d = df2plot[(df2plot["Subject_ID"] == sid) & (df2plot["Sample_origin3"] == origin)]
        title = (f"{otu_map.at[row.feature1, 'Taxon']} vs {otu_map.at[row.feature2, 'Taxon']}\n"
                 f"{sid} {origin} r: {round(row.r, 3)} p-val: {round(row.fdr_p, 3)}")
        _pair_plot(d.assign(Kit_set=d["Kit_set"].astype(object)), f1, f2, "Kit_set", kit_colors, title,
                   base / sid / f"{origin}-correlations" / f"{sid}-{origin}-{f1}-{f2}.pdf")


def cocorrelated_asvs_all_subjects(ctx):
    ps = ctx.ps
    df2plot, otu_map = _all_samples_long(ctx)
    cor_long = []
    for origin in ctx.samdf["Sample_origin3"].dropna().unique():
        ps2plot = ps.subset_samples((ps.sam["Sample_origin3"] == origin) & (ps.sam["total_reads"] > 10000))
        if ps2plot.nsamples() <= 4:
            print(f"Skipping {origin}: only {ps2plot.nsamples()} samples")
            continue
        otu, detected, temp = _correlations(ps2plot, cutoff_MT)
        # number of subjects among samples where both features are detected
        subj = ps2plot.sam.loc[otu.index, "Subject_ID"].to_numpy()
        subj_onehot = pd.get_dummies(subj).to_numpy(float)  # samples x subjects
        col = {f: k for k, f in enumerate(otu.columns)}
        i = temp["feature1"].map(col).to_numpy()
        j = temp["feature2"].map(col).to_numpy()
        n_subj = np.empty(len(temp), int)
        for start in range(0, len(temp), 20000):  # chunked to bound memory
            sl = slice(start, start + 20000)
            both = detected[:, i[sl]] * detected[:, j[sl]]  # samples x pairs
            n_subj[sl] = ((both.T @ subj_onehot) > 0).sum(axis=1)
        cor_long.append(temp.assign(n_subj=n_subj, Sample_origin=origin))
    cor_long = pd.concat(cor_long, ignore_index=True)
    f = cor_long[(cor_long["r"].abs() > 0.75) & (cor_long["n_obs"] > 4) & (cor_long["n_subj"] > 5)
                 & (cor_long["fdr_p"] < 0.05)]
    print("\nCross-subject correlations (|r| > 0.75, n_obs > 4, n_subj > 5, FDR < 0.05):\n",
          f.groupby("Sample_origin").size().rename("n_correlations"))
    # NOTE (R difference): R saves to ".../Weeklong-ASV-Fluctuation-0 p01/All/..." (stray space, and
    # the folders are never created); here the files go to Weeklong-ASV-Fluctuation-0p01/All/.
    base = FIG / "Weeklong-ASV-Fluctuation-0p01" / "All"
    for row in f.itertuples(index=False):
        f1, f2 = otu_map.at[row.feature1, "Feature"], otu_map.at[row.feature2, "Feature"]
        origin = row.Sample_origin
        d = df2plot[df2plot["Sample_origin3"] == origin]
        title = (f"{otu_map.at[row.feature1, 'Taxon']} vs {otu_map.at[row.feature2, 'Taxon']}\n"
                 f"{origin} r: {round(row.r, 3)} p-val: {round(row.fdr_p, 3)}")
        subj_levels = sorted(d.loc[d["Feature"].isin([f1, f2]), "Subject_ID"].unique())
        _pair_plot(d, f1, f2, "Subject_ID", C.default_palette(subj_levels), title,
                   base / f"{origin}-correlations" / f"All-{origin}-{f1}-{f2}.pdf")


#######################################
# Run
#######################################

SECTIONS = {
    "sequencer": sequencer_stats,
    "composition": composition_by_sample_origin,
    "composition_paired": composition_paired_cap_stool,
    "composition_kit_set": composition_all_by_kit_set,
    "composition_clustering": composition_capscan_clustering,
    "heatmap_0p01": asv_heatmap_0p01,
    "heatmap_0p001": asv_heatmap_0p001,
    "alpha": alpha_diversity,
    "pcoa_origin": pcoa_by_sample_origin,
    "pcoa_all": pcoa_all_samples,
    "weird_unifrac": weird_unifrac,
    "paired_distances": distances_paired_cap_stool,
    "total_asvs": total_asvs,
    "shared_asvs": shared_number_of_asvs,
    "shared_abundance": shared_abundance_of_asvs,
    "prevalent_asvs": most_prevalent_asvs,
    "fluctuation": asv_fluctuations,
    "fluctuation_variance": fluctuation_variance,
    "cocorrelation_individual": cocorrelated_asvs_individual,
    "cocorrelation_all": cocorrelated_asvs_all_subjects,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sections", nargs="+", default=list(SECTIONS), help="sections to run (default: all)")
    parser.add_argument("--list", action="store_true", help="list section names and exit")
    args = parser.parse_args()
    if args.list:
        print("\n".join(SECTIONS))
        return
    unknown = set(args.sections) - set(SECTIONS)
    if unknown:
        parser.error(f"unknown sections: {sorted(unknown)}")
    t0 = time.time()
    ctx = standard_setup()
    print(f"Setup: {ctx.ps.nsamples()} samples x {ctx.ps.otu.shape[1]} ASVs ({time.time() - t0:.1f}s)")
    for name in args.sections:
        t = time.time()
        SECTIONS[name](ctx)
        print(f"[{name}] done in {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
