"""Shared code for the Weeklong food notebooks (20250402_Weeklong_Meat.Rmd and
20250402_Weeklong_Plants.Rmd), which are identical apart from the dataset.

Run through weeklong_meat.py or weeklong_plants.py. The chunks reuse the Weeklong 16S
helpers (weeklong_16s.py); figures go to 3-figures_python/ with the same names as 3-figures/.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

import config as C
import weeklong_16s as W
from config import plt

FIG = C.FIG_DIR


@dataclass
class Dataset:
    name: str  # "Meat" or "Plants": file prefix and folder names
    setup_fn: object  # C.setup_tables_meat / C.setup_tables_plants
    data_dir: str


MEAT = Dataset("Meat", C.setup_tables_meat, "DADA2-weeklong-meat")
PLANTS = Dataset("Plants", C.setup_tables_plants, "DADA2-weeklong-plants")


#######################################
# Standard Setup
#######################################


def standard_setup(ds: Dataset):
    """Same as the 16S setup, then ps <- ps %>% subset_samples(Group %in% c("LONGIT", "Blank")).

    NOTE (R behaviour kept): samdf (used by the sequencer histograms) still holds every row
    of Weeklong-meat-plants-sample-info.xlsx (meat and plant libraries, all Groups), so
    libraries from the other dataset count as samples with 0 reads.
    """
    return W.standard_setup(ds.setup_fn, ds.data_dir, "Weeklong-meat-plants-sample-info.xlsx",
                            groups=["LONGIT", "Blank"])


#######################################
# Sequencer statistics
#######################################


def sequencer_stats(ctx, ds):
    W.sequencer_stats(ctx, prefix=f"{ds.name}-")


#######################################
# Composition 0 read cutoff, highlight <10k reads
#######################################


def _blank_composition(ctx, ds, folder):
    """### BLANKS: stacked bars per blank, and the same bars laid out by plate row and column."""
    ps2plot = ctx.ps.subset_samples(ctx.ps.sam["Group"] == "Blank")
    ps2plot, _ = W.relabund_pruned(ps2plot, W.cutoff_MT)
    df2plot = C.set_family_order(ps2plot.psmelt(), ctx.taxa_order)
    scale = C.get_color_mapping(df2plot)
    C.composition_plot(df2plot, ["total_reads", "Sample_no"], None, scale, folder / "Composition-blank.pdf",
                       0.5 * df2plot["Sample_no"].nunique() + 1, 3, W.red_if_small_discrete)
    plate_composition(df2plot, scale, folder / "Composition-blank-plate-format.pdf", 8, 6)


def plate_composition(df, scale, path, width, height):
    """geom_bar(aes(x = Col)) + facet_nested(rows = vars(Plate, Row), scales/space = 'free').

    One panel per (Plate, Row); the x axis (plate column) is shared, strips sit on the right
    with Plate merged across its rows.
    """
    colours = dict(zip(scale["breaks"], scale["values"]))
    fam_rank = {f: i for i, f in enumerate(df["Family2"].cat.categories)}
    panels = C.nested_panels(df, ["Plate", "Row"])
    cols = C.sorted_levels(df["Col"])
    xpos = {c: i for i, c in enumerate(cols)}
    n = len(panels)
    left, right, bottom, top, gap = 0.55, 0.45, 0.3, 0.1, 0.04
    ph = (height - bottom - top - gap * (n - 1)) / n
    fig = plt.figure(figsize=(width, height))
    axes = []
    for k, (plate, row) in enumerate(panels):
        y0 = height - top - (k + 1) * ph - k * gap
        ax = fig.add_axes([left / width, y0 / height, (width - left - right) / width, ph / height])
        C.theme_blank(ax)
        d = df[(df["Plate"] == plate) & (df["Row"] == row) & (df["Abundance"] > 0)]
        for col, rows in d.groupby("Col", sort=False):
            rank = rows["Family2"].map(lambda f: fam_rank.get(f, len(fam_rank))).to_numpy()
            rows = rows.iloc[np.lexsort((np.arange(len(rows)), -rank))]  # first family on top
            bottoms = np.concatenate([[0], np.cumsum(rows["Abundance"].to_numpy())[:-1]])
            ax.bar([xpos[col]] * len(rows), rows["Abundance"], bottom=bottoms, width=0.9,
                   color=[colours.get(f, C.GREY50) for f in rows["Family2"]], edgecolor="black", linewidth=0.25)
        ax.set_xlim(-0.6, len(cols) - 0.4)
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0.00", "0.25", "0.50", "0.75", "1.00"], fontsize=4.5)
        ax.tick_params(length=0)
        ax.set_xticks(range(len(cols)), cols if k == n - 1 else [])
        # inner strip: Row (full panel height)
        box = ax.get_position()
        x = (width - right + 0.03) / width
        fig.patches.append(plt.Rectangle((x, box.y0), 0.16 / width, box.height, transform=fig.transFigure,
                                         facecolor="#D9D9D9", edgecolor="none"))
        fig.text(x + 0.08 / width, box.y0 + box.height / 2, C.fmt_facet(row), rotation=-90, ha="center",
                 va="center", fontsize=6)
        axes.append(ax)
    # outer strip: Plate, merged across its rows
    i = 0
    while i < n:
        j = i
        while j + 1 < n and panels[j + 1][0] == panels[i][0]:
            j += 1
        top_box, bot_box = axes[i].get_position(), axes[j].get_position()
        x = (width - right + 0.21) / width
        fig.patches.append(plt.Rectangle((x, bot_box.y0), 0.16 / width, top_box.y1 - bot_box.y0,
                                         transform=fig.transFigure, facecolor="#D9D9D9", edgecolor="none"))
        fig.text(x + 0.08 / width, (top_box.y1 + bot_box.y0) / 2, C.fmt_facet(panels[i][0]), rotation=-90,
                 ha="center", va="center", fontsize=6)
        i = j + 1
    fig.text(0.12 / width, 0.5, "Relative Abundance", rotation=90, ha="center", va="center", fontsize=7)
    C.save(fig, path)


def composition_by_sample_origin(ctx, ds):
    ps = ctx.ps
    folder = FIG / "Weeklong-Food" / f"{ds.name}-composition-0p01"
    _blank_composition(ctx, ds, folder)

    facets = ["Collection_date", "Collection_time", "Sample_origin2"]
    groups = [
        ("Saliva", ps.sam["Region"] == "Saliva", ["total_reads"], W.red_if_small_discrete),
        ("Stool", ps.sam["Region"] == "Stool", ["total_reads"], W.red_if_small_discrete),
        # Blanks have no Region; !Region %in% c(...) keeps them here, as in R
        ("Capscan", ~ps.sam["Region"].isin(["Stool", "Saliva"]), ["total_reads", "Region"],
         W.red_if_small_discrete_cap),
    ]
    for name, mask, xcols, labeller in groups:
        df2plot, scale = W._composition_df(ctx, ps.subset_samples(mask))
        sub = folder / f"{name}-collection"
        for sid in W.subjects(ctx):  # skips NA / "NA" subjects, as in R
            d = df2plot[df2plot["Subject_ID"] == sid]
            if d.empty:  # the Plants notebook skips these explicitly; R would fail on them otherwise
                continue
            C.composition_plot(d, xcols, facets, scale, sub / f"Composition-{name.lower()}-{sid}.pdf",
                               W._width(d), 4, labeller)
        C.legend_figure(scale, sub / f"Composition-{name.lower()}-legend.pdf", 4, 4, ncol=1)


#######################################
# ASV heatmap 10,000 read cutoff
#######################################


def asv_heatmap(ctx, ds):
    # Subjects with no qualifying samples are skipped (an empty subset makes R stop).
    W._asv_heatmaps(ctx, W.cutoff_MT, f"Weeklong-Food/{ds.name}-ASV-heatmap-0p01")


#######################################
# Run
#######################################

SECTIONS = {
    "sequencer": sequencer_stats,
    "composition": composition_by_sample_origin,
    "heatmap": asv_heatmap,
}


def main(ds: Dataset, doc: str):
    parser = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
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
    ctx = standard_setup(ds)
    print(f"{ds.name} setup: {ctx.ps.nsamples()} samples x {ctx.ps.otu.shape[1]} ASVs ({time.time() - t0:.1f}s)")
    for name in args.sections:
        t = time.time()
        SECTIONS[name](ctx, ds)
        print(f"[{name}] done in {time.time() - t:.1f}s")
