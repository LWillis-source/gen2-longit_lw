"""Ingredient and genus frequency in the Weeklong daily diet logs.

Reproduces the diet-log figures made in the Claude cowork session (October 2026): how often
each logged ingredient (or genus) was eaten, which of them the trnL / 12SV5 sequencing could
detect, and whether the plants / meat feature_data.txt contain a matching taxon label.

Inputs
    diet_log_analyses/daily_diet_coding.xlsx   free-text diet logs coded into one row per food entry
                                             (tabs daily_diet_coding and ingredient_lexicon)
    1-data/DADA2-weeklong-plants/feature_data.txt, 1-data/DADA2-weeklong-meat/feature_data.txt

Outputs (diet_log_analyses/figures_Diet-logs/)
    ingredient_frequency.png                                  top 25 ingredients, all ratings
    ingredient_frequency_informative_top40.png                top 40 'Yes' ingredients
    ingredient_frequency_informative_top40_green.png          ... coloured labelled / not labelled
    ingredient_frequency_informative_top40_species_genus.png  ... species / genus-only / no label
    ingredient_frequency_informative_top60_species_genus.png  top 60, same colours
    ingredient_frequency_informative_top60_species_genus_clean.png  top 60, no text after the counts
    genus_frequency_top40.png                                 top 40 genera
    ingredient_frequency.csv, genus_frequency_informative.csv the tables behind the plots

Usage (from the repository root):
    python diet_log_analyses/diet_log_ingredients.py
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

import _paths  # noqa: F401  (makes config.py etc. in 2-analysis_python importable)
import config as C
from config import plt
from matplotlib.patches import Patch

HERE = C.Path(__file__).resolve().parent  # diet_log_analyses/
DIET_CODING = HERE / "daily_diet_coding.xlsx"
FEATURE_DATA = {d: C.DATA_DIR / f"DADA2-weeklong-{d}" / "feature_data.txt" for d in ["plants", "meat"]}
OUT = HERE / "figures_Diet-logs"

N_DAYS = 167  # subject-days in the logs (19 subjects; subject 11 is excluded in the coding)
N_SUBJECTS = 19

# Items left out of the first (all-ingredient) plot: unspecified foods, supplements, diet soda.
EXCLUDED_FROM_PLOT = [
    "mixed vegetables", "grain cereal", "fish", "protein powder", "beans (unspecified)", "fruit (unspecified)",
    "jam", "unknown", "berries (mixed)", "nuts (unspecified)", "trail mix", "seafood (mixed)", "diet soda",
    "supplement", "vegan caesar dressing", "grain-free cereal", "stone fruit", "plant-based mince", "shellfish",
]

# Colours (distinguishable under common colour-vision deficiencies)
BLUE = "#2878D6"
GREEN = "#1B8A4C"
PURPLE = "#7B4FC4"
GREY = "#80838F"
BACKGROUND = "#FCFCFA"
TEXT = "#444444"

SPECIES, GENUS_ONLY, NOT_FOUND = 3, 2, 0
LEVEL_COLOUR = {SPECIES: GREEN, GENUS_ONLY: PURPLE, NOT_FOUND: GREY}
LEVEL_NOTE = {SPECIES: "", GENUS_ONLY: "genus/family label only", NOT_FOUND: "not in feature_data.txt"}


#######################################
# Reading and parsing
#######################################


def read_coding():
    """Food entries and the ingredient lexicon from daily_diet_coding.xlsx."""
    entries = pd.read_excel(DIET_CODING, sheet_name="daily_diet_coding")
    lexicon = pd.read_excel(DIET_CODING, sheet_name="ingredient_lexicon")
    lexicon = lexicon.rename(columns={
        "Ingredient": "ing",
        "Species (scientific name)": "species",
        "Marker that can detect it": "marker",
        "Informative for sequencing? (Yes / Uncertain / No)": "informative",
        "Reason category": "reason",
    })
    return entries, lexicon.set_index("ing")


def split_ingredients(entries):
    """One row per (entry, ingredient), with stated = False when the log marks it '(assumed)'."""
    rows = []
    for e in entries.itertuples(index=False):
        if pd.isna(e.Ingredients):
            continue
        for part in str(e.Ingredients).split(";"):
            part = part.strip()
            if not part:
                continue
            assumed = part.endswith("(assumed)")
            rows.append({"entry": (e.Day_key, e.Entry_no), "Day_key": e.Day_key, "Subject_ID": e.Subject_ID,
                         "ing": re.sub(r"\s*\(assumed\)$", "", part), "stated": not assumed})
    return pd.DataFrame(rows)


def clean_species(sp):
    """'Daucus carota subsp. sativus (assumed)' -> 'Daucus carota'."""
    return re.sub(r"\s*\(assumed\)", "", str(sp)).strip()


def species_list(sp):
    return [clean_species(s) for s in str(sp).split(";") if clean_species(s)]


def display_species(sp):
    """Short name for the plot: binomial only; hybrids as 'Genus spp.'; recipes as 'first species et al.'."""
    parts = species_list(sp)
    words = parts[0].split()
    if len(words) >= 2 and words[1] == "x":
        name = f"{words[0]} spp."
    else:
        name = " ".join(words[:2])
    return name + (" et al." if len(parts) > 1 else "")


def genera_of(sp):
    """Genera named in a lexicon species entry.

    A family/subfamily name is replaced by a genus given in parentheses
    ('Bambusoideae (Phyllostachys spp.)' -> Phyllostachys); family-only names such as
    'Gadidae (cod/haddock/pollock, unspecified)' give no genus.
    """
    out = []
    for s in species_list(sp):
        g = s.split()[0]
        if g.endswith(("idae", "oideae", "aceae")):
            inner = re.search(r"\(([A-Z][a-z]+) ", s)
            g = inner.group(1) if inner else None
        if g and g[:1].isupper() and g not in out:
            out.append(g)
    return out


#######################################
# Feature-data labels
#######################################


def read_labels():
    """Species, genus and per-genus ASV counts in the plants and meat feature_data.txt."""
    species, genus, asvs = set(), set(), {}
    for name, path in FEATURE_DATA.items():
        t = pd.read_csv(path, sep="\t")
        for g, s in t[["Genus", "Species"]].dropna().itertuples(index=False):
            species.add(s if " " in s else f"{g} {s}")  # meat stores binomials, plants only the epithet
        genus |= set(t["Genus"].dropna())
        asvs[name] = t["Genus"].value_counts()
    return species, genus, asvs


def label_level(sp, species, genus):
    """Best match of one species against the labels: exact binomial, else genus, else none."""
    words = clean_species(sp).split()
    if len(words) >= 2 and words[1] not in ("spp.", "x") and f"{words[0]} {words[1]}" in species:
        return SPECIES
    if words and words[0] in genus:
        return GENUS_ONLY
    return NOT_FOUND


#######################################
# Frequency tables
#######################################


def frequency(long, key):
    """Entries, subject-days, subjects and stated/assumed-only days for each value of `key`.

    A day counts as 'stated' when at least one entry that day names the item without '(assumed)'.
    """
    per_day = long.groupby([key, "Day_key"]).agg(stated=("stated", "any"), Subject_ID=("Subject_ID", "first"))
    days = per_day.groupby(level=0).agg(subject_days=("stated", "size"), days_stated=("stated", "sum"),
                                       subjects=("Subject_ID", "nunique"))
    days["entries"] = long.drop_duplicates([key, "entry"]).groupby(key).size()
    days["days_assumed_only"] = days["subject_days"] - days["days_stated"]
    days["pct_of_167_days"] = (100 * days["subject_days"] / N_DAYS).round(1)
    days = days.reset_index()
    # most frequent first; ties by number of entries, then alphabetically
    days = days.sort_values(["subject_days", "entries", key], ascending=[False, False, True])
    return days[[key, "entries", "subject_days", "subjects", "days_stated", "days_assumed_only",
                 "pct_of_167_days"]].reset_index(drop=True)


def ingredient_table(long, lexicon, species, genus):
    freq = frequency(long, "ing")
    lex = lexicon.reindex(freq["ing"])
    freq["informative_for_sequencing"] = lex["informative"].to_numpy()
    freq["informative_reason_category"] = lex["reason"].to_numpy()
    freq["excluded_from_plot"] = freq["ing"].isin(EXCLUDED_FROM_PLOT)
    freq["species"] = lex["species"].to_numpy()
    freq["label_level"] = [max(label_level(s, species, genus) for s in species_list(sp)) if isinstance(sp, str)
                           else NOT_FOUND for sp in freq["species"]]
    return freq


def genus_table(long, lexicon, genus, asvs):
    """Informative ingredients merged by genus.

    A genus counts once per entry. Recipe items that name several genera (kimchi, feta, ...)
    count as 'assumed' for each genus, since the log does not state the individual components.
    """
    informative = lexicon.index[lexicon["informative"] == "Yes"]
    rows = []
    for r in long[long["ing"].isin(informative)].itertuples(index=False):
        gs = genera_of(lexicon.at[r.ing, "species"])
        for g in gs:
            rows.append({"entry": r.entry, "Day_key": r.Day_key, "Subject_ID": r.Subject_ID, "genus": g,
                         "ing": r.ing, "stated": r.stated and len(gs) == 1})
    gl = pd.DataFrame(rows)
    # one row per (entry, genus): stated if any ingredient of that genus is stated in the entry
    pairs = gl.groupby(["entry", "genus"]).agg(Day_key=("Day_key", "first"), Subject_ID=("Subject_ID", "first"),
                                               stated=("stated", "any")).reset_index()
    freq = frequency(pairs, "genus")
    ing_days = long.drop_duplicates(["ing", "Day_key"]).groupby("ing").size()
    contrib = (gl.drop_duplicates(["genus", "ing"])
               .assign(days=lambda d: d["ing"].map(ing_days))
               .sort_values(["genus", "days", "ing"], ascending=[True, False, True])
               .groupby("genus")["ing"].agg(list))
    freq["ingredients"] = freq["genus"].map(lambda g: ", ".join(contrib[g]))
    freq["ASVs_plants"] = freq["genus"].map(asvs["plants"]).fillna(0).astype(int)
    freq["ASVs_meat"] = freq["genus"].map(asvs["meat"]).fillna(0).astype(int)
    freq["in_feature_data"] = freq["genus"].isin(genus)
    stats = {"entry_genus_pairs": len(pairs), "subject_day_genus_pairs": int(freq["subject_days"].sum()),
             "distinct_genera": len(freq)}
    return freq, stats, contrib


#######################################
# Plotting
#######################################


def lighten(colour, amount=0.75):
    rgb = np.array(C.to_rgba(colour)[:3])
    return tuple(rgb + (1 - rgb) * amount)


def frequency_plot(df, labels, colours, path, title, subtitle, footnote, xlabel, notes=None, legend=None,
                   xmax=None, legend_below=False):
    """Horizontal bars: solid = days stated in the log, hatched = days only assumed."""
    n = len(df)
    height = max(4.0, 0.27 * n + 2.4 + (0.6 if legend_below else 0))
    fig = plt.figure(figsize=(10, height), facecolor=BACKGROUND)
    left = 0.04 + max(len(l) for l in labels) * 0.0068
    bottom = (1.25 + (0.6 if legend_below else 0)) / height
    ax = fig.add_axes([left, bottom, 0.97 - left, 1 - bottom - 0.85 / height], facecolor=BACKGROUND)
    y = np.arange(n)
    stated, assumed = df["days_stated"].to_numpy(), df["days_assumed_only"].to_numpy()
    for i in range(n):
        c = colours[i]
        ax.barh(y[i], stated[i], height=0.6, color=c, edgecolor=c, linewidth=0.8)
        ax.barh(y[i], assumed[i], left=stated[i], height=0.6, color=lighten(c), edgecolor=c, linewidth=0.8,
                hatch="////")
        total = stated[i] + assumed[i]
        # round() of the one-decimal percentage (halves to even), as in the original figures
        text = (f"{total}  ({round(df['pct_of_167_days'].iloc[i])}% of days, "
                f"{df['subjects'].iloc[i]} of {N_SUBJECTS} people)")
        if notes is not None and notes[i]:
            text += f"  | {notes[i]}"
        ax.text(total + 1, y[i], text, va="center", fontsize=8.5, color=TEXT)
    ax.set_yticks(y, labels)
    for tick, lab in zip(ax.get_yticklabels(), labels):
        tick.set_color(TEXT)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax or df["subject_days"].max() * 1.3)
    ax.set_ylim(n - 0.3, -1.2)
    ax.set_xlabel(xlabel, color=TEXT, fontsize=10)
    ax.tick_params(axis="y", length=0, labelsize=10)
    ax.tick_params(axis="x", colors=TEXT, labelsize=9)
    ax.grid(axis="x", color="#E3E3E3", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    title_x = min(left, 0.1)  # long label columns: start the title near the left margin
    fig.text(title_x, 1 - 0.25 / height, title, fontsize=13, fontweight="bold", va="top")
    fig.text(title_x, 1 - 0.55 / height, subtitle, fontsize=9, color=TEXT, va="top")
    fig.text(0.01, 0.01, footnote, fontsize=7.5, color=TEXT, va="bottom", wrap=True)
    if legend:
        if legend_below:
            fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.55 / height), ncol=2,
                       frameon=False, fontsize=9)
        else:
            ax.legend(handles=legend, loc="lower right", frameon=False, fontsize=9)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=BACKGROUND)
    plt.close(fig)


def hatch_keys():
    return [Patch(facecolor="white", edgecolor="#333333", label="Solid = stated in the log that day"),
            Patch(facecolor="white", edgecolor="#333333", hatch="////",
                  label="Hatched = assumed only (inferred from the dish)")]


INFORMATIVE_NOTE = ("Only ingredients rated 'Yes' for sequencing (trnL plant or 12SV5 vertebrate marker expected to "
                    "detect them). Excludes 'Uncertain' and 'No' items such as egg, coffee,\nsugar, butter, vegetable "
                    "oil, honey and mushrooms. ")
LABEL_NOTE = "'Labelled' = the taxon appears in either file (not proof of detection in these subjects). "
NAMES_NOTE = "Scientific names are my assignments, not yet checked against NCBI Taxonomy/ITIS; 'et al.' = recipe with several species."
SUBTITLE = f"{N_SUBJECTS} subjects (subject 11 excluded), {N_DAYS} subject-days. Each day counts once per ingredient."
XLABEL = f"Subject-days on which the ingredient appears (out of {N_DAYS})"


def plot_all_ingredients(freq, n_entries):
    top = freq[~freq["excluded_from_plot"]].head(25)
    legend = [Patch(facecolor=BLUE, edgecolor=BLUE, label="Stated in the log (at least one entry that day)"),
              Patch(facecolor=lighten(BLUE), edgecolor=BLUE, hatch="////",
                    label="Assumed only (inferred from the dish, never named)")]
    frequency_plot(top, list(top["ing"]), [BLUE] * len(top), OUT / "ingredient_frequency.png",
                   "Most frequently logged ingredients, weeklong diet logs",
                   f"{N_SUBJECTS} subjects (subject 11 excluded), {N_DAYS} subject-days, {n_entries:,} coded food "
                   "entries. Each day counts once per ingredient.",
                   "Excludes unspecified items (e.g. 'mixed vegetables', 'fish', 'protein powder'), supplements and "
                   "diet soda.\nIngredients, not species: tofu, soy sauce and edamame count separately.",
                   XLABEL, legend=legend, xmax=175)


def informative_labels(top):
    return [f"{i} ($\\it{{{display_species(s).replace(' ', '~')}}}$)" for i, s in zip(top["ing"], top["species"])]


def plot_informative(freq):
    inf = freq[freq["informative_for_sequencing"] == "Yes"]
    title40 = "Top 40 ingredients informative for sequencing, weeklong diet logs"

    # 1. plain blue
    top = inf.head(40)
    legend = [Patch(facecolor=BLUE, edgecolor=BLUE, label="Stated in the log (at least one entry that day)"),
              Patch(facecolor=lighten(BLUE), edgecolor=BLUE, hatch="////",
                    label="Assumed only (inferred from the dish, never named)")]
    frequency_plot(top, informative_labels(top), [BLUE] * 40, OUT / "ingredient_frequency_informative_top40.png",
                   title40, SUBTITLE, INFORMATIVE_NOTE + NAMES_NOTE, XLABEL, legend=legend, xmax=205)

    # 2. labelled (species or genus) vs not labelled
    lv = top["label_level"].to_numpy()
    colours = [GREEN if l != NOT_FOUND else GREY for l in lv]
    legend = [Patch(facecolor=GREEN, label="Taxon labelled in plants/meat feature_data.txt"),
              Patch(facecolor=GREY, label="No label in either feature_data.txt")] + hatch_keys()
    frequency_plot(top, informative_labels(top), colours, OUT / "ingredient_frequency_informative_top40_green.png",
                   title40, SUBTITLE, INFORMATIVE_NOTE + LABEL_NOTE + NAMES_NOTE, XLABEL,
                   notes=[LEVEL_NOTE[l] for l in lv], legend=legend, xmax=230)

    # 3-5. species / genus-only / no label, top 40 and top 60, with and without the text notes
    legend = [Patch(facecolor=GREEN, label="Species-level label in plants/meat feature_data.txt"),
              Patch(facecolor=PURPLE, label="Genus/family label only (species not labelled)"),
              Patch(facecolor=GREY, label="No label in either feature_data.txt")] + hatch_keys()
    for n, suffix, with_notes in [(40, "top40_species_genus", True), (60, "top60_species_genus", True),
                                  (60, "top60_species_genus_clean", False)]:
        top = inf.head(n)
        lv = top["label_level"].to_numpy()
        frequency_plot(top, informative_labels(top), [LEVEL_COLOUR[l] for l in lv],
                       OUT / f"ingredient_frequency_informative_{suffix}.png",
                       f"Top {n} ingredients informative for sequencing, weeklong diet logs", SUBTITLE,
                       INFORMATIVE_NOTE + LABEL_NOTE + NAMES_NOTE, XLABEL,
                       notes=[LEVEL_NOTE[l] for l in lv] if with_notes else None, legend=legend, xmax=230,
                       legend_below=True)


def plot_genera(gfreq, contrib):
    top = gfreq.head(40)

    def label(g):
        ings = contrib[g]
        extra = f" +{len(ings) - 3}" if len(ings) > 3 else ""
        return f"$\\it{{{g}}}$ ({', '.join(ings[:3])}{extra})"

    legend = [Patch(facecolor=GREEN, label="Genus labelled in plants/meat feature_data.txt"),
              Patch(facecolor=GREY, label="No ASV labelled with this genus")] + hatch_keys()
    frequency_plot(top, [label(g) for g in top["genus"]], [GREEN if f else GREY for f in top["in_feature_data"]],
                   OUT / "genus_frequency_top40.png",
                   "Top 40 genera from ingredients informative for sequencing, weeklong diet logs",
                   f"{N_SUBJECTS} subjects (subject 11 excluded), {N_DAYS} subject-days. Ingredients are merged by "
                   "genus; each day counts once per genus.",
                   "Only ingredients rated 'Yes' for sequencing. Parentheses list up to 3 contributing ingredients "
                   "(+n more). Recipe items with several genera (kimchi, feta) count as 'assumed'\nfor each genus. "
                   "'Labelled' = an ASV with that genus label exists in either file (not proof of detection in these "
                   "subjects). Genus names are my assignments, not yet checked against NCBI Taxonomy/ITIS.",
                   f"Subject-days on which the genus appears (out of {N_DAYS})", legend=legend, xmax=215,
                   legend_below=True)


#######################################
# Run
#######################################


def main():
    entries, lexicon = read_coding()
    long = split_ingredients(entries)
    species, genus, asvs = read_labels()
    freq = ingredient_table(long, lexicon, species, genus)
    gfreq, gstats, contrib = genus_table(long, lexicon, genus, asvs)

    informative = set(lexicon.index[lexicon["informative"] == "Yes"])
    inf_long = long[long["ing"].isin(informative)]
    print(f"Food entries: {len(entries):,}; with an informative ingredient: {inf_long['entry'].nunique():,}")
    print(f"Ingredient mentions: {len(inf_long):,} informative of {len(long):,}")
    print(f"Entry-genus pairs: {gstats['entry_genus_pairs']:,}; subject-day-genus pairs: "
          f"{gstats['subject_day_genus_pairs']:,}; distinct genera: {gstats['distinct_genera']} "
          f"(from {len(informative)} informative ingredients)")
    for n in [40, 60]:
        lv = freq[freq["informative_for_sequencing"] == "Yes"].head(n)["label_level"]
        print(f"Top {n}: {(lv == SPECIES).sum()} species-level, {(lv == GENUS_ONLY).sum()} genus-only, "
              f"{(lv == NOT_FOUND).sum()} no label")

    OUT.mkdir(parents=True, exist_ok=True)
    freq.drop(columns="species").to_csv(OUT / "ingredient_frequency.csv", index=False)
    gfreq.to_csv(OUT / "genus_frequency_informative.csv", index=False)
    plot_all_ingredients(freq, len(entries))
    plot_informative(freq)
    plot_genera(gfreq, contrib)
    print(f"Figures written to {OUT}")


if __name__ == "__main__":
    main()
