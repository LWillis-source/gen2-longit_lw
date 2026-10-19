"""The shared modules (diet_log.py, food_seq.py) reproduce the earlier outputs in old_scripts_figures/.

These are the same rules tested in rules_edited.py (re-implemented there from the CLAUDE.md text); here the
module code that the notebooks use is tested. Run from the repository root:
    /opt/anaconda3/bin/python -m pytest diet_log_analyses/scripts/tests -q
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _paths  # noqa: E402,F401
import diet_log as DL  # noqa: E402
import food_seq as FS  # noqa: E402

OLD = _paths.DIET_DIR / "old_scripts_figures" / "figures_Diet-logs"


@pytest.fixture(scope="module")
def diet():
    return DL.load()


@pytest.fixture(scope="module")
def runs():
    return FS.load_runs()


def test_meal_assignment_matches_old(diet):
    """Expected: every (logged time text, meal) pair and its entry count identical to the earlier meal_assignment.csv."""
    entries, _, _ = diet
    meals = DL.assign_meals(entries).merge(entries[["Day_key", "Entry_no", "Time/meal as logged"]], on=["Day_key", "Entry_no"])
    meals = meals.rename(columns={"Time/meal as logged": "text"})
    new = meals[meals.text.notna() & (meals.text.astype(str).str.strip() != "")].groupby(["text", "meal"]).size()
    ref = pd.read_csv(OLD / "Meal-time-series" / "meal_assignment.csv", keep_default_na=False)
    ref = ref.set_index(["Time/meal as logged", "meal"])["entries"]
    new.index.names = ref.index.names
    assert new.sort_index().equals(ref.sort_index())


def test_meal_every_entry(diet):
    """Expected: one meal per entry, all from the four allowed labels."""
    entries, _, _ = diet
    meals = DL.assign_meals(entries)
    assert len(meals) == len(entries) and set(meals.meal) <= set(DL.MEALS)


def test_compatible_asvs_match_old(diet, runs):
    """Expected: n_compatible_ASVs identical to the earlier stool_detection_long.csv for all its ingredients."""
    _, lex, _ = diet
    old = pd.read_csv(OLD / "Stool-detection" / "stool_detection_long.csv").groupby(["ingredient", "run"]).n_compatible_ASVs.first()
    lexi = lex.set_index("Ingredient")
    diffs = {}
    for (ing, run), n_old in old.items():
        n_new = len(FS.compatible_asvs(lexi.at[ing, FS.SPECIES], runs[run][1], run))
        if n_new != n_old:
            diffs[ing] = (n_old, n_new)
    assert not diffs, diffs


def test_food_taxa_partition(diet, runs):
    """Expected: every matched ingredient in at least one taxon; taxa of one run never share an ASV (the merge is complete)."""
    _, lex, _ = diet
    taxa, member = FS.food_taxa(lex, runs)
    assert set(member) == {i for t in taxa.ingredients for i in t.split(", ")}
    assert all(member.values())
    for run, g in taxa.groupby("run"):
        seen = {}
        for t in g.itertuples(index=False):
            for a in t.asvs:
                assert a not in seen, f"ASV in {seen.get(a)} and {t.taxon_id}"
                seen[a] = t.taxon_id


def test_bos_taurus_is_one_taxon(diet, runs):
    """Positive control: milk, cheese and beef cannot be separated by 12SV5, so they share one taxon labelled Bos taurus."""
    _, lex, _ = diet
    taxa, member = FS.food_taxa(lex, runs)
    tid = {t for i in ("cow milk", "cheese", "beef") for t in member[i]}
    assert len(tid) == 1 and taxa.set_index("taxon_id").at[tid.pop(), "label"] == "Bos taurus"


def test_recipes_do_not_glue_taxa(diet, runs):
    """Kimchi lists several species: it belongs to several taxa, and cabbage and garlic stay in different taxa."""
    _, lex, _ = diet
    taxa, member = FS.food_taxa(lex, runs)
    assert len(member["kimchi"]) > 1
    assert set(member["cabbage"]).isdisjoint(member["garlic"])


def test_match_detail_agrees_with_compatible(diet, runs):
    """match_detail must count the same compatible ASVs as compatible_asvs, for every informative ingredient."""
    _, lex, _ = diet
    inf = lex[lex["Informative for sequencing? (Yes / Uncertain / No)"] == "Yes"]
    bad = {}
    for r in inf.itertuples(index=False):
        run = FS.RUN_OF_MARKER.get(r[inf.columns.get_loc("Marker that can detect it")])
        if run is None:
            continue
        field = r[inf.columns.get_loc(FS.SPECIES)]
        tax = runs[run][1]
        d = FS.match_detail(field, tax, run)
        # per species part, the counted ASVs must equal compatible_asvs of that part alone
        for sp, n in zip(d.species_part, d.compatible):
            if n != len(FS.compatible_asvs(sp, tax, run)):
                bad[(r.Ingredient, sp)] = (n, len(FS.compatible_asvs(sp, tax, run)))
    assert not bad, bad
