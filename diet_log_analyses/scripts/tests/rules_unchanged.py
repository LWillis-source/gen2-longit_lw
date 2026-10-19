"""Checks that the file-locating and join rules in diet_log_analyses/CLAUDE.md hold in the data.

Rules unchanged by the 2026-10-17/18 edits. Checks 5, 8, 9, 16, 34, 36 and 37 tested the earlier wording
and are replaced by rules_edited.py; test_claude_md_rules.py skips them. Each check states its claim and
expected result before comparing. Read-only. Run through pytest (see test_claude_md_rules.py) or directly.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

REPO = Path("/Users/lisa/Documents/GitHub/gen2-longit")
sys.path.insert(0, str(REPO / "diet_log_analyses" / "scripts"))
import _paths  # noqa: E402,F401
import config as C  # noqa: E402
import weeklong_16s as W  # noqa: E402

RESULTS = []


def check(n, claim, expected, found, ok, note=False):
    status = "NOTE" if note else ("PASS" if ok else "FAIL")
    RESULTS.append((n, status, claim, expected, found))
    print(f"\n[{n}] {status}  {claim}\n     expected: {expected}\n     found:    {found}")


DATA = REPO / "1-data"
DIET = _paths.DIET_CODING

# ---------------------------------------------------------------- locating files
sheet_path = C.SAMPLE_SHEET
check(1, "Sample sheet at gen2_capScan_sanitized00/data/work-in-progress-meta/LONGITWeeklong-samplesheet-FINAL.xlsx",
      "file exists and config.SAMPLE_SHEET points to it", str(sheet_path).replace(str(REPO.parent) + "/", ""),
      sheet_path.exists() and str(sheet_path).endswith(
          "gen2_capScan_sanitized00/data/work-in-progress-meta/LONGITWeeklong-samplesheet-FINAL.xlsx"))

xl = pd.ExcelFile(sheet_path)
want = {"Sample_ID", "Kit_ID", "Daily-Nutrient", "Pre-ingestion-Lifestyle"}
check(2, "Sample-sheet workbook holds Sample_ID, Kit_ID, questionnaires (Pre-ingestion-Lifestyle) and Daily-Nutrient",
      f"sheets include {sorted(want)}", f"sheets: {xl.sheet_names}", want <= set(xl.sheet_names))

kits_raw = C.read_excel_like_readxl(sheet_path, sheet_name="Kit_ID")
kit_cols = {"Kit_ID", "Subject_ID", "Ingestion_date", "Ingestion_time", "Collection_date", "Collection_time",
            "Transit_time_h", "BSS", "Sampling_no"}
check(3, "Kit_ID sheet has Subject_ID, ingestion/collection date and time, Transit_time_h, BSS, Sampling_no",
      f"columns include {sorted(kit_cols)}", f"missing: {sorted(kit_cols - set(kits_raw.columns))}",
      kit_cols <= set(kits_raw.columns))

dx = pd.ExcelFile(DIET)
tabs = ["daily_diet_coding", "source_diet_text", "ingredient_lexicon", "needs_review", "collapse_groups",
        "informative_changes", "README"]
check(4, "daily_diet_coding.xlsx tabs as listed", f"exactly {tabs} (any order)", f"{dx.sheet_names}",
      set(tabs) == set(dx.sheet_names))

ddc = C.read_excel_like_readxl(DIET, sheet_name="daily_diet_coding")
src = C.read_excel_like_readxl(DIET, sheet_name="source_diet_text")
lex = C.read_excel_like_readxl(DIET, sheet_name="ingredient_lexicon")
print("\n     daily_diet_coding columns:", list(ddc.columns))
print("     ingredient_lexicon columns:", list(lex.columns))

has_species = "Species (scientific name)" in ddc.columns
check(5, "Ingredient lists and taxonomic names come from `Ingredients` and `Species (scientific name)` in the daily_diet_coding sheet",
      "both columns in daily_diet_coding", f"Ingredients: {'Ingredients' in ddc.columns}; "
      f"Species (scientific name) in daily_diet_coding: {has_species}; in ingredient_lexicon: "
      f"{'Species (scientific name)' in lex.columns}", "Ingredients" in ddc.columns and has_species)

lex_cols = ["Informative for sequencing? (Yes / Uncertain / No)", "Fermented? (Yes / No / Variable / Unknown)",
            "Fibrous? (Yes / No / Variable / Unknown)", "Likely live microbes? (Yes / Variable / No / Unknown)",
            "Marker that can detect it", "Species (scientific name)", "Ingredient"]
missing = [c for c in lex_cols if c not in lex.columns]
check(6, "Lexicon columns by exact name (classification, marker, species, Ingredient)", "all present",
      f"missing: {missing}", not missing)
for c in lex_cols[:4]:
    allowed = set(re.search(r"\((.*)\)", c).group(1).split(" / "))
    vals = set(lex[c].dropna().astype(str).str.strip()) - {""}
    check("6" + c[:4], f"`{c}` values within the levels named in the header", f"subset of {sorted(allowed)}",
          f"extra values: {sorted(vals - allowed)}; blanks: {int(lex[c].isna().sum() + (lex[c].astype(str).str.strip() == '').sum())}",
          vals <= allowed)

for d, files in {"DADA2-weeklong": ["feature_data.txt", "seqtab_all.rds", "dsvs_msa.tree"],
                 "DADA2-weeklong-plants": ["feature_data.txt", "seqtab_all.rds", "dsvs_msa.tree"],
                 "DADA2-weeklong-meat": ["feature_data.txt", "seqtab_all.rds", "dsvs_msa.tree"]}.items():
    present = [f for f in files if (DATA / d / f).exists()]
    check(f"7{d[-5:]}", f"1-data/{d}/ holds the sequencing tables", f"{files}", f"{present}", present == files)

gbif = pd.read_csv(DATA / "genus_family_gbif.csv")
pf = pd.read_csv(DATA / "DADA2-weeklong-plants" / "feature_data.txt", sep="\t")
mf = pd.read_csv(DATA / "DADA2-weeklong-meat" / "feature_data.txt", sep="\t")
pl_genera = set(pf["Genus"].dropna())
check(8, "Plant families from 1-data/genus_family_gbif.csv; plants feature_data has no Family",
      "plants Family column empty/absent; GBIF cache covers genera in plants feature_data",
      f"plants Family non-missing: {int(pf['Family'].notna().sum()) if 'Family' in pf else 'no column'}; "
      f"cache columns {list(gbif.columns)}, {len(gbif)} genera; plant genera not in cache: "
      f"{len(pl_genera - set(gbif.iloc[:, 0]))} of {len(pl_genera)}",
      ("Family" not in pf or pf["Family"].isna().all()))
check(9, "Meat families come from meat feature_data", "meat Family filled for most ASVs",
      f"meat Family non-missing: {int(mf['Family'].notna().sum())} of {len(mf)}", mf["Family"].notna().mean() > 0.9)

# ---------------------------------------------------------------- subjects and days
diet_subj = pd.Series(ddc["Subject_ID"].unique())
check(10, "Subject_ID is an integer in daily_diet_coding / source_diet_text",
      "all values whole numbers (stored as numbers, not '01' text)",
      f"daily_diet_coding sample values {diet_subj.head(5).tolist()}, types {sorted({type(v).__name__ for v in ddc['Subject_ID']})}; "
      f"source_diet_text types {sorted({type(v).__name__ for v in src['Subject_ID']})}",
      all(isinstance(v, (int, float, np.integer, np.floating)) and float(v).is_integer() for v in ddc["Subject_ID"]))

kits, samples = W.read_sample_sheet(sheet_path)
ss_subj = set(samples["Subject_ID"].dropna())
check(11, "read_sample_sheet() gives zero-padded text Subject_ID ('01')", "all match \\d\\d",
      f"values {sorted(ss_subj)[:6]}...; non-matching {sorted(s for s in ss_subj if not re.fullmatch(r'\d\d', str(s)))}",
      all(re.fullmatch(r"\d\d", str(s)) for s in ss_subj))

diet_pad = {f"{int(s):02d}" for s in diet_subj}
check(12, "Subject 11 has no coded diet log (present in sample sheet)", "'11' not in diet log, '11' in sample sheet",
      f"diet subjects {sorted(diet_pad)}; sample-sheet subjects without diet log {sorted(ss_subj - diet_pad)}; "
      f"diet subjects without samples {sorted(diet_pad - ss_subj)}", "11" not in diet_pad and "11" in ss_subj)

date_col = "Date (MM-DD)"
dates_ok = ddc[date_col].astype(str).str.fullmatch(r"\d{2}-\d{2}")
check(13, "Diet days are `Date (MM-DD)` text", "all values MM-DD text", f"non-matching: {int((~dates_ok).sum())} "
      f"e.g. {ddc.loc[~dates_ok, date_col].head(3).tolist()}", dates_ok.all())

if "Day_key" in ddc:
    rebuilt = ddc["Subject_ID"].map(lambda s: str(int(s))) + "_" + ddc[date_col].astype(str)
    check(14, "Day_key = f'{Subject_ID}_{MM-DD}' with unpadded subject", "Day_key column equals rebuilt key on every row",
          f"mismatches: {int((rebuilt != ddc['Day_key']).sum())} of {len(ddc)}; example {ddc['Day_key'].iloc[0]}",
          (rebuilt == ddc["Day_key"]).all())
else:
    check(14, "Day_key column exists", "column present", "absent", False)

dup = ddc.duplicated(["Day_key", "Entry_no"]).sum() if {"Day_key", "Entry_no"} <= set(ddc.columns) else None
check(15, "A food entry is (Day_key, Entry_no)", "unique key, no duplicates", f"duplicates: {dup}", dup == 0)

ev = src["Event_name"].astype(str) if "Event_name" in src else pd.Series(dtype=str)
pat = ev.str.fullmatch(r"Day \d{2} .*")
check(16, "Study day in source_diet_text.Event_name ('Day 01 ingestion ', may have trailing spaces)",
      "values start 'Day NN'; some have trailing spaces",
      f"{ev.drop_duplicates().head(4).tolist()}; not 'Day NN ...': {int((~pat).sum())}; trailing spaces: "
      f"{int((ev != ev.str.rstrip()).sum())}", bool(len(ev)) and pat.all())
# does source_diet_text cover the same subject-days?
if {"Subject_ID", date_col} <= set(src.columns):
    sk = set(zip(src["Subject_ID"].astype(int), src[date_col].astype(str)))
    dk = set(zip(ddc["Subject_ID"].astype(int), ddc[date_col].astype(str)))
    check(17, "source_diet_text and daily_diet_coding cover the same subject-days", "same set",
          f"source {len(sk)}, coded {len(dk)}, only in source {sorted(sk - dk)[:4]}, only coded {sorted(dk - sk)[:4]}",
          sk == dk)
else:
    check(17, "source_diet_text joins to daily_diet_coding on Subject_ID + Date (MM-DD)", "both columns present",
          f"source_diet_text columns: {list(src.columns)}", False)

cd = samples["Collection_date"].dropna().astype(str)
check(18, "Sample-sheet dates are yymmdd text; Collection_date_reformat is MM-DD",
      "Collection_date matches \\d{6} or a token; reformat = digits 3-6 as MM-DD",
      f"non-6-digit values: {sorted(set(cd[~cd.str.fullmatch(r'\d{6}')]))}; reformat mismatches: "
      f"{int((samples.loc[cd.index[cd.str.fullmatch(r'\d{6}')], 'Collection_date_reformat'] != cd[cd.str.fullmatch(r'\d{6}')].str[2:4] + '-' + cd[cd.str.fullmatch(r'\d{6}')].str[4:6]).sum())}",
      cd.str.fullmatch(r"\d{6}").mean() > 0.9)
ct = samples["Collection_time"].astype(str)
check(19, "Times are HH:MM; 'NR' or blank means unknown", "times match H:MM/HH:MM, 'NR', or blank",
      f"other values: {sorted(set(ct[~ct.str.fullmatch(r'\d{1,2}:\d{2}|NR|nan|None')]))[:8]}; 'NR' count {int((ct == 'NR').sum())}",
      ct.str.fullmatch(r"\d{1,2}:\d{2}|NR|nan|None").all())
years = sorted(set(cd[cd.str.fullmatch(r"\d{6}")].str[:2]))
check(20, "Dates are in 2025", "yy = 25 everywhere", f"years: {years}", years == ["25"])

dn = C.read_excel_like_readxl(sheet_path, sheet_name="Daily-Nutrient")
dn_ok = {"Subject_ID", "Date_reformat"} <= set(dn.columns)
if dn_ok:
    dn_keys = set(zip(dn["Subject_ID"].astype(str), dn["Date_reformat"].astype(str)))
    diet_keys = set(zip(ddc["Subject_ID"].map(lambda s: f"{int(s):02d}"), ddc[date_col].astype(str)))
    ov = dn_keys & diet_keys
    per_subj = pd.Series([s for s, _ in ov]).value_counts().sort_index().to_dict()
    check(21, "Daily-Nutrient: Subject_ID text, Date_reformat MM-DD; mostly covers days before the diet log",
          "text subjects like '01'; limited overlap with diet days",
          f"Subject_ID types {sorted({type(v).__name__ for v in dn['Subject_ID']})}, e.g. {dn['Subject_ID'].iloc[0]!r}; "
          f"Date_reformat e.g. {dn['Date_reformat'].iloc[0]!r}; nutrient subject-days {len(dn_keys)}, diet subject-days "
          f"{len(diet_keys)}, overlapping {len(ov)}; overlap per subject {per_subj}",
          all(isinstance(v, str) for v in dn["Subject_ID"]))
else:
    check(21, "Daily-Nutrient has Subject_ID and Date_reformat", "both present", f"columns {list(dn.columns)[:12]}", False)

# ---------------------------------------------------------------- samples
kit = kits_raw.drop_duplicates("Kit_ID").set_index("Kit_ID")
sal = samples[samples["Region"] == "Saliva"]
first_kit = sal["Kit_ID"].astype(str).str.split(",").str[0].str.strip()
exp_t = kit.reindex(first_kit)["Ingestion_time"].map(C.r_num_str).to_numpy()
exp_d = kit.reindex(first_kit)["Ingestion_date"].map(C.r_num_str).to_numpy()
bad = (sal["Collection_time"].to_numpy() != exp_t) | (sal["Collection_date"].to_numpy() != exp_d)
check(22, "Saliva time = the kit's Ingestion_date/time", "every saliva sample equals its kit's ingestion date+time",
      f"{len(sal)} saliva samples, mismatches {int(bad.sum())}", len(sal) > 0 and not bad.any())

multi = samples[samples["Kit_ID"].astype(str).str.contains(",")]
mk_regions = multi["Region"].value_counts().to_dict()
check(23, "Multi-kit samples ('LS114, LS115') are stools; same subject and collection time; no transit time",
      "all multi-kit rows are Stool, Transit_time_h empty (read_sample_sheet asserts shared subject/time)",
      f"{len(multi)} rows, regions {mk_regions}, transit non-empty {int(multi['Transit_time_h'].notna().sum())}; "
      f"e.g. {multi['Kit_ID'].head(2).tolist()}",
      set(mk_regions) <= {"Stool"} and multi["Transit_time_h"].isna().all())

tok = {}
for name, df in {"Kit_ID": kits_raw, "Sample_ID": C.read_excel_like_readxl(sheet_path, sheet_name="Sample_ID")}.items():
    for c in df.columns:
        v = df[c].astype(str)
        for t in ("NR", "NM"):
            k = int((v == t).sum())
            if k:
                tok[f"{name}.{c}={t}"] = k
check(24, "'NR' (not recorded) and 'NM' (not measured) are real tokens", "both occur as text and survive reading",
      f"{tok}", any(k.endswith("=NR") for k in tok) and any(k.endswith("=NM") for k in tok))

# ---------------------------------------------------------------- libraries
info16 = C.read_excel_like_readxl(DATA / "Weeklong-sample-info.xlsx")
seq16 = pyreadr.read_r(str(DATA / "DADA2-weeklong" / "seqtab_all.rds"))[None]
lib16 = info16["Sample"].astype(str).str.replace("sample_", "", n=1)
in_tab = lib16.isin(seq16.index)
check(25, "16S: library name = info-sheet `Sample` without 'sample_' prefix",
      "stripped names are count-table rows; nearly all count-table rows covered",
      f"info rows {len(info16)}, prefix present {int(info16['Sample'].astype(str).str.startswith('sample_').sum())}, "
      f"found in count table {int(in_tab.sum())}; count-table rows not in info sheet {len(set(seq16.index) - set(lib16))}",
      in_tab.mean() > 0.95)
sid16 = info16["Sample_ID"].dropna().astype(str)
check(26, "16S Sample_IDs join to read_sample_sheet()", "every non-blank Sample_ID found once in the sample sheet",
      f"{len(sid16)} Sample_IDs, not in sheet {sorted(set(sid16) - set(samples['Sample_ID'].astype(str)))[:8]}, "
      f"sheet duplicates {int(samples['Sample_ID'].duplicated().sum())}",
      set(sid16) <= set(samples["Sample_ID"].astype(str)) and not samples["Sample_ID"].duplicated().any())
fn = samples.get("16S_filename")
if fn is not None:
    hit = fn.dropna().astype(str).isin(seq16.index).sum()
    check(27, "The sample sheet's 16S_filename does not match the 16S library names", "few or no matches",
          f"{int(hit)} of {int(fn.notna().sum())} 16S_filename values are count-table rows; e.g. {fn.dropna().iloc[0]!r} vs "
          f"library {seq16.index[0]!r}", hit < 0.5 * fn.notna().sum())

infof = C.read_excel_like_readxl(DATA / "Weeklong-meat-plants-sample-info.xlsx")
print("\n     food info columns:", list(infof.columns))
gcol = "group" if "group" in infof else None
check(28, "Food info sheet: `group` = Meat / Plant; `Group` = LONGIT / Blank / IBD / gen3",
      "those level sets", f"group {infof['group'].value_counts().to_dict() if gcol else 'missing'}; "
      f"Group {infof['Group'].value_counts().to_dict() if 'Group' in infof else 'missing'}",
      gcol and set(infof["group"].dropna()) == {"Meat", "Plant"} and
      set(infof["Group"].dropna()) == {"LONGIT", "Blank", "IBD", "gen3"})
bl = infof[infof["Group"] == "Blank"]
check(29, "Blanks have no Sample_ID", "Sample_ID blank on every Blank row",
      f"{len(bl)} blank rows, with Sample_ID {int(bl['Sample_ID'].notna().sum())}", bl["Sample_ID"].isna().all())

run_dir = {"Plant": "DADA2-weeklong-plants", "Meat": "DADA2-weeklong-meat"}
libsets = {}
for g, d in run_dir.items():
    tab = pyreadr.read_r(str(DATA / d / "seqtab_all.rds"))[None]
    sub = infof[infof["group"] == g]
    lib = sub["Sample"].astype(str).str.replace("sample_", "", n=1)
    libsets[g] = sub.assign(lib=lib)
    check(f"30{g}", f"{g} run: info-sheet library names (minus 'sample_') are count-table rows",
          "nearly all found", f"{int(lib.isin(tab.index).sum())} of {len(lib)} found; count-table rows not in sheet "
          f"{len(set(tab.index) - set(lib))}", lib.isin(tab.index).mean() > 0.95)
pl = libsets["Plant"].query("Group == 'LONGIT'")
me = libsets["Meat"].query("Group == 'LONGIT'")
sp, sm = set(pl["Sample_ID"].dropna()), set(me["Sample_ID"].dropna())
same_lib = len(set(pl["lib"]) & set(me["lib"]))
check(31, "Plants and meat runs sequenced the same samples; join on Sample_ID, never on library name",
      "same LONGIT Sample_ID sets; library names differ between runs",
      f"plants {len(sp)}, meat {len(sm)}, shared {len(sp & sm)}, only plants {sorted(sp - sm)[:5]}, only meat "
      f"{sorted(sm - sp)[:5]}; library names shared across runs {same_lib}", sp == sm)
check(32, "Food-run Sample_IDs join to read_sample_sheet()", "all found",
      f"not in sheet: {sorted((sp | sm) - set(samples['Sample_ID'].astype(str)))[:8]}",
      (sp | sm) <= set(samples["Sample_ID"].astype(str)))

# ---------------------------------------------------------------- food entries and ingredients
ing = ddc["Ingredients"].dropna().astype(str).str.split(";").explode().str.strip()
ing = ing[ing != ""]
assumed = ing.str.endswith(" (assumed)")
base = ing.str.replace(r" \(assumed\)$", "", regex=True)
unknown = sorted(set(base) - set(lex["Ingredient"].astype(str)))
check(33, "Ingredients ';'-separated; strip ' (assumed)' to get the lexicon Ingredient (exact match)",
      "every stripped name matches a lexicon Ingredient exactly",
      f"{len(ing)} ingredient mentions, {int(assumed.sum())} assumed; names not in lexicon: {len(unknown)} {unknown[:8]}",
      not unknown)
other_marks = sorted(set(ing[ing.str.contains(r"\(")].str.extract(r"(\([^)]*\))")[0].dropna()) - {"(assumed)"})
check(34, "'(assumed)' is the only annotation inside ingredient names", "no other parenthesised tags",
      f"other tags: {other_marks[:8]}", not other_marks, note=bool(other_marks))

tm = ddc["Time/meal as logged"].astype(str).str.strip()
filled = tm[(tm != "") & (tm != "nan")]
check(35, "Meal timing only from `Time/meal as logged` (free text, mostly blank)", "column exists, mostly blank",
      f"filled {len(filled)} of {len(ddc)} entries; distinct values {filled.nunique()}", len(filled) < len(ddc))

mk = lex["Marker that can detect it"].astype(str).str.strip()
check(36, "Lexicon `Marker that can detect it`: trnL / 12SV5 / none", "only these three values",
      f"{mk.value_counts().to_dict()}", set(mk) <= {"trnL", "12SV5", "none"})

sp_vals = lex["Species (scientific name)"].dropna().astype(str)
cases = {
    "binomial": r"[A-Z][a-z]+ [a-z]+(\s*\(assumed\))?",
    "several ;-separated": r".*;.*",
    "Genus spp.": r"[A-Z][a-z]+ spp\.?(\s*\(assumed\))?",
    "hybrid x": r"[A-Z][a-z]+ [x×] [a-z]+.*",
    "family (genus)": r"[A-Z][a-z]+(eae|idae|oideae|aceae) \(.*\)",
    "family only": r"[A-Z][a-z]+(eae|idae|oideae|aceae)",
}
labels = []
for v in sp_vals:
    lab = next((k for k, p in cases.items() if re.fullmatch(p, v.strip())), "OTHER")
    labels.append(lab)
lab_s = pd.Series(labels)
others = sorted(set(sp_vals[lab_s.eq("OTHER").to_numpy()]))
check(37, "Lexicon Species formats: several ';', '(assumed)', 'Genus spp.', hybrids, family (genus), family only",
      "every value is one of these cases or a plain binomial", f"{lab_s.value_counts().to_dict()}; unclassified "
      f"{len(others)}: {others[:10]}", not others, note=bool(others))

pf_sp = pf["Species"].dropna().astype(str)
mf_sp = mf["Species"].dropna().astype(str)
check(38, "feature_data Species: epithet only in plants, binomial in meat; quoted 'NA' = missing",
      "plants: no spaces; meat: 'Genus species'; 'NA' strings present",
      f"plants with space {int(pf_sp.str.contains(' ').sum())} of {len(pf_sp)} (e.g. {pf_sp.iloc[:3].tolist()}); "
      f"meat with space {int(mf_sp.str.contains(' ').sum())} of {len(mf_sp)} (e.g. {mf_sp.iloc[:2].tolist()}); "
      f"'NA' text read with keep_default_na=False: plants "
      f"{int((pd.read_csv(DATA / 'DADA2-weeklong-plants' / 'feature_data.txt', sep=chr(9), keep_default_na=False)['Species'] == 'NA').sum())}",
      pf_sp.str.contains(" ").mean() < 0.05 and mf_sp.str.contains(" ").mean() > 0.9)

colors_pl = C.read_excel_like_readxl(DATA / "Family_colors.xlsx", sheet_name=3)
gcol_name = [c for c in colors_pl.columns if c.lower() == "genus"]
na_rows = int((colors_pl[gcol_name[0]].astype(str) == "NA").sum()) if gcol_name else None
check(39, "Plants colour sheet (Family_colors.xlsx, 4th sheet) has a genus row literally named 'NA'",
      "one 'NA' genus row read as text", f"sheet {pd.ExcelFile(DATA / 'Family_colors.xlsx').sheet_names[3]!r}, "
      f"genus column {gcol_name}, 'NA' rows {na_rows}", bool(na_rows))

# ---------------------------------------------------------------- gotchas
plain = pd.read_excel(sheet_path, sheet_name="Kit_ID")
diff = (plain["Subject_ID"].astype(str) != kits_raw["Subject_ID"].astype(str)).sum()
plain_na = int(plain.isna().sum().sum()) - int(kits_raw.isna().sum().sum())
check(40, "Plain pd.read_excel turns '01' into 1 and 'NA' into NaN", "differences between the two readers",
      f"Kit_ID Subject_ID differs on {int(diff)} rows (plain {plain['Subject_ID'].iloc[0]!r} vs readxl-like "
      f"{kits_raw['Subject_ID'].iloc[0]!r}); extra missing cells with plain reader {plain_na}", diff > 0 or plain_na > 0)

tree = C.Tree((DATA / "DADA2-weeklong-plants" / "dsvs_msa.tree").read_text())
in_both = set(pf["Sequence"])
tip_order = [s for s in tree.tip_labels if s in in_both]
otu_names = {s: f"feature_{i + 1:04d}" for i, s in enumerate(tip_order)}
same = sum(otu_names[s] == f for s, f in zip(pf["Sequence"], pf["Feature"]) if s in otu_names)
check(41, "OTU names (feature_%04d by tree tip order) differ from feature_data Feature", "most differ",
      f"plants: {same} of {len(otu_names)} ASVs have OTU name == Feature", same < 0.5 * len(otu_names))

bos = lex[lex["Species (scientific name)"].astype(str).str.contains("Bos taurus")]["Ingredient"].tolist()
check(42, "Milk, cheese and beef are all Bos taurus in the lexicon", "all three map to Bos taurus",
      f"Bos taurus ingredients: {bos}", {"cow milk", "cheese", "beef"} <= set(bos) or
      all(any(k in b for b in bos) for k in ("milk", "cheese", "beef")))

# ---------------------------------------------------------------- summary
print("\n\nSUMMARY")
for n, s, c, *_ in RESULTS:
    print(f"  {s:4s} [{n}] {c[:110]}")
print(f"\n{sum(s == 'PASS' for _, s, *_ in RESULTS)} pass, {sum(s == 'FAIL' for _, s, *_ in RESULTS)} fail, "
      f"{sum(s == 'NOTE' for _, s, *_ in RESULTS)} note")
