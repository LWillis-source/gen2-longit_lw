"""Diet log (by meal) next to stool detection, one figure per subject, same ingredient rows.

Left panel: the meal presence/absence grid from diet_log_meal_timeseries.py (days x breakfast,
lunch, dinner, not recorded). Right panel: the stool detection grid from
stool_detection_timeseries.py (stool samples in collection order). Both panels use the same
60 informative ingredients in the same order, so each row reads across from what was eaten
to what was detected. See those two scripts for how meals and detections are defined.

Output: diet_log_analyses/figures_Diet-logs/Diet-vs-stool/Diet-vs-stool-<subject>.png

Usage (from the repository root):
    python diet_log_analyses/diet_vs_stool_timeseries.py
"""

from __future__ import annotations

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import config as C
import diet_log_ingredients as D
import diet_log_meal_timeseries as M
import stool_detection_timeseries as S
from config import plt

OUT = D.OUT / "Diet-vs-stool"


def plot_subject(sid, days, cells, det, top, path, labels=None, title_rows=None):
    sid_txt = f"{int(sid):02d}"
    n_rows = len(top)
    n_samples = len(S.subject_samples(det, sid_txt))
    label_w, meal_count_w, panel_gap, stool_count_w, right = 2.75, 0.35, 0.35, 0.5, 0.2
    meal_w = M.meal_grid_width(days)
    stool_w = n_samples * S.COL_IN
    width = label_w + meal_w + meal_count_w + panel_gap + stool_w + stool_count_w + right
    width = max(width, 11.0)
    bottom, top_margin = 1.25, 2.65  # inches: legends + notes below; title, panel titles, column labels above
    grid_h = n_rows * S.CELL_IN
    height = grid_h + bottom + top_margin
    fig = plt.figure(figsize=(width, height), facecolor=D.BACKGROUND)

    x_meal = label_w
    x_stool = label_w + meal_w + meal_count_w + panel_gap
    ax_meal = fig.add_axes([x_meal / width, bottom / height, meal_w / width, grid_h / height], facecolor=D.BACKGROUND)
    ax_stool = fig.add_axes([x_stool / width, bottom / height, stool_w / width, grid_h / height],
                            facecolor=D.BACKGROUND)
    M.draw_meal_grid(ax_meal, sid, days, cells, top, show_labels=True, labels=labels)
    S.draw_stool_grid(ax_stool, sid_txt, det, top, show_labels=False)

    # faint guide lines every 5 rows, across both panels, to follow a row from diet to stool
    for i in range(5, n_rows, 5):
        y = (bottom + grid_h - i * S.CELL_IN) / height
        fig.add_artist(plt.Line2D([x_meal / width, (x_stool + stool_w) / width], [y, y], color="#D0D0D0", linestyle=":",
                                  linewidth=0.5, zorder=0))

    # panel titles
    panel_y = 1 - 0.72 / height
    fig.text((x_meal + meal_w / 2) / width, panel_y, "Diet log: ingredients by meal", ha="center", va="bottom",
             fontsize=9.5, fontweight="bold", color=D.TEXT)
    fig.text((x_stool + stool_w / 2) / width, panel_y, "Stool sequencing: detection per sample", ha="center",
             va="bottom", fontsize=9.5, fontweight="bold", color=D.TEXT)

    meal_days = cells[(cells["Subject_ID"] == sid) & (cells["meal"] != "not recorded")]["Date"].nunique()
    fig.text(0.015, 1 - 0.12 / height,
             f"Subject {sid_txt}: {title_rows or f'top {M.TOP_N} informative ingredients'}, diet log vs stool sequencing",
             fontsize=12, fontweight="bold", va="top")
    fig.text(0.015, 1 - 0.38 / height,
             f"Left: {len(days)} logged days ({meal_days} with meals assigned); B/L/D = breakfast/lunch/dinner, "
             f"? = no meal or time logged. Right: {n_samples} stool samples in collection order; detected = compatible "
             f"ASVs ≥ {S.DETECTION_MIN:.1%} of reads.", fontsize=8, color=D.TEXT, va="top")

    # one legend per panel
    leg_y = (bottom - 0.12) / height
    fig.legend(handles=M.meal_legend(), title="Diet log", loc="upper left",
               bbox_to_anchor=(0.01, leg_y), ncol=2, frameon=False, fontsize=7, title_fontsize=7.5,
               alignment="left")
    fig.legend(handles=S.stool_legend(), title="Stool sequencing", loc="upper left",
               bbox_to_anchor=(x_stool / width - 0.02, leg_y), ncol=1, frameon=False, fontsize=7,
               title_fontsize=7.5, alignment="left")
    fig.text(0.015, 0.04 / height, M.MEAL_NOTE + "\n" + S.STOOL_NOTE.replace("\n", " "), fontsize=6, color=D.TEXT,
             va="bottom")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


def main():
    cells, top, entries, _ = M.presence_table()
    days = M.study_days(entries)
    _, lexicon = D.read_coding()
    det = S.detection_table(S.load_runs(), top, lexicon)
    plotted = []
    for sid in sorted(days):
        if (det["Subject_ID"] == f"{int(sid):02d}").any():
            plot_subject(sid, days[sid], cells, det, top, OUT / f"Diet-vs-stool-{int(sid):02d}.png")
            plotted.append(sid)
    print(f"{len(plotted)} subjects plotted to {OUT}")


if __name__ == "__main__":
    main()
