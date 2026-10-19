import re, collections, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from informative import classify
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SP = str(HERE / "data") + "/"
OUT = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "daily_diet_coding_rebuilt.xlsx")
S5 = str(HERE / "data" / "d4fo02656j2_suppl.xlsx")

# ---------- lexicon ----------
lex = {}
for ln in open(SP + "lexicon.tsv", encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln:
        continue
    k, sp, mk, note = (ln.split("\t") + [""] * 4)[:4]
    lex[k] = dict(species=sp, marker=mk, note=note)

# ---------- Petrone 2025 Table S5 labels ----------
wb5 = load_workbook(S5, read_only=True)
s5 = [r for r in wb5["Table S5"].iter_rows(values_only=True)][4:]
s5_labels = set()
for r in s5:
    for v in r[1:4]:
        if v:
            s5_labels.add(str(v).lower())
s5_genera = {l.split()[0] for l in s5_labels if l}

def s5_match(species):
    hits = False
    for part in species.split(";"):
        p = part.strip().lower()
        if not p or p.startswith(("unspecified", "unknown", "none", "mixed")):
            continue
        words = p.split()
        genus = words[0]
        if p in s5_labels or genus in s5_genera or genus in s5_labels:
            hits = True
    return hits

# ---------- lab DADA2 taxa ----------
def taxa_sets(path):
    f = pd.read_csv(path, sep="\t")
    s = set()
    for c in ["Family", "Genus"]:
        if c in f:
            s |= set(f[c].dropna().astype(str).str.strip())
    s.discard("NA")
    sp = set()
    if "Species" in f:
        sp = set(f["Species"].dropna().astype(str))
    return s, f
plant_set, pf = taxa_sets(str(REPO / "1-data/DADA2-weeklong-plants/feature_data.txt"))
meat_set, mf = taxa_sets(str(REPO / "1-data/DADA2-weeklong-meat/feature_data.txt"))

def dada_status(species, marker):
    tokens = []
    for part in species.split(";"):
        w = part.strip().split()
        if not w or w[0].lower() in ("unspecified", "unknown", "none", "mixed", "mixed", "crustacea/mollusca"):
            continue
        if w[0][0].isupper() and not w[0].lower().startswith(("unspec",)):
            tokens.append(w[0].strip("()"))
    if not tokens or marker.startswith("none") or marker == "unknown":
        return "n/a"
    ref = meat_set if marker.startswith("12SV5") else plant_set
    found = [t for t in tokens if t in ref]
    if marker.startswith("trnL / 12SV5"):
        found = [t for t in tokens if t in ref or t in meat_set or t in plant_set]
    if found and len(found) == len(tokens):
        return "genus/family in lab DADA2 output"
    if found:
        return "some genera in lab DADA2 output"
    return "not found in lab DADA2 output"

# ---------- parse coding ----------
rows = []
day_order = []
cur = None
n = 0
time = ""
for fn in ["coding_part1.txt", "coding_part2.txt", "coding_part3.txt"]:
    for ln in open(SP + fn, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln:
            continue
        if ln.startswith("## "):
            s, d = ln[3:].split("|")
            cur = (int(s), d)
            day_order.append(cur)
            n = 0
            time = ""
            continue
        t, item, ings = ln.split("|")
        if t:
            time = t
        n += 1
        toks = [x.strip() for x in ings.split(",") if x.strip()]
        rows.append(dict(subj=cur[0], date=cur[1], n=n, time=time, item=item, toks=toks))

# ---------- raw diet ----------
diet = pd.read_excel(str(REPO / "1-data/Weeklong-Redcap-export.xlsx"), sheet_name="Daily-Diet")
diet = diet[diet.Subject_ID != 11].reset_index(drop=True)
diet["key"] = diet.Subject_ID.astype(int).astype(str) + "_" + diet.Date.astype(str)
coded_keys = {f"{s}_{d}" for s, d in day_order}
raw_keys = set(diet.key)
print("days coded", len(coded_keys), "raw", len(raw_keys), "missing in coding", sorted(raw_keys - coded_keys), "extra", sorted(coded_keys - raw_keys))
assert not (raw_keys ^ coded_keys)

# ---------- build rows ----------
used = collections.Counter()
missing = set()
out_rows = []
for r in rows:
    ing_txt, sp_stated, sp_assumed, markers = [], [], [], []
    review = []
    for tk in r["toks"]:
        assumed = tk.endswith("?")
        k = tk.rstrip("?")
        if k not in lex:
            missing.add(k)
            continue
        used[k] += 1
        ing_txt.append(k + (" (assumed)" if assumed else ""))
        sps = [x.strip() for x in lex[k]["species"].split(";")]
        (sp_assumed if assumed else sp_stated).extend(sps)
        mk = lex[k]["marker"]
        if mk and mk not in markers:
            markers.append(mk)
        if k in ("unknown", "fruit (unspecified)", "mixed vegetables", "protein powder", "beans (unspecified)",
                 "grain cereal", "grain-free cereal", "nuts (unspecified)", "trail mix", "jam", "fish", "seafood (mixed)",
                 "shellfish", "berries (mixed)", "plant-based mince", "stone fruit", "vegan caesar dressing", "white fish"):
            review.append(k)
    seen = set()
    sp_all = []
    for s_ in sp_stated:
        if s_ not in seen:
            seen.add(s_); sp_all.append(s_)
    for s_ in sp_assumed:
        if s_ not in seen:
            seen.add(s_); sp_all.append(s_ + " (assumed)")
    ing_dedup = []
    for x in ing_txt:
        if x not in ing_dedup:
            ing_dedup.append(x)
    out_rows.append([r["subj"], r["date"], r["n"], r["time"], r["item"], "; ".join(ing_dedup), "; ".join(sp_all),
                     "; ".join(markers), ("unspecified: " + ", ".join(dict.fromkeys(review))) if review else "",
                     f"{r['subj']}_{r['date']}"])
assert not missing, missing
print("rows", len(out_rows), "unused lexicon", sorted(set(lex) - set(used)))

# ---------- workbook ----------
FONT = "Arial"
hf = Font(name=FONT, bold=True, color="FFFFFF", size=10)
hfill = PatternFill("solid", start_color="1F4E78")
bf = Font(name=FONT, size=10)
wrap = Alignment(wrap_text=True, vertical="top")
thin = Side(style="thin", color="D9D9D9")
border = Border(bottom=thin)

def sheet(ws, headers, data, widths, freeze="A2"):
    ws.append(headers)
    for c in ws[1]:
        c.font = hf; c.fill = hfill; c.alignment = Alignment(wrap_text=True, vertical="center")
    for r in data:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = bf; c.alignment = wrap; c.border = border
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 30

wb = Workbook()
ws0 = wb.active
ws0.title = "README"

# coding tab
ws1 = wb.create_sheet("daily_diet_coding")
sheet(ws1, ["Subject_ID", "Date (MM-DD)", "Entry_no", "Time/meal as logged", "Food entry (as logged)", "Ingredients",
            "Species (scientific name)", "Marker that can detect it", "Needs review", "Day_key"],
      out_rows, [10, 11, 9, 20, 55, 48, 52, 18, 30, 12])

# raw text tab
ws2 = wb.create_sheet("source_diet_text")
raw = [[int(r.Subject_ID), r.Date, r.Event_name, " ".join(str(r.Diet).split()), None, r.key] for r in diet.itertuples()]
sheet(ws2, ["Subject_ID", "Date (MM-DD)", "Event_name", "Diet (original free text)", "n_coded_entries", "Day_key"],
      raw, [10, 11, 22, 100, 14, 12])
for i in range(2, len(raw) + 2):
    ws2.cell(i, 5).value = f"=COUNTIF(daily_diet_coding!$J:$J,F{i})"

# lexicon tab
ws3 = wb.create_sheet("ingredient_lexicon")
lx = []
for k in sorted(lex):
    v = lex[k]
    src = "Petrone 2025 Table S5 (same genus/species label present)" if s5_match(v["species"]) else "General taxonomy knowledge; not yet checked against NCBI Taxonomy / ITIS"
    st, cat, why = classify(k, v["species"], v["marker"], v["note"])
    lx.append([k, v["species"], v["marker"], v["note"], src, dada_status(v["species"], v["marker"]), used.get(k, 0), st, cat, why])
sheet(ws3, ["Ingredient", "Species (scientific name)", "Marker that can detect it", "Notes (resolution / DNA caveats)",
            "Source of species assignment", "Genus/family assigned in your DADA2 weeklong output?", "Rows using it (at build time)",
            "Informative for sequencing? (Yes / Uncertain / No)", "Reason category", "Reasoning"],
      lx, [26, 52, 18, 52, 50, 32, 14, 18, 26, 90])

# review tab: all rows needing review
ws4 = wb.create_sheet("needs_review")
rv = [[r[0], r[1], r[2], r[4], r[5], r[8]] for r in out_rows if r[8]]
sheet(ws4, ["Subject_ID", "Date (MM-DD)", "Entry_no", "Food entry (as logged)", "Ingredients", "What is unspecified"],
      rv, [10, 11, 9, 55, 48, 45])

# README
lines = [
    ("daily_diet_coding.xlsx", True),
    ("Coding of free-text daily diet logs (Weeklong-Redcap-export.xlsx, tab Daily-Diet) into one row per food entry, with ingredients and species.", False),
    ("", False),
    ("Tabs", True),
    ("daily_diet_coding: one row per separate food/drink entry. Edit here.", False),
    ("source_diet_text: original free text per subject-day; n_coded_entries is a formula counting rows in daily_diet_coding.", False),
    ("ingredient_lexicon: ingredient -> species -> marker; edit a species here only if you also change it where the ingredient is used.", False),
    ("needs_review: entries where the log gives no usable detail (e.g. 'protein shake', 'fish', 'mixed vegetables').", False),
    ("", False),
    ("Conventions", True),
    ("Subject 11 excluded (as in the earlier mapping). Dates are MM-DD exactly as in the source tab.", False),
    ("'(assumed)' after an ingredient or species = not stated in the log; inferred from the dish name or a typical recipe (e.g. pizza -> wheat, tomato, cheese). Check these first.", False),
    ("Species are given for the ingredient, not for the exact product: cheese, milk and yogurt are assumed cow (Bos taurus); 'salmon' assumed Atlantic salmon (Salmo salar).", False),
    ("Marker: trnL = plant chloroplast marker; 12SV5 = vertebrate mitochondrial marker; none = not amplified (fungi, algae, shrimp/crab/mollusc) or no DNA expected (refined sugar, distilled spirits).", False),
    ("Refined oils, sugar, sauces and protein isolates contain little or no DNA, so absence of their species in stool is expected.", False),
    ("Informative for sequencing? (lexicon columns H-J): Yes = DNA expected to survive and be amplified by trnL or 12SV5. Uncertain = DNA is reduced, trace, composition unknown or only a group is named, so a miss should not be counted as a false negative. No = nothing comparable is expected: no marker covers it (fungi, invertebrates, honey), processing removes the DNA (distilled spirits, refined sugar/oil, isolates, butter), or the log names no single taxon. 'No' items should be left out of sequencing-vs-log comparisons. This is a judgement from general knowledge of the markers and food processing; it has not been tested against your sequencing data.", False),
    ("Ingredient resolution depends on the marker: e.g. wheat/rye/barley and the Brassica oleracea vegetables will likely collapse to a higher level in sequencing (see Notes in the lexicon).", False),
    ("Water, and non-food text (e.g. 'collected sample'), were not coded.", False),
    ("", False),
    ("Where the species come from", True),
    ("Species are assigned from general taxonomy knowledge. The lexicon column 'Source' marks which genera/species also appear in Petrone et al. 2025 Table S5 (diet-record, DNA and protein labels). None of the assignments has been checked against NCBI Taxonomy / ITIS yet.", False),
    ("The lexicon column 'Genus/family assigned in your DADA2 weeklong output?' checks the genus or family against the assigned taxa in feature_data.txt (DADA2-weeklong-plants / DADA2-weeklong-meat). 'Not found' means no ASV was labelled with that genus in this dataset: the food may not have been detected, the sequence may be labelled at another level or under a merged genus (e.g. apple may sit under Pyrus), or the reference database may lack it. It does not show the food was absent.", False),
    ("Packaged-product recipes (IKEA plant balls, Huel, Impossible) are from memory of the labels and need checking.", False),
    ("", False),
    ("Layout of an entry (example)", True),
    ("Entry 'breaded chicken' -> Ingredients: chicken; wheat (assumed) -> Species: Gallus gallus; Triticum aestivum (assumed) -> Marker: 12SV5; trnL", False),
]
for i, (t, b) in enumerate(lines, 1):
    c = ws0.cell(i, 1, t)
    c.font = Font(name=FONT, size=12 if i == 1 else 10, bold=b)
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws0.column_dimensions["A"].width = 130

wb.save(OUT)
print("saved", OUT, len(out_rows))
# summary stats
c = collections.Counter(r[0] for r in out_rows)
print(dict(sorted(c.items())))
print(sum(1 for r in out_rows if r[8]), "rows need review")
st = collections.Counter(x[5] for x in lx); print(st)
print(sum(1 for x in lx if x[4].startswith("Petrone")), "lexicon rows with S5 match of", len(lx))
