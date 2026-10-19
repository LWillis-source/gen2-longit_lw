"""Check the Genus/Family/Order/Class columns of ingredient_lexicon against GBIF.

Run in Jupyter or a terminal on a machine that can reach api.gbif.org:
    python verify_lexicon_taxonomy_gbif.py
Writes lexicon_taxonomy_gbif_check.csv (one row per genus). NOT yet run: the
environment that built the columns could not reach GBIF.
"""
import re, time, requests, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent

FILE = str(HERE.parent / "daily_diet_coding.xlsx")
lex = pd.read_excel(FILE, sheet_name="ingredient_lexicon")
rows = []
for _, r in lex.iterrows():
    gs = [g.strip() for g in str(r["Genus"]).split(";")] if pd.notna(r["Genus"]) else []
    fam = [x.strip() for x in str(r["Family"]).split(";")] if pd.notna(r["Family"]) else []
    for i, g in enumerate(gs):
        if g and g != "-":
            rows.append({"genus": g, "family": fam[i] if i < len(fam) else "",
                         "order": str(r["Order"]).split(";")[i].strip() if pd.notna(r["Order"]) else "",
                         "class": str(r["Class"]).split(";")[i].strip() if pd.notna(r["Class"]) else ""})
mine = pd.DataFrame(rows).drop_duplicates("genus").reset_index(drop=True)

out = []
for _, m in mine.iterrows():
    j = requests.get("https://api.gbif.org/v1/species/match",
                     params={"name": m.genus, "rank": "GENUS"}, timeout=30).json()
    out.append({**m.to_dict(), "gbif_status": j.get("status"), "gbif_match": j.get("matchType"),
                "gbif_family": j.get("family"), "gbif_order": j.get("order"), "gbif_class": j.get("class"),
                "family_agrees": j.get("family") == m.family, "order_agrees": j.get("order") == m["order"],
                "class_agrees": j.get("class") == m["class"]})
    time.sleep(0.1)
res = pd.DataFrame(out)
res.to_csv(HERE / "lexicon_taxonomy_gbif_check.csv", index=False)
print(res[["family_agrees", "order_agrees", "class_agrees"]].mean())
print(res[~(res.family_agrees & res.order_agrees & res.class_agrees)])
