"""Breakfast / lunch / dinner presence-absence time series of the top 60 informative ingredients.

For each subject, one figure: rows = the 60 most frequently logged ingredients rated 'Yes' for
sequencing (same ranking as diet_log_ingredients.py), columns = each logged day split into
Breakfast, Lunch, Dinner and 'not recorded'. A filled cell means the ingredient appears in at
least one food entry of that meal.

How entries are assigned to a meal (column 'Time/meal as logged' of daily_diet_coding.xlsx):
    1. A meal word wins: breakfast/brunch -> Breakfast, lunch -> Lunch, dinner -> Dinner.
    2. Otherwise the logged clock time: before 11:00 Breakfast, 11:00-15:59 Lunch, from 16:00 Dinner.
       Times without am/pm ('6:45', '6:30-7:30') are read as the earliest of the am/pm readings
       that is not before the previous timed entry of the same day (logs are chronological);
       1:00-5:59 without am/pm is always pm.
    3. Anything else (blank, 'Snacks', 'Dessert', 'Korean food', ...) -> 'not recorded'.
       Nothing is inferred from the order of untimed entries.

Colours follow the frequency plots: green = species-level label in the plants/meat
feature_data.txt, purple = genus/family label only, grey = no label. Dark = stated in the log,
light hatched = assumed only (inferred from the dish).

Outputs (diet_log_analyses/figures_Diet-logs/Meal-time-series/)
    Meal-presence-<subject>.png      one figure per subject
    meal_presence_long.csv           subject, date, meal, ingredient, stated (one row per cell)
    meal_assignment.csv              how each 'Time/meal as logged' value was assigned

Usage (from the repository root):
    python diet_log_analyses/diet_log_meal_timeseries.py
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import config as C
import diet_log_ingredients as D
from config import plt

OUT = D.OUT / "Meal-time-series"
MEALS = ["Breakfast", "Lunch", "Dinner", "not recorded"]
MEAL_ABBR = {"Breakfast": "B", "Lunch": "L", "Dinner": "D", "not recorded": "?"}
TOP_N = 60

#######################################
# Meal assignment
#######################################

MEAL_WORDS = [("breakfast", "Breakfast"), ("brunch", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]
# first clock time in the text: '6', '6:30', '6-7:30', '11-11:30am', '1:15pm'
TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?(?:\s*-\s*\d{1,2}(?::\d{2})?)?\s*(am|pm)?", re.I)


def parse_time(text):
    """First clock time in `text` as (minutes, has_am_pm); None if there is none."""
    m = TIME_RE.search(str(text))
    if not m:
        return None
    h, mins, ampm = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
    if h > 24 or mins > 59:
        return None
    if ampm == "pm" and h < 12:
        h += 12
    if ampm == "am" and h == 12:
        h = 0
    return h * 60 + mins, bool(ampm) or h >= 13


def meal_of_minutes(t):
    return "Breakfast" if t < 11 * 60 else "Lunch" if t < 16 * 60 else "Dinner"


def assign_meals(entries):
    """Meal for every food entry, following the rules in the module docstring."""
    meals, how = [], []
    for _, day in entries.sort_values(["Day_key", "Entry_no"]).groupby("Day_key", sort=False):
        last = None  # minutes of the previous timed entry that day
        for e in day.itertuples(index=False):
            text = getattr(e, "_3")  # 'Time/meal as logged'
            meal, rule, t = "not recorded", "no meal word or time", None
            if isinstance(text, str):
                lower = text.lower()
                word = next((m for w, m in MEAL_WORDS if w in lower), None)
                parsed = parse_time(text)
                t = None
                if parsed:
                    t, explicit = parsed
                    if not explicit and 60 <= t < 6 * 60:  # '1:30' without am/pm: nobody logs 1-5 am meals
                        t += 12 * 60
                    elif not explicit and t < 12 * 60:  # ambiguous: choose am or pm, keeping the day in order
                        am, pm = t, t + 12 * 60
                        t = am if last is None or am >= last else pm if pm >= last else am
                    last = t
                if word:
                    meal, rule = word, "meal word"
                elif t is not None:
                    meal, rule = meal_of_minutes(t), f"clock time {t // 60:02d}:{t % 60:02d}"
            meals.append((e.Day_key, e.Entry_no, meal, t))
            how.append({"Time/meal as logged": text, "meal": meal, "rule": rule})
    m = pd.DataFrame(meals, columns=["Day_key", "Entry_no", "meal", "minutes"])  # minutes: parsed clock time
    return m, pd.DataFrame(how)



#######################################
# Presence table
#######################################


def presence_table(top_n=TOP_N):
    """One row per (subject, date, meal, ingredient) for the top `top_n` informative ingredients (None = all)."""
    entries, lexicon = D.read_coding()
    long = D.split_ingredients(entries)
    species, genus, _ = D.read_labels()
    freq = D.ingredient_table(long, lexicon, species, genus)
    top = freq[freq["informative_for_sequencing"] == "Yes"]
    top = (top if top_n is None else top.head(top_n)).reset_index(drop=True)

    meals, how = assign_meals(entries)
    long["Entry_no"] = long["entry"].map(lambda e: e[1])
    long = long.merge(meals, on=["Day_key", "Entry_no"], how="left")
    long = long[long["ing"].isin(top["ing"])]
    long["Date"] = long["Day_key"].str.split("_").str[1]
    cells = (long.groupby(["Subject_ID", "Date", "meal", "ing"])["stated"].any().reset_index()
             .rename(columns={"ing": "ingredient"}))
    assignment = (how.dropna(subset=["Time/meal as logged"])
                  .groupby(["Time/meal as logged", "meal", "rule"]).size().rename("entries").reset_index()
                  .sort_values(["meal", "entries"], ascending=[True, False]))
    return cells, top, entries, assignment


def study_days(entries):
    """Every logged day per subject (date and study-day number from the source tab's Event_name)."""
    src = pd.read_excel(D.DIET_CODING, sheet_name="source_diet_text")
    src["day_no"] = src["Event_name"].astype(str).str.extract(r"Day\s*0*(\d+)", expand=False).astype(float)
    return {sid: g.sort_values("Date (MM-DD)")[["Date (MM-DD)", "day_no"]].values.tolist()
            for sid, g in src.groupby("Subject_ID")}


#######################################
# Plot
#######################################


CELL_IN, DAY_GAP_IN = 0.16, 0.12  # cell size and gap between days (inches)


def meal_grid_width(days):
    """Width of the meal grid in inches (without the 'days' count column)."""
    return len(days) * (4 * CELL_IN + DAY_GAP_IN) - DAY_GAP_IN


def draw_meal_grid(ax, sid, days, cells, top, show_labels=True, labels=None):
    """Draw one subject's ingredient x (day, meal) grid on `ax` (rows = top ingredients)."""
    n_rows = len(top)
    level = dict(zip(top["ing"], top["label_level"]))
    row = {ing: i for i, ing in enumerate(top["ing"])}
    sub = cells[cells["Subject_ID"] == sid]
    step = 4 + DAY_GAP_IN / CELL_IN  # in cell units

    for d, (date, day_no) in enumerate(days):
        x0 = d * step
        for k, meal in enumerate(MEALS):
            shade = "#E4E4E4" if meal == "not recorded" else "#F2F2F2"
            for i in range(n_rows):
                ax.add_patch(Rectangle((x0 + k + 0.06, i + 0.06), 0.88, 0.88, facecolor=shade, edgecolor="none"))
        for r in sub[sub["Date"] == date].itertuples(index=False):
            i, k = row[r.ingredient], MEALS.index(r.meal)
            colour = D.LEVEL_COLOUR[level[r.ingredient]]
            if r.stated:
                ax.add_patch(Rectangle((x0 + k + 0.06, i + 0.06), 0.88, 0.88, facecolor=colour, edgecolor=colour))
            else:
                ax.add_patch(Rectangle((x0 + k + 0.06, i + 0.06), 0.88, 0.88, facecolor=D.lighten(colour),
                                       edgecolor=colour, hatch="////", linewidth=0.6))
        day_label = f"Day {int(day_no)}\n{date}" if not np.isnan(day_no) else date
        ax.text(x0 + 2, -1.6, day_label, ha="center", va="bottom", fontsize=7.5, color=D.TEXT)
        for k, meal in enumerate(MEALS):
            ax.text(x0 + k + 0.5, -0.3, MEAL_ABBR[meal], ha="center", va="bottom", fontsize=6.5,
                    color="#888888" if meal == "not recorded" else D.TEXT)

    # number of days this subject ate each ingredient
    n_days = sub.groupby("ingredient")["Date"].nunique()
    x_end = len(days) * step - DAY_GAP_IN / CELL_IN
    for ing, i in row.items():
        n = int(n_days.get(ing, 0))
        ax.text(x_end + 0.4, i + 0.5, str(n) if n else "", ha="left", va="center", fontsize=6.5, color=D.TEXT)
    ax.text(x_end + 0.4, -0.3, "days", ha="left", va="bottom", fontsize=6.5, color=D.TEXT)

    ax.set_xlim(0, x_end)
    ax.set_ylim(n_rows, 0)
    if show_labels:
        ax.set_yticks(np.arange(n_rows) + 0.5, labels or D.informative_labels(top), fontsize=7.5)
        for tick in ax.get_yticklabels():
            tick.set_color(D.TEXT)
    else:
        ax.set_yticks([])
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def meal_legend():
    return [Patch(facecolor=D.GREEN, label="Species-level label in plants/meat feature_data.txt"),
            Patch(facecolor=D.PURPLE, label="Genus/family label only"),
            Patch(facecolor=D.GREY, label="No label in either feature_data.txt"),
            Patch(facecolor="white", edgecolor="#333333", label="Solid = stated in the log"),
            Patch(facecolor="white", edgecolor="#333333", hatch="////", label="Hatched = assumed only")]


MEAL_NOTE = ("Meals from 'Time/meal as logged': a meal word, else clock time (<11:00 breakfast, 11:00-15:59 lunch, "
             ">=16:00 dinner). Untimed snacks, desserts and drinks are in '?'. Nothing is inferred from entry order.")


def plot_subject(sid, days, cells, top, path):
    n_rows = len(top)
    label_w, right_w = 2.75, 0.75
    width = label_w + meal_grid_width(days) + right_w
    bottom, top_margin = 0.75, 1.25  # inches: legend + footnote below, title + day labels above
    height = n_rows * CELL_IN + bottom + top_margin
    fig = plt.figure(figsize=(width, height), facecolor=D.BACKGROUND)
    ax = fig.add_axes([label_w / width, bottom / height, meal_grid_width(days) / width, n_rows * CELL_IN / height],
                      facecolor=D.BACKGROUND)
    draw_meal_grid(ax, sid, days, cells, top)
    sub = cells[cells["Subject_ID"] == sid]

    meal_days = sub[sub["meal"] != "not recorded"]["Date"].nunique()
    fig.text(0.02, 1 - 0.15 / height, f"Subject {int(sid):02d}: top {TOP_N} informative ingredients by meal, weeklong diet log",
             fontsize=11, fontweight="bold", va="top")
    fig.text(0.02, 1 - 0.4 / height,
             f"B = breakfast, L = lunch, D = dinner, ? = logged without a meal name or time. "
             f"{meal_days} of {len(days)} days have at least one of these ingredients assigned to a meal.",
             fontsize=8, color=D.TEXT, va="top")
    fig.legend(handles=meal_legend(), loc="lower left", bbox_to_anchor=(0.01, 0.2 / height), ncol=3, frameon=False,
               fontsize=7.5)
    fig.text(0.02, 0.06 / height, MEAL_NOTE, fontsize=6.5, color=D.TEXT, va="bottom")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=D.BACKGROUND)
    plt.close(fig)


#######################################
# Run
#######################################


def main():
    cells, top, entries, assignment = presence_table()
    days = study_days(entries)
    OUT.mkdir(parents=True, exist_ok=True)
    cells.to_csv(OUT / "meal_presence_long.csv", index=False)
    assignment.to_csv(OUT / "meal_assignment.csv", index=False)
    for sid in sorted(days):
        plot_subject(sid, days[sid], cells, top, OUT / f"Meal-presence-{int(sid):02d}.png")
    share = cells.assign(known=cells["meal"] != "not recorded").groupby("Subject_ID")["known"].mean()
    print(f"{len(days)} subjects plotted to {OUT}")
    print("Share of ingredient-meal cells with a known meal, per subject:")
    print((100 * share).round(0).astype(int).astype(str).add("%").to_string())


if __name__ == "__main__":
    main()
