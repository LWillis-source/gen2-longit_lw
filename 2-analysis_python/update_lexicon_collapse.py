"""Add sequencing-collapse columns and a re-checked 'Informative for sequencing?' column to
daily_diet_coding.xlsx (tab ingredient_lexicon). Run once; makes a dated backup first.

Sources used (all read in full text or via the project): Taberlet 2007 (doi:10.1093/nar/gkl938),
Reese 2019 (10.1128/mSystems.00458-19), Petrone 2023 (10.1073/pnas.2304441120),
Petrone 2025 (10.1039/d4fo02656j), Aqeel 2025 (10.1002/oby.24205), Superdock 2025 (10.1128/msystems.00158-25),
Jeffrey 2026 preprint (10.64898/2026.07.29.26359128, not peer reviewed).
"""
import re, shutil, copy
from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

SRC = Path("daily_diet_coding.xlsx")
BAK = Path("daily_diet_coding_backup_2026-10-17.xlsx")
if not BAK.exists():
    shutil.copy2(SRC, BAK)

wb = openpyxl.load_workbook(SRC)          # keeps formulas
ws = wb["ingredient_lexicon"]
hdr = [c.value for c in ws[1]]
col = {h: i + 1 for i, h in enumerate(hdr)}
C_ING, C_SP, C_MK = col["Ingredient"], col["Species (scientific name)"], col["Marker that can detect it"]
C_INF = col["Informative for sequencing? (Yes / Uncertain / No)"]
C_CAT, C_WHY = col["Reason category"], col["Reasoning"]

# ------------------------------------------------------------------ collapse groups
S1 = "Documented: identical published sequences + shared label in FoodSeq papers"
S2 = "Documented: shared label in FoodSeq papers"
S3 = "Documented: identical published sequences (Taberlet 2007 Table 4)"
S4 = "Near-identical (1 base) - usually separable if sequencing is accurate"
S5 = "Conflicting evidence - check the lab reference"
S6 = "Possible: same family as a documented group, not documented itself"
S7 = "Not documented - species-level label only if the lab reference has a unique sequence"
S8 = "Unknown (animal): needs the 12SV5 reference and classifier settings"
S9 = "Species-level label seen in Petrone 2025 (no collapse documented)"
S10 = "No marker, so no sequencing label"
S11 = "Not applicable (log names no single taxon)"

GROUPS = [
 dict(id="Wheat + rye", taxa=["Triticum", "Secale"], partners="rye (Secale cereale)",
      label="Poaceae (family)", strength=S1,
      ev="Taberlet 2007 Table 4: identical P6 sequence for Triticum aestivum (AB042240) and Secale cereale (AF519162). Petrone 2025 Methods: an ASV matching wheat and rye is relabelled Poaceae."),
 dict(id="Rice (conflicting)", taxa=["Oryza"], partners="",
      label="Possibly Poaceae with wheat + rye; otherwise rice-specific", strength=S5,
      ev="Reese 2019 Discussion: rice, rye and wheat are 'identical at the trnL-P6 locus'. Taberlet 2007 Table 4 lists a different rice sequence (X15901) from wheat/rye. Which holds depends on the reference used."),
 dict(id="Apple + pear", taxa=["Malus", "Pyrus"], partners="",
      label="Rosaceae (one sequence variant)", strength=S2,
      ev="Reese 2019 Discussion: Malus and Pyrus identical at trnL-P6. Petrone 2023: one Rosaceae sequence variant indicates apple and pear intake."),
 dict(id="Strawberry + raspberry/blackberry", taxa=["Fragaria", "Rubus"], partners="bramble berries",
      label="Rosaceae (a second, separate variant); Aqeel 2025 label 'strawberry, bramble berries'", strength=S2,
      ev="Petrone 2023: a second Rosaceae variant identifies strawberries and raspberries (kept separate from apple/pear but both carry the family label Rosaceae). Aqeel 2025 PCA label: 'strawberry, bramble berries'."),
 dict(id="Brassica oleracea cultivars", taxa=["Brassica oleracea"], partners="kohlrabi, collards",
      label="Brassica oleracea (Aqeel 2025 label: 'cabbage family')", strength=S2,
      ev="Taberlet 2007 Discussion: P6 cannot separate cultivars of B. oleracea (Brussels sprouts, kohlrabi, broccoli...). Reese 2019: broccoli, kale and cabbage are one species. Aqeel 2025 lists 'cabbage family (two variants)'."),
 dict(id="Prunus species", taxa=["Prunus"], partners="apricot",
      label="Prunus (genus)", strength=S3,
      ev="Taberlet 2007: P6 cannot distinguish most Prunus species; Table 4 shows identical sequences for apricot (P. armeniaca, EF010968) and sour cherry (P. cerasus, EF010970)."),
 dict(id="Carrot + parsley + cumin (Apiaceae)", taxa=["Daucus", "Petroselinum", "Cuminum"], partners="parsnip",
      label="Apiaceae (Aqeel 2025 label: 'carrot and parsley family, cumin')", strength=S2,
      ev="Petrone 2025: carrot, parsnip and parsley share a sequence, 'among other species', labelled at family level. Aqeel 2025 PCA label: 'carrot and parsley family, cumin'."),
 dict(id="Other Apiaceae (possible)", taxa=["Apium", "Anethum", "Coriandrum", "Foeniculum", "Pastinaca"], partners="",
      label="Possibly Apiaceae", strength=S6,
      ev="Petrone 2025 says the shared Apiaceae sequence includes 'other species'; celery, dill, coriander and fennel are not named, so this is possible but undocumented."),
 dict(id="Potato + goji berry + other nightshades", taxa=["Solanum tuberosum", "Lycium"], partners="tomatillo, tamarillo, cutleaf groundcherry, goji berry",
      label="Shared 'potato family' variant (Aqeel 2025 label: 'potato, goji berry')", strength=S2,
      ev="Petrone 2023: one sequence variant is shared by potato, tomatillo, tamarillo, goji berry, cutleaf groundcherry and edible nightshades (71% of adolescents). Taberlet 2007: potato, tomato and eggplant differ by single mutations, so tomato is a separate taxon in Petrone 2025."),
 dict(id="Tomato / eggplant vs potato", taxa=["Solanum lycopersicum", "Solanum melongena"], partners="",
      label="Own taxon expected (1-base difference from potato)", strength=S4,
      ev="Taberlet 2007 Table 4: tomato and eggplant each differ from potato by one base. Petrone 2025 Table S4 lists Solanum lycopersicum as its own taxon."),
 dict(id="Soybean + guar bean", taxa=["Glycine"], partners="guar bean (guar gum)",
      label="'guar bean, soybean' (Aqeel 2025 label)", strength=S2,
      ev="Aqeel 2025 PCA label 'guar bean, soybean'. A soybean hit could therefore come from guar gum as well as soy."),
 dict(id="Onion vs leek", taxa=["Allium cepa", "Allium ampeloprasum"], partners="",
      label="Own taxon expected (1-base difference)", strength=S4,
      ev="Taberlet 2007 Table 5 note: onion and leek P6 sequences differ by a single substitution."),
]

ANIMAL_TOK = ["Bos", "Gallus", "Ovis", "Sus", "Salmo", "Meleagris", "Capra", "Oncorhynchus", "Thunnus", "Gadus", "Oreochromis",
              "Anas", "Cervus", "Bison", "Seriola", "Engraulis", "Coturnix", "Actinopterygii", "Penaeidae", "Pectinidae",
              "Brachyura", "Octopus", "Teuthida", "Crustacea", "Apis", "Equus", "Lepus", "Oryctolagus", "Cyprinus", "Clupea"]
SPECIES_SEEN = {  # Petrone 2025 Table S4 (named taxa by FoodSeq)
    "Bos taurus": "Bos taurus (named to species; prevalence 22, Petrone 2025 Table S4)",
    "Gallus gallus": "Gallus gallus (named to species; prevalence 21, Table S4)",
    "Meleagris gallopavo": "Meleagris gallopavo (named to species; prevalence 16, Table S4)",
    "Sus scrofa": "Sus scrofa (named to species; prevalence 11, Table S4)",
    "Salmo salar": "Salmo salar (named to species; prevalence 10, Table S4)"}

DETECT = [  # tokens -> published detection note
 ("Triticum", "Wheat detected in >50% of samples (Aqeel 2025); consistently detected (Superdock 2025)."),
 ("Zea", "Corn detected in >50% of samples (Aqeel 2025)."),
 ("Theobroma", "Cacao in >50% of samples (Aqeel 2025); chocolate (Malvaceae) detected though missing from records (Petrone 2025)."),
 ("Glycine", "Soybean/guar bean in >50% of samples (Aqeel 2025)."),
 ("Capsicum", "Peppers reliably detected by FoodSeq and metaproteomics; prevalence 20 (Petrone 2025, Table S4)."),
 ("Daucus", "Carrots reliably detected (Petrone 2025); Apiaceae prevalence 20 (Table S4)."),
 ("Spinacia", "Spinach prevalence 17 (Petrone 2025, Table S4)."),
 ("Malus", "Rosaceae (apple/pear) prevalence 17 (Petrone 2025, Table S4)."),
 ("Pyrus", "Rosaceae (apple/pear) prevalence 17 (Petrone 2025, Table S4)."),
 ("Cocos", "Coconut prevalence 16 (Petrone 2025, Table S4)."),
 ("Brassica oleracea", "Brassica oleracea prevalence 15 (Petrone 2025, Table S4)."),
 ("Avena", "Oat prevalence 15 (Petrone 2025, Table S4)."),
 ("Solanum lycopersicum", "Tomato prevalence 15 (Petrone 2025, Table S4)."),
 ("Pisum", "Peas better detected by FoodSeq than metaproteomics (Petrone 2025)."),
 ("Oryza", "Rice consistently detected (Superdock 2025)."),
 ("Camellia", "Tea detected (Superdock 2025) but listed as inconsistent in Reese 2019."),
 ("Bos taurus", "Beef/cow prevalence 22 (Petrone 2025, Table S4)."),
 ("Gallus", "Chicken reliably detected; prevalence 21 (Petrone 2025, Table S4); Superdock 2025."),
 ("Meleagris", "Turkey prevalence 16 (Petrone 2025, Table S4)."),
 ("Sus scrofa", "Pork prevalence 11 (Petrone 2025, Table S4); Superdock 2025."),
 ("Salmo", "Salmon prevalence 10 (Petrone 2025, Table S4)."),
 ("Oreochromis", "Tilapia better detected by FoodSeq than metaproteomics (Petrone 2025)."),
]

def tokens_in(sp, toks):
    return [t for t in toks if t in sp]

def single(sp):
    return ";" not in sp and "/" not in sp and "unspecified" not in sp.lower() and sp.strip() not in ("none", "unknown")

rows = {}
for r in range(2, ws.max_row + 1):
    ing = ws.cell(r, C_ING).value
    if ing is None:
        continue
    rows[r] = dict(ing=ing, sp=str(ws.cell(r, C_SP).value or ""), mk=str(ws.cell(r, C_MK).value or ""),
                   inf=ws.cell(r, C_INF).value, cat=ws.cell(r, C_CAT).value, why=ws.cell(r, C_WHY).value or "")

members = {g["id"]: [] for g in GROUPS}
for r, d in rows.items():
    for g in GROUPS:
        if tokens_in(d["sp"], g["taxa"]):
            members[g["id"]].append((r, d))

# ------------------------------------------------------------------ informative re-check
REWRITE = {  # rows whose reasoning referred to the lab's own run; rewritten from literature only
 "apple": "Whole fruit: DNA expected. Apple and pear share one Rosaceae sequence variant in FoodSeq studies (Petrone 2023).",
 "butter": "Milk fat: little cow cell material expected, but not zero (general knowledge; no source retrieved). Any Bos taurus hit cannot be attributed to butter because milk, cheese and beef give the same signal.",
 "cacao": "Roasted, processed chocolate/cocoa, but cacao was detected in >50% of stool samples (Aqeel 2025) and chocolate (Malvaceae) was detected although missing from records (Petrone 2025).",
 "coffee": "Roasted and brewed: roasting degrades DNA and the grounds are discarded. Coffee was the only plant food recorded in diaries but never detected in Reese 2019.",
 "collagen": "Hydrolysed animal protein: processing removes most cells and DNA (general knowledge; no source retrieved). Cow/pig hits cannot be attributed to collagen because meat and dairy give the same signal.",
 "gelatin": "Hydrolysed animal protein: processing removes most cells and DNA (general knowledge; no source retrieved). Cow/pig hits cannot be attributed to gelatin because meat and dairy give the same signal.",
 "whey": "Isolated milk protein: processing removes most cells and DNA (general knowledge; no source retrieved). Cow hits cannot be attributed to whey because milk, cheese and beef give the same signal.",
 "egg": "Egg white has almost no DNA and yolk little (general knowledge; no source retrieved). Chicken hits cannot be attributed to egg alone because chicken meat gives the same signal.",
 "goat cheese": "Goat-milk cheese: Capra hircus DNA expected. Whether 12SV5 separates goat from cow or sheep is not documented in the studies read; needs the 12SV5 reference.",
 "sugar": "Refined sugar: little or no plant DNA expected (Jeffrey 2026 preprint, citing Reese 2019, says sugar leaves little residual DNA). Taberlet 2007 amplified sugarcane P6 from brown sugar, but needed 50 cycles in a dedicated low-DNA setup, so 'little' not 'none'. Beet or sugarcane hits cannot be attributed to sugar because whole beet or sugarcane foods give the same signal.",
 "vegetable oil": "Refined oil (generic, assumed): refining removes most DNA (general knowledge; no source retrieved). Soy or Brassica hits cannot be attributed to the oil because whole soy and Brassica foods give the same signal.",
}
DOWN = {"Distilled": "Distilled spirits: little or no DNA expected (general knowledge; no source retrieved), but not shown to be zero, so a miss is not counted as a false negative.",
        "Refined / purified": "Refined or purified product: little DNA expected (general knowledge; no source retrieved), but not shown to be zero.",
        "Hydrolysed / isolated / fat": "Isolated protein or fat: little DNA expected (general knowledge; no source retrieved), but not shown to be zero."}
UNSPEC_DISTILLED = {"amaro", "herbal liqueur", "spirits"}   # also name no single taxon -> stay No

changes = []
for r, d in rows.items():
    old, new = d["inf"], d["inf"]
    ing, cat = d["ing"], d["cat"]
    basis, note = "", ""
    if cat == "No marker in pipeline" or ing in ("nori", "seaweed"):
        new = "No"
        if ing in ("nori", "seaweed"):
            ws.cell(r, C_CAT).value = "No marker in pipeline"
            ws.cell(r, C_WHY).value = "Seaweed/alga: Petrone 2025 (Fig. 2 legend) states the FoodSeq assay has no marker for fungi, seaweed or bacteria-derived foods."
            note = "Moved from Uncertain to No on published evidence (Petrone 2025)."
        basis = "Marker design - no marker covers this group"
        if "mushroom" in d["sp"].lower() or d["sp"].split()[0] in ("Cantharellus","Flammulina","Lentinula","Pleurotus","Auricularia","Tuber","Agaricus","Saccharomyces"):
            note = note or "Fungus: no fungal marker in the pipeline (Petrone 2025 Fig. 2 legend)."
        elif any(t in d["sp"] for t in ("Brachyura","Octopus","Teuthida","Pectinidae","Crustacea","Penaeidae")):
            note = note or "Invertebrate: 12SV5 is vertebrate-specific (Superdock 2025: shellfish not captured)."
        elif "Apis" in d["sp"]:
            note = note or "Bee product: invertebrate; no marker (marker design)."
    elif cat == "Unspecified taxon":
        new = "No"; basis = "Log names no single taxon"
    elif cat == "No food DNA":
        new = "No"; basis = "Log names no food"
    elif cat in DOWN:
        if ing in UNSPEC_DISTILLED:
            new = "No"; basis = "Log names no single taxon (unspecified botanicals; also distilled)"
        else:
            new = "Uncertain"; basis = "General knowledge - processing (no source retrieved)"
            if cat == "Distilled" or ing not in REWRITE:
                ws.cell(r, C_WHY).value = DOWN[cat] if ing not in REWRITE else REWRITE[ing]
            note = "Moved from No to Uncertain: the claim that processing removes all DNA is not supported by a retrieved source."
            if ing == "sugar":
                basis = "Published: Jeffrey 2026 preprint (citing Reese 2019) and Taberlet 2007"
    elif cat in ("Processed: DNA reduced", "Trace amount", "Low DNA", "Composite product", "Partly unspecified"):
        basis = "General knowledge - processing/amount (no source retrieved)"
        if ing == "coffee": basis = "Published: Reese 2019 (never detected)"
        if ing == "olive oil": basis = "Published: Petrone 2025 (olive 'poorly suited' to detection)"; note = "Petrone 2025: olives or olive oil, and sugarcane, are poorly suited to detection by either method."
        if ing == "tea": basis = "Published (mixed): Superdock 2025 detected; Reese 2019 inconsistent"
        if cat == "Composite product": basis = "Log names a product, not a single taxon (components listed)"
    elif cat == "Whole or lightly processed food":
        hits = [txt for tok, txt in DETECT if tok in d["sp"]]
        if hits:
            basis = "Published detection"; note = " ".join(dict.fromkeys(hits))
        elif d["mk"].startswith("12SV5"):
            basis = "Marker design (vertebrate 12SV5); not specifically reported in the studies read"
        else:
            basis = "Marker design (land-plant trnL), whole food; not specifically reported in the studies read"
    if ing in REWRITE and ws.cell(r, C_WHY).value == d["why"]:
        ws.cell(r, C_WHY).value = REWRITE[ing]
    if ing in ("coffee","tea") and not note:
        note = ""
    if any(tok in d["sp"] for tok, _ in DETECT) and cat != "Whole or lightly processed food":
        hits = [txt for tok, txt in DETECT if tok in d["sp"]]
        if hits and not note: note = " ".join(dict.fromkeys(hits))
    d.update(new=new, basis=basis, note=note, old=old)
    if new != old:
        ws.cell(r, C_INF).value = new
        changes.append((ing, old, new, cat, note or "See reasoning", basis))

# ------------------------------------------------------------------ new columns
newcols = ["Collapse group(s) (sequencing cannot separate)",
           "Other lexicon ingredients in the same group",
           "Label sequencing is expected to report",
           "Collapse evidence (source)",
           "Collapse evidence strength",
           "Informative: value before 17 Oct 2026 review",
           "Informative: evidence basis",
           "Informative: review note"]
start = ws.max_column + 1
hs = ws.cell(1, C_WHY)
for i, h in enumerate(newcols):
    c = ws.cell(1, start + i, h)
    c.font = copy.copy(hs.font); c.fill = copy.copy(hs.fill); c.alignment = Alignment(wrap_text=True, vertical="top")
    c.border = copy.copy(hs.border)
    ws.column_dimensions[get_column_letter(start + i)].width = [34, 38, 40, 70, 44, 18, 44, 70][i]

for r, d in rows.items():
    sp = d["sp"]
    gs = [g for g in GROUPS if tokens_in(sp, g["taxa"])]
    if gs:
        gnames, labs, evs, strs, others = [], [], [], [], []
        for g in gs:
            comp = "" if single(sp) else " (via a component of this product)"
            gnames.append(g["id"] + comp)
            labs.append(g["label"]); evs.append(g["ev"]); strs.append(g["strength"])
            lex = sorted({m["ing"] for rr, m in members[g["id"]] if rr != r and single(m["sp"]) and m["sp"] != sp})
            extra = f" [named in papers, not in lexicon: {g['partners']}]" if g["partners"] else ""
            others.append((", ".join(lex) if lex else "(none in lexicon)") + extra)
        vals = ["; ".join(gnames), " | ".join(others), " | ".join(labs), " ".join(evs), " | ".join(dict.fromkeys(strs))]
    else:
        animal = d["mk"].startswith("12SV5") or any(t in sp for t in ANIMAL_TOK)
        if d["mk"] == "none" or d["mk"] == "unknown" or d["ing"] in ("diet soda", "supplement"):
            vals = ["", "", "none (no marker)", "", S10 if d["new"] == "No" and d["basis"].startswith("Marker") else S11]
        elif not single(sp):
            vals = ["", "", "n/a (log names no single taxon)", "", S11]
        elif animal:
            seen = [v for k, v in SPECIES_SEEN.items() if k in sp]
            if seen:
                vals = ["", "", seen[0], "Petrone 2025 Table S4 lists this species among FoodSeq 12SV5 taxa.", S9]
            else:
                vals = ["", "", "Unknown - run the 12SV5 reference through the lab's assignTaxonomy settings", "", S8]
        else:
            vals = ["", "", "Own species/genus label expected only if unique in the lab reference", "", S7]
    vals += [d["old"], d["basis"], d["note"]]
    for i, v in enumerate(vals):
        c = ws.cell(r, start + i, v if v != "" else None)
        c.alignment = Alignment(wrap_text=True, vertical="top")

# ------------------------------------------------------------------ extra tabs
for name in ("collapse_groups", "informative_changes"):
    if name in wb.sheetnames:
        del wb[name]
cg = wb.create_sheet("collapse_groups")
cg.append(["Group", "Lexicon ingredients in the group", "Partner foods named in papers but not in lexicon",
           "Label sequencing is expected to report", "Evidence (source)", "Evidence strength"])
for g in GROUPS:
    lex = sorted({m["ing"] for rr, m in members[g["id"]] if single(m["sp"])})
    cg.append([g["id"], ", ".join(lex) or "(none)", g["partners"] or None, g["label"], g["ev"], g["strength"]])
cg.append([])
cg.append(["Notes"])
cg.append(["Rules for adding a group: it needs a published source that two foods share a sequence or a label. Foods not listed are NOT proven separable; they are 'not documented'."])
cg.append(["The apple/pear variant and the strawberry/raspberry variant both carry the family label Rosaceae (Petrone 2023), so a Rosaceae label alone cannot say which."])
cg.append(["Animal foods: no published list of collapses was found. 12SV5 uses assignTaxonomy (statistical), so collapse must be tested with the lab's 12SV5 reference."])
cg.append(["Verify with the lab reference: run each species through the same assignSpecies/assignTaxonomy step, then replace this table with the observed labels."])
for c in cg[1]:
    c.font = Font(bold=True)
for i, w in enumerate([34, 50, 40, 50, 90, 50]):
    cg.column_dimensions[get_column_letter(i + 1)].width = w
for row in cg.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")

ic = wb.create_sheet("informative_changes")
ic.append(["Ingredient", "Before", "After", "Reason category (unchanged unless noted)", "Why changed", "Evidence basis"])
for ch in sorted(changes):
    ic.append(list(ch))
for c in ic[1]:
    c.font = Font(bold=True)
for i, w in enumerate([26, 12, 12, 34, 90, 54]):
    ic.column_dimensions[get_column_letter(i + 1)].width = w

# ------------------------------------------------------------------ README
rd = wb["README"]
for r in range(1, rd.max_row + 1):
    v = rd.cell(r, 1).value
    if isinstance(v, str) and v.startswith("Informative for sequencing?"):
        rd.cell(r, 1).value = ("Informative for sequencing? (lexicon column H, re-checked 17 Oct 2026): Yes = marker covers it, the log names a single taxon, and DNA is expected to survive. "
                               "Uncertain = DNA reduced, trace, low or unproven (including refined, distilled and isolated products, where 'no DNA' is not supported by a retrieved source), or only a group/product is named; a miss is not counted as a false negative. "
                               "No = no marker covers it (fungi, seaweed, invertebrates) or the log names no single taxon or food. Previous values are kept in lexicon column P; every change is listed on tab informative_changes. "
                               "Evidence basis (column Q) says whether a call rests on marker design, a paper, or general knowledge. The reasoning no longer refers to the lab's own sequencing output.")
base = rd.max_row + 2
for i, line in enumerate([
    "Changes 17 Oct 2026",
    "ingredient_lexicon columns K-O: which ingredients collapse into one sequencing label, with sources and evidence strength (see tab collapse_groups). Based on published studies, not on your DADA2 output.",
    "ingredient_lexicon columns P-R: previous 'Informative' value, evidence basis and review note. Backup of the earlier file: daily_diet_coding_backup_2026-10-17.xlsx.",
    "Animal foods are 'unknown': no collapse list was published; test with the lab's 12SV5 reference.",
    "Species names are still unverified against NCBI Taxonomy/ITIS (network blocked); 179 labels also appear in Petrone 2025 Table S5.",
]):
    rd.cell(base + i, 1).value = line
wb.save(SRC)
print("saved; changes:", len(changes))
for ch in sorted(changes): print(ch[:3])
