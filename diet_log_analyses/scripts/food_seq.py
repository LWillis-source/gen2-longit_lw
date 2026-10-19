"""Food-sequencing tables (trnL plants run, 12SV5 meat run) for the diet-log notebooks.

Follows diet_log_analyses/CLAUDE.md ("Samples", "Ingredients to taxa"):
- libraries -> Sample_ID through 1-data/Weeklong-meat-plants-sample-info.xlsx (Sample minus 'sample_'),
  count table seqtab_all.rds, taxonomy feature_data.txt;
- lexicon marker trnL = plants run, 12SV5 = meat run; other markers cannot be matched;
- ingredient -> compatible ASVs by the rule in CLAUDE.md (congener fallback included);
- species whose compatible ASVs overlap are merged into one "food taxon" (sequencing cannot separate them);
  a recipe listing several species belongs to several taxa.
"""
import re

import pandas as pd
import pyreadr

import _paths
import config as C

RUN_DIRS = {"plants": "DADA2-weeklong-plants", "meat": "DADA2-weeklong-meat"}
RUN_OF_MARKER = {"trnL": "plants", "12SV5": "meat"}
INFO_GROUP = {"plants": "Plant", "meat": "Meat"}
SPECIES = "Species (scientific name)"
_FAMILY = re.compile(r"^[A-Z][a-z]+(eae|idae|oideae|aceae)\b")


def split_species(field):
    """Split a lexicon species field on ';' outside brackets."""
    parts, depth, cur = [], 0, ""
    for ch in str(field):
        depth += (ch == "(") - (ch == ")")
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in parts + [cur] if p.strip()]


def parse_species(sp):
    """(format, genus, epithet) of one lexicon species value; genus None = undetectable (CLAUDE.md)."""
    s = re.sub(r"\s*\(assumed\)", "", sp).strip()
    if re.match(r"^(unspecified|mixed|none|unknown)\b", s):
        return "no taxon", None, None
    if "/" in s:
        return "slash list", None, None
    if _FAMILY.match(s):
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
        return ("var./subsp." if re.search(r" (var\.|subsp\.) ", s) else "binomial"), w[0], w[1]
    return "unclassified", None, None


def compatible_asvs(field, tax, run):
    """Sequences of the ASVs compatible with a lexicon species field in one run (CLAUDE.md rule)."""
    out = set()
    for sp in split_species(field):
        _, genus, epi = parse_species(sp)
        if genus is None:
            continue
        g = tax[tax["Genus"] == genus]
        if epi is None:
            out |= set(g["Sequence"])
            continue
        lab, unl = g["Species"].astype(str), g["Species"].isna()
        if run == "plants":   # plants store the epithet ('oleracea', 'oleracea_subsp_var.')
            same = ~unl & ((lab == epi) | lab.str.startswith(epi + "_"))
        else:                 # meat stores the binomial ('Bos taurus'); hybrid labels never match
            same = ~unl & (lab == f"{genus} {epi}")
        out |= set(g["Sequence"][same | unl]) if same.any() else set(g["Sequence"])   # congener fallback
    return out


def load_runs():
    """{run: (counts DataFrame libraries x ASV sequences, taxonomy DataFrame)} from seqtab_all.rds and feature_data.txt."""
    out = {}
    for run, d in RUN_DIRS.items():
        counts = pyreadr.read_r(str(C.DATA_DIR / d / "seqtab_all.rds"))[None]
        tax = pd.read_csv(C.DATA_DIR / d / "feature_data.txt", sep="\t")
        out[run] = (counts, tax)
    return out


def food_taxa(lexicon, runs, informative_only=True, levels=("Yes",)):
    """Merge lexicon ingredients into food taxa that sequencing can tell apart.

    Each species named in an ingredient's species field is matched to its compatible ASVs separately; species parts
    of one run whose ASVs overlap are merged (union-find). A recipe listing several species (e.g. kimchi) therefore
    belongs to several taxa, but cannot glue unrelated taxa together.

    Returns (taxa, membership). taxa: one row per food taxon (taxon_id, run, label, n_asvs, ingredients, asvs).
    membership: ingredient -> sorted list of taxon_ids, for every ingredient with at least one compatible ASV.
    """
    lex = lexicon
    if informative_only:   # levels: which `Informative for sequencing?` values to include (default: Yes only)
        lex = lex[lex["Informative for sequencing? (Yes / Uncertain / No)"].isin(levels)]
    parts = []   # (ingredient, run, (genus, epithet), asvs) for each species part with compatible ASVs
    for r in lex.itertuples(index=False):
        run = RUN_OF_MARKER.get(r[lex.columns.get_loc("Marker that can detect it")])
        if run is None:
            continue
        for sp in split_species(r[lex.columns.get_loc(SPECIES)]):
            asvs = compatible_asvs(sp, runs[run][1], run)
            if asvs:
                _, genus, epi = parse_species(sp)
                parts.append((r.Ingredient, run, (genus, epi), asvs))
    parent = list(range(len(parts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if parts[i][1] == parts[j][1] and parts[i][3] & parts[j][3]:
                parent[find(i)] = find(j)
    groups = {}
    for i, part in enumerate(parts):
        groups.setdefault(find(i), []).append(part)
    taxa, member = [], {}
    for k, g in enumerate(sorted(groups.values(), key=lambda g: sorted(x[0] for x in g)[0])):
        tid = f"T{k + 1:03d}"
        parsed = {x[2] for x in g}
        genera = sorted({ge for ge, _ in parsed})
        if len(parsed) == 1 and next(iter(parsed))[1]:
            label = " ".join(next(iter(parsed)))
        elif len(genera) == 1:
            label = f"{genera[0]} spp."
        else:
            label = " / ".join(genera)
        asvs = set().union(*(x[3] for x in g))
        ings = sorted({x[0] for x in g})
        taxa.append({"taxon_id": tid, "run": g[0][1], "label": label, "n_asvs": len(asvs),
                     "ingredients": ", ".join(ings), "asvs": asvs})
        for ing in ings:
            member.setdefault(ing, []).append(tid)
    return pd.DataFrame(taxa), {k: sorted(v) for k, v in member.items()}


def libraries(samples, runs, min_reads):
    """LONGIT food-run libraries joined to the sample sheet: one row per (run, Sample_ID) with reads and inclusion flag."""
    info = C.read_excel_like_readxl(C.DATA_DIR / "Weeklong-meat-plants-sample-info.xlsx")
    out = []
    for run, (counts, _) in runs.items():
        sub = info[(info["group"] == INFO_GROUP[run]) & (info["Group"] == "LONGIT")].copy()
        sub["library"] = sub["Sample"].str.replace("sample_", "", n=1)
        sub["reads"] = sub["library"].map(counts.sum(axis=1)).fillna(0).astype(int)
        sub["run"] = run
        out.append(sub[["run", "Sample_ID", "library", "reads"]])
    lib = pd.concat(out, ignore_index=True)
    lib = lib.merge(samples[["Sample_ID", "Subject_ID", "Sample_origin3", "Region", "Collection_date_reformat"]],
                    on="Sample_ID", how="left")
    lib["included"] = lib["reads"] >= min_reads
    return lib


def taxon_abundance(lib, taxa, runs):
    """Relative abundance of each food taxon in each library of its run: long table (run, library, taxon_id, rel)."""
    out = []
    for run, (counts, _) in runs.items():
        libs = lib.loc[lib["run"] == run, "library"]
        libs = libs[libs.isin(counts.index)]
        sub = counts.loc[libs]
        total = sub.sum(axis=1)
        for t in taxa[taxa["run"] == run].itertuples(index=False):
            cols = [a for a in t.asvs if a in sub.columns]
            rel = sub[cols].sum(axis=1) / total.where(total > 0)
            out.append(pd.DataFrame({"run": run, "library": rel.index, "taxon_id": t.taxon_id, "rel": rel.to_numpy()}))
    return pd.concat(out, ignore_index=True)


def match_detail(field, tax, run):
    """How each species of a lexicon field matches the run's ASVs (for checking the naming conventions).

    One row per species part: format, genus, epithet, whether the genus occurs in the run at all, the number of ASVs
    labelled with the exact species, unlabelled ASVs of the genus, congener-labelled ASVs, whether the congener fallback
    was used, the compatible ASVs (as compatible_asvs counts them) and the species labels the run uses for that genus.
    """
    rows = []
    for sp in split_species(field):
        fmt, genus, epi = parse_species(sp)
        r = {"species_part": sp, "format": fmt, "genus": genus, "epithet": epi, "genus_in_run": False, "exact": 0,
             "unlabelled": 0, "congener": 0, "fallback": False, "compatible": 0, "run_labels": ""}
        if genus is not None:
            g = tax[tax["Genus"] == genus]
            r["genus_in_run"] = len(g) > 0
            lab, unl = g["Species"].astype(str), g["Species"].isna()
            if epi is None:
                r["unlabelled"], r["congener"] = int(unl.sum()), int((~unl).sum())
                r["compatible"] = len(g)
            else:
                same = ~unl & (((lab == epi) | lab.str.startswith(epi + "_")) if run == "plants" else (lab == f"{genus} {epi}"))
                r["exact"], r["unlabelled"], r["congener"] = int(same.sum()), int(unl.sum()), int((~unl & ~same).sum())
                # congener fallback: the genus has labelled ASVs, but none with the food's own species
                r["fallback"] = bool(len(g) and not same.any() and (~unl).any())
                r["compatible"] = len(g) if r["fallback"] else int((same | unl).sum())
            r["run_labels"] = ", ".join(f"{k} ({v})" for k, v in lab[~unl].value_counts().head(4).items())
        rows.append(r)
    return pd.DataFrame(rows)
