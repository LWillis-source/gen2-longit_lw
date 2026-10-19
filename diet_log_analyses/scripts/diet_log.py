"""Diet-log tables and figures shared by the diet-log notebooks.

Follows the join rules in diet_log_analyses/CLAUDE.md:
- Subject_ID is an integer in the diet workbook; converted to zero-padded text ('01').
- Ingredients are ';'-separated; only a trailing ' (assumed)' is stripped, which gives the lexicon
  Ingredient name (exact match) and a stated/assumed flag.
- Food classes come only from lexicon columns (never hard-coded lists).
"""
import re

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

import _paths
import config as C

LEX_COLS = {  # short name -> lexicon column (exact names, CLAUDE.md "Data sources")
    "live": "Likely live microbes? (Yes / Variable / No / Unknown)",
    "fermented": "Fermented? (Yes / No / Variable / Unknown)",
    "fibrous": "Fibrous? (Yes / No / Variable / Unknown)",
    "informative": "Informative for sequencing? (Yes / Uncertain / No)",
    "dairy": "Dairy? (Yes / No / Variable / Unknown)",
}
CATEGORY_LABELS = {"live": "Live-microbe foods", "fermented": "Fermented foods", "fibrous": "Fibrous foods"}
CATEGORY_COLORS = {"live": "#2F6F6B", "fermented": "#B5562A", "fibrous": "#4C6A9C"}


def load():
    """Return (entries, lexicon, mentions).

    entries:  daily_diet_coding sheet, one row per food entry, plus `subject` ('01') and `date` (Timestamp).
    lexicon:  ingredient_lexicon sheet.
    mentions: one row per (entry, ingredient) with `stated` False when the log marks it '(assumed)'.
    """
    entries = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="daily_diet_coding")
    lexicon = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="ingredient_lexicon")
    entries["subject"] = entries["Subject_ID"].map(lambda s: f"{int(s):02d}")
    entries["date"] = pd.to_datetime("2025-" + entries["Date (MM-DD)"].astype(str))
    rows = []
    for e in entries.itertuples(index=False):
        text = e.Ingredients if isinstance(e.Ingredients, str) else ""
        for part in (p.strip() for p in text.split(";")):
            if part:
                rows.append({"subject": e.subject, "date": e.date, "Day_key": e.Day_key, "Entry_no": e.Entry_no,
                             "ingredient": re.sub(r" \(assumed\)$", "", part),
                             "stated": not part.endswith(" (assumed)")})
    return entries, lexicon, pd.DataFrame(rows)


MEAL_WORDS = [("breakfast", "Breakfast"), ("brunch", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]
MEALS = ["Breakfast", "Lunch", "Dinner", "not recorded"]
_TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?(?:\s*-\s*\d{1,2}(?::\d{2})?)?\s*(am|pm)?", re.I)


def _first_time(text):
    """First clock time in minutes; a range is read at its start, with am/pm written after the range applied."""
    m = _TIME_RE.search(text)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
    if h > 24 or mi > 59:
        return None
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return h * 60 + mi, bool(ap) or h >= 13   # (minutes, taken as written)


def assign_meals(entries):
    """Meal of every food entry, following CLAUDE.md "Food entries" (meal word first, else clock time).

    Bare 1:00-5:59 is pm; any other bare time before 12:00 is am or pm, whichever keeps that day's
    entries (in Entry_no order) in time order. Returns a DataFrame: Day_key, Entry_no, meal.
    """
    out = []
    for _, day in entries.sort_values(["Day_key", "Entry_no"]).groupby("Day_key", sort=False):
        last = None   # minutes of the previous timed entry that day
        for e in day.itertuples(index=False):
            text = e[entries.columns.get_loc("Time/meal as logged")]   # column name has a '/', so read by position
            meal = "not recorded"
            if isinstance(text, str) and text.strip():
                word = next((m for w, m in MEAL_WORDS if w in text.lower()), None)
                t = _first_time(text)
                if t:
                    t, written = t
                    if not written and 60 <= t < 6 * 60:
                        t += 12 * 60
                    elif not written and t < 12 * 60:
                        am, pm = t, t + 12 * 60
                        t = am if last is None or am >= last else pm if pm >= last else am
                    last = t
                if word:
                    meal = word
                elif t is not None:
                    meal = "Breakfast" if t < 11 * 60 else "Lunch" if t < 16 * 60 else "Dinner"
            out.append((e.Day_key, e.Entry_no, meal))
    return pd.DataFrame(out, columns=["Day_key", "Entry_no", "meal"])


def category_sets(lexicon, level="Yes"):
    """Ingredients whose lexicon value equals `level` for each food class (live, fermented, fibrous)."""
    return {k: set(lexicon.loc[lexicon[LEX_COLS[k]] == level, "Ingredient"]) for k in CATEGORY_LABELS}


def frequency(mentions, n_days):
    """Per ingredient: entries, subject_days, subjects, days_stated, days_assumed_only, pct_of_days.

    A subject-day counts once per ingredient; it is 'stated' if at least one mention that day is stated.
    """
    per_day = mentions.groupby(["ingredient", "subject", "date"])["stated"].any().reset_index()
    out = per_day.groupby("ingredient").agg(subject_days=("date", "size"), days_stated=("stated", "sum"),
                                            subjects=("subject", "nunique"))
    out["entries"] = mentions.drop_duplicates(["ingredient", "Day_key", "Entry_no"]).groupby("ingredient").size()
    out["days_assumed_only"] = out["subject_days"] - out["days_stated"]
    out["pct_of_days"] = (100 * out["subject_days"] / n_days).round(1)
    return out.reset_index().sort_values(["subject_days", "entries", "ingredient"], ascending=[False, False, True])


def category_days(mentions, sets, subject_days):
    """One row per logged subject-day: number of distinct foods of each class eaten, and whether any was stated."""
    out = subject_days[["subject", "date"]].copy()
    for k, foods in sets.items():
        m = mentions[mentions["ingredient"].isin(foods)]
        n = m.groupby(["subject", "date"])["ingredient"].nunique().rename(f"n_{k}")
        st = m.groupby(["subject", "date"])["stated"].any().rename(f"stated_{k}")
        out = out.merge(n, on=["subject", "date"], how="left").merge(st, on=["subject", "date"], how="left")
        out[f"n_{k}"] = out[f"n_{k}"].fillna(0).astype(int)
        out[f"stated_{k}"] = out[f"stated_{k}"].astype("boolean").fillna(False).astype(bool)
    return out


def save(fig, name, data, folder):
    """Save a figure as PNG (300 dpi) and PDF, and its data as CSV, in figures/<folder>/ (CLAUDE.md)."""
    out = _paths.FIG_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    data.to_csv(out / f"{name}.csv", index=False)
    return [out / f"{name}.{ext}" for ext in ("png", "pdf", "csv")]


def frequency_bars(freq, labels, title, subtitle, n_days, color="#2B7BD6"):
    """Horizontal bars of subject-days per ingredient: solid = stated that day, hatched = assumed only."""
    freq = freq.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 0.28 * len(freq) + 1.6))
    y = range(len(freq))
    light = tuple(0.65 + 0.35 * c for c in plt.matplotlib.colors.to_rgb(color))
    ax.barh(y, freq["days_stated"], height=0.65, color=color, edgecolor=color)
    ax.barh(y, freq["days_assumed_only"], left=freq["days_stated"], height=0.65, color=light,
            edgecolor=color, hatch="////", linewidth=0.6)
    for i, r in enumerate(freq.itertuples(index=False)):
        ax.text(r.subject_days + 1, i, f"{r.subject_days}  ({r.pct_of_days:.0f}% of days, {r.subjects} people)",
                va="center", fontsize=7.5)
    ax.set_yticks(list(y), [labels.get(i, i) for i in freq["ingredient"]], fontsize=8)
    ax.set_xlim(0, n_days * 1.12)
    ax.set_xlabel(f"Subject-days on which the ingredient appears (out of {n_days})")
    ax.grid(axis="x", color="#E3E3E3")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Patch(facecolor=color, edgecolor=color, label="Stated in the log that day"),
                       Patch(facecolor=light, edgecolor=color, hatch="////", label="Assumed only (inferred from the dish)")],
              loc="lower right", frameon=False, fontsize=8)
    ax.set_title(f"{title}\n", loc="left", fontsize=12, fontweight="bold")
    ax.text(0, 1.005, subtitle, transform=ax.transAxes, fontsize=8.5, va="bottom")
    fig.tight_layout()
    return fig
