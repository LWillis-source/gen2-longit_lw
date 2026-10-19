"""Checks for the CLAUDE.md rules edited on 2026-10-17/18, against the data.

The meal-timing and ASV-matching rules are re-implemented here from the CLAUDE.md text only and compared
with the old outputs in old_scripts_figures/figures_Diet-logs/ (read-only references). Read-only.
Run through pytest (see test_claude_md_rules.py) or directly.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pyreadr

REPO = Path("/Users/lisa/Documents/GitHub/gen2-longit")
sys.path.insert(0, str(REPO / "diet_log_analyses" / "scripts"))
import _paths  # noqa: E402,F401
import config as C  # noqa: E402
import weeklong_16s as W  # noqa: E402

DATA = REPO / "1-data"
OLD = REPO / "diet_log_analyses" / "old_scripts_figures" / "figures_Diet-logs"
RESULTS = []


def check(n, claim, expected, found, ok):
    RESULTS.append((n, "PASS" if ok else "FAIL", claim, expected, found))
    print(f"\n[{n}] {'PASS' if ok else 'FAIL'}  {claim}\n     expected: {expected}\n     found:    {found}")


ddc = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="daily_diet_coding")
src = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="source_diet_text")
lex = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="ingredient_lexicon")
SP, MK = "Species (scientific name)", "Marker that can detect it"
kits, samples = W.read_sample_sheet(C.SAMPLE_SHEET)


def split_ings(s):
    return [p.strip() for p in str(s).split(";") if p.strip() and str(s) != "nan"]


# ---------------------------------------------------------------- edit 1: meal timing
MEAL_WORDS = [("breakfast", "Breakfast"), ("brunch", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]
TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?(?:\s*-\s*\d{1,2}(?::\d{2})?)?\s*(am|pm)?", re.I)


def first_time(text):
    """First clock time; a range is read at its start, with am/pm written after the range applied."""
    m = TIME_RE.search(text)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
    if h > 24 or mi > 59:
        return None
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return h * 60 + mi, bool(ap) or h >= 13  # minutes, taken-as-written


def meal_rule(day):
    out, last = [], None
    for _, e in day.sort_values("Entry_no").iterrows():
        text = e["Time/meal as logged"]
        meal = "not recorded"
        if isinstance(text, str) and text.strip():
            word = next((m for w, m in MEAL_WORDS if w in text.lower()), None)
            t = first_time(text)
            if t:
                t, written = t
                if not written and 60 <= t < 6 * 60:  # bare 1:00-5:59 is pm
                    t += 12 * 60
                elif not written and t < 12 * 60:  # am or pm, whichever keeps the day in order
                    am, pm = t, t + 12 * 60
                    t = am if last is None or am >= last else pm if pm >= last else am
                last = t
            if word:
                meal = word
            elif t is not None:
                meal = "Breakfast" if t < 11 * 60 else "Lunch" if t < 16 * 60 else "Dinner"
        out.append((e["Day_key"], e["Entry_no"], text, meal))
    return out


rows = [r for _, d in ddc.groupby("Day_key") for r in meal_rule(d)]
mine = pd.DataFrame(rows, columns=["Day_key", "Entry_no", "text", "meal"])
mine_agg = (mine.dropna(subset=["text"]).query("text.str.strip() != ''", engine="python")
            .groupby(["text", "meal"]).size().rename("entries").reset_index())
ref = pd.read_csv(OLD / "Meal-time-series" / "meal_assignment.csv", keep_default_na=False)
m = mine_agg.merge(ref, left_on=["text", "meal"], right_on=["Time/meal as logged", "meal"], how="outer",
                   suffixes=("_new", "_old"), indicator=True)
diff = m[(m["_merge"] != "both") | (m["entries_new"] != m["entries_old"])]
check("E1", "Meal timing rule as written in CLAUDE.md reproduces old meal_assignment.csv",
      "identical (value, meal, entries) rows", f"new {len(mine_agg)} rows, old {len(ref)}, differing {len(diff)}"
      + (f": {diff[['text', 'meal', 'entries_new', 'entries_old']].head(6).to_dict('records')}" if len(diff) else ""),
      len(diff) == 0)

# ---------------------------------------------------------------- edit 2: species source
lexsp = dict(zip(lex["Ingredient"], lex[SP].astype(str)))
aligned = 0
for _, r in ddc.iterrows():
    ings = [re.sub(r" \(assumed\)$", "", i) for i in split_ings(r["Ingredients"])]
    per = [re.sub(r"\s*\([a-z ]+\)", "", x).strip() for x in str(r[SP]).split(";") if x.strip()]
    flat = [s.strip() for i in ings for s in lexsp.get(i, "").split(";") if s.strip()]
    aligned += per == [re.sub(r"\s*\(assumed\)", "", s).strip() for s in flat]
tags = sorted(set(re.findall(r"\(([a-z]+)\)", " ".join(ddc[SP].astype(str)))))
check("E2", "Per-entry Species column is a summary with rank tags, not aligned with Ingredients",
      "rank tags like (species)/(variety) present; many entries not position-aligned with lexicon species",
      f"tags include {[t for t in tags if t in ('species', 'variety', 'subspecies', 'genus', 'family')]}; "
      f"entries position-aligned {aligned} of {len(ddc)}", "species" in tags and aligned < len(ddc))
unmatched = sorted({re.sub(r" \(assumed\)$", "", i) for s in ddc["Ingredients"] for i in split_ings(s)} - set(lex["Ingredient"]))
check("E2b", "Every ingredient looks up a lexicon row by Ingredient name", "0 unmatched", f"{len(unmatched)} {unmatched[:5]}",
      not unmatched)

# ---------------------------------------------------------------- edits 3, 5: species formats and ASV matching
FAM = re.compile(r"^[A-Z][a-z]+(eae|idae|oideae|aceae)\b")


def split_species(field):
    """Split a lexicon species field on ';' outside brackets ('unspecified (whey: …; pea: …)' stays whole)."""
    parts, depth, cur = [], 0, ""
    for ch in str(field):
        depth += (ch == "(") - (ch == ")")
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in parts + [cur] if p.strip()]


def classify(sp):
    s = re.sub(r"\s*\(assumed\)", "", sp).strip()
    if re.match(r"^(unspecified|mixed|none|unknown)\b", s):
        return "no taxon", None, None
    if "/" in s:
        return "slash list", None, None
    if FAM.match(s):
        inner = re.findall(r"\(([A-Z][a-z]+)", s)
        return ("family (genus)", inner[0], None) if inner else ("family only", None, None)
    if re.fullmatch(r"[A-Z][a-z]+ \(.*\)", s):
        return "higher taxon", None, None
    w = s.split()
    if len(w) >= 4 and w[2] == "x":
        return "two-parent hybrid", w[0], None
    if len(w) >= 2 and w[1] == "x":
        return "hybrid", w[0], None
    if len(w) >= 2 and w[1] in ("spp.", "spp"):
        return "Genus spp.", w[0], None
    if len(w) >= 2 and re.fullmatch(r"[a-z][a-z-]*", w[1]):
        kind = "var./subsp." if re.search(r" (var\.|subsp\.) ", s) else "binomial"
        return kind, w[0], w[1]
    return "UNCLASSIFIED", None, None


kinds = pd.Series([classify(s)[0] for v in lex[SP].astype(str) for s in split_species(v)])
check("E5", "Every lexicon species value fits one of the formats listed in CLAUDE.md",
      "0 unclassified", f"{kinds.value_counts().to_dict()}", (kinds == "UNCLASSIFIED").sum() == 0)

tax = {"plants": pd.read_csv(DATA / "DADA2-weeklong-plants" / "feature_data.txt", sep="\t"),
       "meat": pd.read_csv(DATA / "DADA2-weeklong-meat" / "feature_data.txt", sep="\t")}
RUN = {"trnL": "plants", "12SV5": "meat"}


def compatible(field, run):
    t = tax[run]
    allc = set()
    for sp in split_species(field):
        kind, genus, epi = classify(sp)
        if genus is None:
            continue  # undetectable
        g = t[t["Genus"] == genus]
        if epi is None:
            allc |= set(g["Sequence"])
            continue
        lab = g["Species"].astype(str)
        unl = g["Species"].isna()
        same = ~unl & ((lab == epi) | lab.str.startswith(epi + "_")) if run == "plants" else ~unl & (lab == f"{genus} {epi}")
        allc |= set(g["Sequence"][same | unl]) if same.any() else set(g["Sequence"])  # congener fallback
    return len(allc)


old = pd.read_csv(OLD / "Stool-detection" / "stool_detection_long.csv")
old_n = old.groupby(["ingredient", "run"])["n_compatible_ASVs"].first()
lexi = lex.set_index("Ingredient")
cmp = []
for (ing, run), n_old in old_n.items():
    mk = lexi.loc[ing, MK]
    n_new = compatible(lexi.loc[ing, SP], RUN[mk]) if RUN.get(mk) == run else 0
    cmp.append((ing, run, n_old, n_new))
cmp = pd.DataFrame(cmp, columns=["ingredient", "run", "old", "new"])
d = cmp[cmp.old != cmp.new]
expect_diff = {"banana", "berries (mixed)", "grain cereal"}  # changed on purpose (PROGRESS.md decision)
check("E3", "ASV-matching rule as written reproduces old n_compatible_ASVs (60 ingredients)",
      f"equal except the deliberately changed {sorted(expect_diff)} (where present)",
      f"{len(cmp)} ingredient x run pairs, differing {len(d)}: {d.to_dict('records')}",
      set(d.ingredient) <= expect_diff)
for ing in sorted(expect_diff):
    mk = lexi.loc[ing, MK]
    print(f"     {ing}: species {lexi.loc[ing, SP]!r}, marker {mk}, compatible ASVs under new rule "
          f"{compatible(lexi.loc[ing, SP], RUN[mk]) if mk in RUN else 'n/a'}; in old top-60 table: {ing in set(old.ingredient)}")

# ---------------------------------------------------------------- edit 4: markers
vc = lex[MK].value_counts()
extra = ["trnL / 12SV5", "12SV5 (fish part only)", "unknown"]
odd_rows = lex[lex[MK].isin(extra)]
odd_n = [compatible(r[SP], "plants") + compatible(r[SP], "meat") for _, r in odd_rows.iterrows()]
check("E4", "Markers: trnL / 12SV5 / none plus three others, one ingredient each, matching no ASVs",
      "exactly 6 values; extras once each; 0 compatible ASVs in either run",
      f"{vc.to_dict()}; compatible ASVs for {odd_rows['Ingredient'].tolist()}: {odd_n}",
      set(vc.index) == {"trnL", "12SV5", "none", *extra} and all(vc[e] == 1 for e in extra) and sum(odd_n) == 0)

# ---------------------------------------------------------------- edit 6: plant families
gb = pd.read_csv(DATA / "genus_family_gbif.csv").set_index("genus")["family"]
trn = lex[lex[MK] == "trnL"]
single = trn[trn["Genus"].notna() & ~trn["Genus"].astype(str).str.contains(";|/")]
lf = single.drop_duplicates("Genus").set_index("Genus")["Family"]
dis = {g: (lf[g], gb[g]) for g in gb.index if g in lf.index and lf[g] != gb[g]}
check("E6", "Lexicon Family covers trnL genera; GBIF cache is a subset that agrees",
      "all single-genus trnL rows have a Family; every cache genus in lexicon with the same family",
      f"lexicon genera {len(lf)}, Family missing {int(lf.isna().sum())}; cache {len(gb)}, not in lexicon "
      f"{sorted(set(gb.index) - set(lf.index))}, disagreements {dis}",
      lf.notna().all() and set(gb.index) <= set(lf.index) and not dis)
mf = tax["meat"]
check("E6b", "Meat Family blank only for ASVs not assigned to a genus", "0 ASVs with Genus but no Family",
      f"{int((mf['Genus'].notna() & mf['Family'].isna()).sum())}", ((mf["Genus"].notna()) & mf["Family"].isna()).sum() == 0)

# ---------------------------------------------------------------- edit 7: subject 11
s11 = samples[samples["Subject_ID"] == "11"]
check("E7", "Subject 11: samples exist, no diet log", "samples > 0, diet rows 0",
      f"samples {s11['Sample_origin3'].value_counts().to_dict()}; diet rows {int((ddc['Subject_ID'] == 11).sum())}",
      len(s11) > 0 and (ddc["Subject_ID"] == 11).sum() == 0)

# ---------------------------------------------------------------- edit 8: count tables
from config import Tree  # noqa: E402
for d in ["DADA2-weeklong", "DADA2-weeklong-plants", "DADA2-weeklong-meat"]:
    st = pyreadr.read_r(str(DATA / d / "seqtab_all.rds"))[None]
    fd = pd.read_csv(DATA / d / "feature_data.txt", sep="\t")
    tips = set(Tree((DATA / d / "dsvs_msa.tree").read_text()).tip_labels)
    check(f"E8 {d}", "seqtab_all.rds matches feature_data.txt and dsvs_msa.tree", "same ASV sets",
          f"seqtab {st.shape[1]}, feature_data {len(fd)}, tree {len(tips)}; equal: "
          f"{set(st.columns) == set(fd['Sequence']) == tips}", set(st.columns) == set(fd["Sequence"]) == tips)
alt = pyreadr.read_r(str(DATA / "DADA2-weeklong-plants" / "seqtab.rds"))[None]
check("E8b", "Plants seqtab.rds has extra ASVs with no taxonomy", "more ASVs; extras absent from feature_data",
      f"{alt.shape[1]} ASVs, not in feature_data {len(set(alt.columns) - set(tax['plants']['Sequence']))}",
      len(set(alt.columns) - set(tax["plants"]["Sequence"])) > 0)

# ---------------------------------------------------------------- edit 9: libraries
info16 = C.read_excel_like_readxl(DATA / "Weeklong-sample-info.xlsx")
s16 = pyreadr.read_r(str(DATA / "DADA2-weeklong" / "seqtab_all.rds"))[None]
lib16 = set(info16["Sample"].str.replace("sample_", "", n=1))
ext = [x for x in s16.index if x not in lib16]
ls = sorted({m.group(0) for x in ext for m in [re.search(r"LS\d+", x)] if m})
check("E9a", "16S count-table rows without an info-sheet row: mostly blanks, 4 study samples (LS1888-LS1891)",
      "blanks the majority; LS IDs = LS1888-LS1891", f"{len(ext)} rows, blanks {sum('Blank' in x for x in ext)}, LS IDs {ls}",
      ls == ["LS1888", "LS1889", "LS1890", "LS1891"] and sum("Blank" in x for x in ext) > len(ext) / 2)
infof = C.read_excel_like_readxl(DATA / "Weeklong-meat-plants-sample-info.xlsx")
for g, d in {"Plant": "DADA2-weeklong-plants", "Meat": "DADA2-weeklong-meat"}.items():
    st = pyreadr.read_r(str(DATA / d / "seqtab_all.rds"))[None]
    sub = infof[infof["group"] == g].assign(lib=lambda x: x["Sample"].str.replace("sample_", "", n=1))
    miss = sub[~sub["lib"].isin(st.index)]
    want = 5 if g == "Meat" else 0
    check(f"E9 {g}", "Food-run library = Sample minus 'sample_'; missing libraries are blanks",
          f"{want} missing, all Blank", f"missing {len(miss)}, groups {miss['Group'].value_counts().to_dict()}",
          len(miss) == want and (miss["Group"] == "Blank").all())

# ---------------------------------------------------------------- edit 10: sample type
ct = pd.crosstab(samples["Sample_origin3"], samples["Region"])
ok = (ct.loc["Stool"].drop("Stool").sum() == 0 and ct.loc["Saliva"].drop("Saliva").sum() == 0
      and set(ct.columns[ct.loc["Capscan"] > 0]) == {"R1", "R2", "R3"})
check("E10", "Sample_origin3 gives the type; Region gives R1-R3 for capsules", "consistent cross-table",
      ct.to_dict(), ok)

# ---------------------------------------------------------------- edit 11: study day
ev = src["Event_name"].astype(str)
mt = ev.str.extract(r"^Day (\d{2})( ingestion)?(\s*)$")
day = mt[0].astype(float)
check("E11", "Event_name = 'Day NN' (+ ' ingestion' for 01-07; Day 01 trailing space)",
      "all parse; 'ingestion' exactly on days 1-7; trailing space only on Day 01",
      f"unparsed {int(day.isna().sum())}; days with 'ingestion' {sorted(day[mt[1].notna()].astype(int).unique())}; "
      f"trailing space on days {sorted(day[mt[2] != ''].astype(int).unique())}",
      day.notna().all() and sorted(day[mt[1].notna()].astype(int).unique()) == list(range(1, 8))
      and sorted(day[mt[2] != ""].astype(int).unique()) == [1])

# ---------------------------------------------------------------- edit 12: stripping
allparts = [p for s in ddc["Ingredients"] for p in split_ings(s)]
trail = {re.sub(r" \(assumed\)$", "", p) for p in allparts}
every = {re.sub(r"\s*\([^)]*\)", "", p).strip() for p in allparts}
check("E12", "Strip only a trailing ' (assumed)'; other brackets are part of the name",
      "trailing strip: 0 names missing from lexicon; stripping every bracket: some names missing",
      f"trailing: {len(trail - set(lex['Ingredient']))}; every bracket: {len(every - set(lex['Ingredient']))} "
      f"e.g. {sorted(every - set(lex['Ingredient']))[:4]}",
      not (trail - set(lex["Ingredient"])) and bool(every - set(lex["Ingredient"])))

print("\n\nSUMMARY")
for n, s, c, *_ in RESULTS:
    print(f"  {s} [{n}] {c[:100]}")
print(f"\n{sum(s == 'PASS' for _, s, *_ in RESULTS)} pass, {sum(s == 'FAIL' for _, s, *_ in RESULTS)} fail")
