"""Profile every data source used by the diet-log analyses (CLAUDE.md workflow step 0).

Writes one Markdown report per input to figures/input_profiles/, plus joins.md (how well the
documented joins match up) and manifest.json (checksum and modification time of every input).
Run from the repository root:
    /opt/anaconda3/bin/python diet_log_analyses/scripts/profile_inputs.py
The reports describe the inputs; they do not test the CLAUDE.md rules (that is scripts/tests/).
If an input changed since the last run, the previous manifest is kept as manifest_previous.json
and the changed files are listed in changes.md.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyreadr

import _paths
import config as C
import weeklong_16s as W

OUT = _paths.FIG_DIR / "input_profiles"
DATA = C.DATA_DIR
MAX_LISTED = 25  # list every distinct value when a column has at most this many
WIDE = 200  # sheets with more columns are summarised as a whole
TOKENS = ["NA", "NR", "NM", "(assumed)"]

WORKBOOKS = {
    "sample_sheet": C.SAMPLE_SHEET,
    "daily_diet_coding": _paths.DIET_CODING,
    "16S_sample_info": DATA / "Weeklong-sample-info.xlsx",
    "food_sample_info": DATA / "Weeklong-meat-plants-sample-info.xlsx",
    "family_colors": DATA / "Family_colors.xlsx",
}
TEXT_FILES = {
    "16S_feature_data": DATA / "DADA2-weeklong" / "feature_data.txt",
    "plants_feature_data": DATA / "DADA2-weeklong-plants" / "feature_data.txt",
    "meat_feature_data": DATA / "DADA2-weeklong-meat" / "feature_data.txt",
    "genus_family_gbif": DATA / "genus_family_gbif.csv",
}
COUNT_TABLES = {
    "16S_seqtab_all": DATA / "DADA2-weeklong" / "seqtab_all.rds",
    "plants_seqtab_all": DATA / "DADA2-weeklong-plants" / "seqtab_all.rds",
    "meat_seqtab_all": DATA / "DADA2-weeklong-meat" / "seqtab_all.rds",
}
# key columns expected to identify rows uniquely: (input, sheet) -> columns
KEYS = {
    ("sample_sheet", "Kit_ID"): ["Kit_ID"],
    ("sample_sheet", "Sample_ID"): ["Sample_ID"],
    ("daily_diet_coding", "daily_diet_coding"): ["Day_key", "Entry_no"],
    ("daily_diet_coding", "source_diet_text"): ["Subject_ID", "Date (MM-DD)"],
    ("daily_diet_coding", "ingredient_lexicon"): ["Ingredient"],
    ("16S_sample_info", "all"): ["Sample"],
    ("food_sample_info", "Sheet1"): ["Sample"],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cell(v, width=60):
    s = str(v).replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= width else s[: width - 1] + "…"


def file_header(name, path):
    st = path.stat()
    return [f"# {name}", "", f"- File: `{path}`",
            f"- Modified: {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M}",
            f"- Size: {st.st_size:,} bytes", f"- SHA-256: `{sha256(path)}`",
            f"- Profiled: {datetime.now():%Y-%m-%d %H:%M} by `diet_log_analyses/scripts/profile_inputs.py`", ""]


def column_rows(df):
    rows = ["| Column | Types | Missing | Distinct | Tokens | Values |", "|---|---|---|---|---|---|"]
    for c in df.columns:
        s = df[c]
        missing = int(s.isna().sum() + (s.astype(str).str.strip() == "").sum())
        present = s.dropna()
        present = present[present.astype(str).str.strip() != ""]
        types = ", ".join(sorted({type(v).__name__ for v in present})) or "—"
        text = present.astype(str)
        tok = {t: int(text.str.contains(re.escape(t)).sum() if t.startswith("(") else (text == t).sum()) for t in TOKENS}
        tok = ", ".join(f"{k}: {v}" for k, v in tok.items() if v)
        nd = text.nunique()
        if nd <= MAX_LISTED and text.str.len().mean() < 60:
            vals = "; ".join(f"{cell(k, 40)} ({v})" for k, v in text.value_counts().sort_index().items())
        else:
            num = pd.to_numeric(present, errors="coerce")
            rng = f"range {num.min():g}–{num.max():g}; " if num.notna().all() and len(num) else ""
            vals = rng + "e.g. " + "; ".join(cell(v, 40) for v in text.drop_duplicates().head(4))
        rows.append(f"| {cell(c, 50)} | {types} | {missing} | {nd} | {tok or '—'} | {vals} |")
    return rows


def key_rows(name, sheet, df):
    cols = KEYS.get((name, sheet))
    if not cols:
        return []
    if not set(cols) <= set(df.columns):
        return [f"- Key {cols}: **columns missing**", ""]
    dup = int(df.duplicated(cols).sum())
    return [f"- Key {' + '.join(cols)}: {'unique' if dup == 0 else f'**{dup} duplicate rows**'}", ""]


def profile_workbook(name, path):
    lines = file_header(name, path)
    sheets = pd.ExcelFile(path).sheet_names
    lines += [f"Sheets ({len(sheets)}): " + ", ".join(f"`{s}`" for s in sheets), ""]
    for sh in sheets:
        df = C.read_excel_like_readxl(path, sheet_name=sh)
        lines += [f"## Sheet `{sh}`", "", f"- {len(df)} rows x {df.shape[1]} columns", ""]
        lines += key_rows(name, sh, df)
        if df.shape[1] > WIDE:
            num = df.apply(pd.to_numeric, errors="coerce")
            lines += [f"- Wide sheet: first columns {', '.join(f'`{c}`' for c in df.columns[:5])}; "
                      f"numeric cells {int(num.notna().sum().sum()):,} of {df.size:,}", ""]
            continue
        lines += column_rows(df) + [""]
    return lines


def profile_text(name, path):
    df = pd.read_csv(path, sep="\t" if path.suffix == ".txt" else ",", keep_default_na=False, na_values=[""])
    lines = file_header(name, path) + [f"- {len(df)} rows x {df.shape[1]} columns", ""]
    return lines + column_rows(df) + [""]


def profile_counts(name, path):
    t = pyreadr.read_r(str(path))[None]
    reads = t.sum(axis=1)
    return file_header(name, path) + [
        f"- {t.shape[0]} libraries x {t.shape[1]} ASVs; total reads {int(reads.sum()):,}",
        f"- Reads per library: min {int(reads.min()):,}, median {int(reads.median()):,}, max {int(reads.max()):,}; "
        f"libraries with 0 reads: {int((reads == 0).sum())}",
        f"- Example library names: {', '.join(f'`{x}`' for x in t.index[:3])}", ""]


def joins():
    """Coverage of every join path documented in CLAUDE.md, as counts."""
    ddc = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="daily_diet_coding")
    lex = C.read_excel_like_readxl(_paths.DIET_CODING, sheet_name="ingredient_lexicon")
    _, samples = W.read_sample_sheet(C.SAMPLE_SHEET)
    sheet_ids = set(samples["Sample_ID"].astype(str))
    rows = ["# Join coverage", "", f"Profiled {datetime.now():%Y-%m-%d %H:%M}. Each row: a join documented in "
            "diet_log_analyses/CLAUDE.md and how many keys find a partner.", "",
            "| Join | Left keys | Matched | Unmatched (examples) |", "|---|---|---|---|"]

    def add(label, left, right):
        left, right = set(left), set(right)
        miss = sorted(left - right)
        rows.append(f"| {label} | {len(left)} | {len(left & right)} | {len(miss)}"
                    + (f" ({', '.join(cell(m, 30) for m in miss[:4])})" if miss else "") + " |")

    diet_subj = {f"{int(s):02d}" for s in ddc["Subject_ID"]}
    add("diet subjects -> sample-sheet subjects", diet_subj, samples["Subject_ID"].dropna())
    add("sample-sheet subjects -> diet subjects", samples["Subject_ID"].dropna(), diet_subj)
    ings = {re.sub(r" \(assumed\)$", "", p.strip()) for s in ddc["Ingredients"].dropna() for p in str(s).split(";") if p.strip()}
    add("diet ingredients -> lexicon Ingredient", ings, lex["Ingredient"])
    dn = C.read_excel_like_readxl(C.SAMPLE_SHEET, sheet_name="Daily-Nutrient")
    diet_days = set(zip(ddc["Subject_ID"].map(lambda s: f"{int(s):02d}"), ddc["Date (MM-DD)"].astype(str)))
    add("diet subject-days -> Daily-Nutrient days", diet_days,
        set(zip(dn["Subject_ID"].astype(str), dn["Date_reformat"].astype(str))))
    info16 = C.read_excel_like_readxl(DATA / "Weeklong-sample-info.xlsx")
    t16 = pyreadr.read_r(str(COUNT_TABLES["16S_seqtab_all"]))[None]
    lib16 = info16["Sample"].str.replace("sample_", "", n=1)
    add("16S info-sheet libraries -> count table", lib16, t16.index)
    add("16S count-table rows -> info sheet", t16.index, lib16)
    add("16S info-sheet Sample_ID -> sample sheet", info16["Sample_ID"].dropna().astype(str), sheet_ids)
    infof = C.read_excel_like_readxl(DATA / "Weeklong-meat-plants-sample-info.xlsx")
    ids = {}
    for g, key in {"Plant": "plants_seqtab_all", "Meat": "meat_seqtab_all"}.items():
        t = pyreadr.read_r(str(COUNT_TABLES[key]))[None]
        sub = infof[infof["group"] == g]
        add(f"{g} info-sheet libraries -> count table", sub["Sample"].str.replace("sample_", "", n=1), t.index)
        add(f"{g} count-table rows -> info sheet", t.index, sub["Sample"].str.replace("sample_", "", n=1))
        ids[g] = set(sub.loc[sub["Group"] == "LONGIT", "Sample_ID"].dropna().astype(str))
        add(f"{g} LONGIT Sample_ID -> sample sheet", ids[g], sheet_ids)
    add("plants LONGIT Sample_ID -> meat LONGIT Sample_ID", ids["Plant"], ids["Meat"])
    add("meat LONGIT Sample_ID -> plants LONGIT Sample_ID", ids["Meat"], ids["Plant"])
    return rows + [""]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    old_path = OUT / "manifest.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else None
    manifest, changed = {}, []
    jobs = [(n, p, profile_workbook) for n, p in WORKBOOKS.items()]
    jobs += [(n, p, profile_text) for n, p in TEXT_FILES.items()]
    jobs += [(n, p, profile_counts) for n, p in COUNT_TABLES.items()]
    for name, path, fn in jobs:
        st = path.stat()
        manifest[name] = {"path": str(path), "sha256": sha256(path), "size": st.st_size,
                          "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}
        report = OUT / f"{name}.md"
        if old and name in old and old[name]["sha256"] != manifest[name]["sha256"]:
            changed.append(name)
            if report.exists():  # keep the report of the previous version for comparison
                (OUT / "previous").mkdir(exist_ok=True)
                report.replace(OUT / "previous" / report.name)
        report.write_text("\n".join(fn(name, path)) + "\n")
        print(f"profiled {name}")
    (OUT / "joins.md").write_text("\n".join(joins()) + "\n")

    changes = ["# Input changes", "", f"Profiled {datetime.now():%Y-%m-%d %H:%M}.", ""]
    if old is None:
        changes += ["- First profile: no earlier manifest to compare with.", ""]
    else:
        new = [n for n in manifest if n not in old]
        if changed or new:
            (OUT / "manifest_previous.json").write_text(old_path.read_text())
        changes += [f"- Changed since the last profile: {', '.join(changed) or 'none'}",
                    f"- New inputs: {', '.join(new) or 'none'}", ""]
        if changed:
            changes += ["The previous reports of these inputs are in previous/. Compare them with the new ones, "
                        "classify every difference (correction vs change of meaning), and rerun scripts/tests/ "
                        "(CLAUDE.md step 0).", ""]
    old_path.write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "changes.md").write_text("\n".join(changes))
    print("\n".join(changes))


if __name__ == "__main__":
    main()
