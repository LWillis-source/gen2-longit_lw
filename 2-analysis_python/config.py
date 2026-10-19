"""Shared setup and helper functions for the Python 16S analyses.

Python counterpart of ``0-config.R``. It provides:

* paths to the repository's data and figure folders,
* ``setup_tables`` (builds the ASV table, taxonomy, sample sheet and tree),
* a minimal stand-in for a phyloseq object (``PS``) with the operations the
  Weeklong notebook uses (subset_samples, prune_taxa, transform_sample_counts,
  psmelt, ...),
* beta-diversity distances matching phyloseq::distance (bray, canberra,
  binary, unifrac, wunifrac) and PCoA matching ape::pcoa,
* ggplot2-like plotting helpers (colours, themes, histograms, nested facets).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
from scipy.spatial.distance import cdist, squareform

import matplotlib

matplotlib.use("Agg")  # write files only, never open windows
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgba  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

##########################
# Paths
##########################

REPO_DIR = Path(__file__).resolve().parents[1]  # gen2-longit/
DATA_DIR = REPO_DIR / "1-data"
FIG_DIR = REPO_DIR / "3-figures_python"

# The R notebook reads the sample sheet from a personal Dropbox path. The same
# workbook lives in the sibling gen2_capScan_sanitized00 repository; override
# with the WEEKLONG_SAMPLE_SHEET environment variable if it moves.
# This is the corrected sheet (sheets Kit_ID and Sample_ID; subject and timing on Kit_ID);
# weeklong_16s.read_sample_sheet() joins the two. The earlier layout
# (LONGIT-Weeklong_SampleSheet_FINAL.xlsx) is in pre-corrections/ and is no longer read.
SAMPLE_SHEET = Path(os.environ.get(
    "WEEKLONG_SAMPLE_SHEET",
    REPO_DIR.parent / "gen2_capScan_sanitized00" / "data" / "work-in-progress-meta"
    / "LONGITWeeklong-samplesheet-FINAL.xlsx",
))

GREY50 = "#7F7F7F"  # ggplot2's na.value for fill scales

##########################
# Small R-compatibility helpers
##########################


def r_sort_key(value):
    """Approximate R's locale string sort (case-insensitive, punctuation first)."""
    s = str(value)
    return (s.casefold(), s)


def r_num_str(value):
    """Format an Excel cell the way readxl does for a text column ("6", "5.5", "3E")."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return str(int(value)) if float(value).is_integer() else f"{value:.15g}"
    return str(value)


def read_excel_like_readxl(path, sheet_name=0):
    """pd.read_excel with readxl's defaults.

    readxl only treats blank cells as missing, so a literal "NA" in a cell stays the string
    "NA" (in this workbook it is a real category, e.g. Prediction == "NA"), and a column that
    contains any text becomes a text column (numbers in it are kept as strings like "6").
    """
    # dtype=object stops pandas from re-parsing text cells ("01" would otherwise become 1)
    df = pd.read_excel(path, sheet_name=sheet_name, keep_default_na=False, na_values=[""], dtype=object)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, str)).any():
            df[col] = df[col].map(r_num_str)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def ordered_categorical(series, levels):
    """R's factor(x, levels = ..., ordered = TRUE): values not in levels become NaN."""
    return pd.Categorical(series, categories=levels, ordered=True)


def sorted_levels(values):
    """Levels of an R factor built from values: numbers sort numerically, strings by locale."""
    vals = pd.Series(values).dropna().unique()
    if len(vals) and all(isinstance(v, (int, float, np.integer, np.floating)) for v in vals):
        return sorted(vals)
    return sorted(vals, key=r_sort_key)


def level_order(series):
    """Sort key for a column: categorical code order if categorical, else R factor order."""
    if isinstance(series.dtype, pd.CategoricalDtype):
        return list(series.cat.categories)
    return sorted_levels(series)


def safe_name(value):
    return str(value)


##########################
# Taxonomy helpers
##########################


def _blank(value, prefix):
    return value is None or (isinstance(value, float) and np.isnan(value)) or str(value).replace(prefix, "") == ""


def generate_taxon(Kingdom, Phylum, Class, Order, Family, Genus, Species):
    """Concise taxon label: deepest named rank (e.g. 'Blautia obeum', 'f: Lachnospiraceae')."""
    if _blank(Genus, "g__"):
        if _blank(Family, "f__"):
            if _blank(Order, "o__"):
                if _blank(Class, "c__"):
                    if _blank(Phylum, "p__"):
                        return "k: " + str(Kingdom).replace("k__", "")
                    return "p: " + str(Phylum).replace("p__", "")
                return "c: " + str(Class).replace("c__", "")
            return "o: " + str(Order).replace("o__", "")
        return "f: " + str(Family).replace("f__", "")
    if _blank(Species, "s__"):
        return str(Genus).replace("g__", "") + " sp."
    return str(Genus).replace("g__", "") + " " + str(Species).replace("s__", "")


def r_paste(*cols):
    """paste(..., sep = ';') where NA becomes the string 'NA'."""
    parts = [c.astype(object).where(c.notna(), "NA").astype(str) for c in cols]
    out = parts[0]
    for p in parts[1:]:
        out = out + ";" + p
    return out


##########################
# Phylogenetic tree + UniFrac
##########################


class Tree:
    """Unrooted Newick tree stored as an undirected graph, so it can be re-rooted anywhere."""

    def __init__(self, newick: str):
        self.adj: list[list[tuple[int, float]]] = []
        self.tip_node: dict[str, int] = {}
        self.tip_labels: list[str] = []  # tips in Newick order (= ape's tip.label order)
        self._parse(newick.strip())

    def _new_node(self):
        self.adj.append([])
        return len(self.adj) - 1

    def _parse(self, s):
        root = self._new_node()
        stack, cur, i, n = [], root, 0, len(s)
        pending = None  # node whose label/length is being read
        while i < n:
            ch = s[i]
            if ch == "(":
                child = self._new_node()
                stack.append(cur)
                self._link(cur, child, 0.0)
                cur = child
                pending = None
                i += 1
            elif ch == ",":
                parent = stack[-1]
                child = self._new_node()
                self._link(parent, child, 0.0)
                cur = child
                pending = None
                i += 1
            elif ch == ")":
                cur = stack.pop()
                pending = cur
                i += 1
            elif ch == ";":
                break
            else:
                j = i
                while j < n and s[j] not in ",():;":
                    j += 1
                label = s[i:j]
                if label and pending is None:  # a tip name
                    self.tip_node[label] = cur
                    self.tip_labels.append(label)
                i = j
                if i < n and s[i] == ":":
                    j = i + 1
                    while j < n and s[j] not in ",();":
                        j += 1
                    self._set_length(cur, float(s[i + 1:j]))
                    i = j
        self.root = root

    def _link(self, a, b, length):
        self.adj[a].append((b, length))
        self.adj[b].append((a, length))

    def _set_length(self, node, length):
        # A node's branch length is stored on the edge to the node it was created from.
        parent = self.adj[node][0][0]
        self.adj[node][0] = (parent, length)
        self.adj[parent] = [(c, length if c == node else l) for c, l in self.adj[parent]]

    def rooted_at(self, root):
        """Parent array, branch lengths and a root-first node order for a given root node."""
        n = len(self.adj)
        parent = np.full(n, -1)
        length = np.zeros(n)
        order = [root]
        seen = np.zeros(n, bool)
        seen[root] = True
        k = 0
        while k < len(order):
            v = order[k]
            for w, l in self.adj[v]:
                if not seen[w]:
                    seen[w] = True
                    parent[w] = v
                    length[w] = l
                    order.append(w)
            k += 1
        return parent, length, np.array(order)

    def phyloseq_root(self, taxa, outgroup):
        """Root used by phyloseq for an unrooted tree.

        phyloseq::UniFrac calls ape::root(tree, outgroup = <random taxon>, resolve.root = TRUE)
        on the tree pruned to the object's taxa. That puts the root at the most recent common
        ancestor of all *other* taxa. Here we find that node on the full tree.
        """
        t = self.tip_node[outgroup]
        others = np.array([self.tip_node[x] for x in taxa if x != outgroup])
        other_set = set(others.tolist())
        # Hang the tree from the outgroup tip and count the other taxa below each node.
        parent, _, order = self.rooted_at(t)
        count = np.zeros(len(self.adj), int)
        count[others] = 1
        for v in order[::-1][:-1]:
            count[parent[v]] += count[v]
        # Walk down from the outgroup's neighbour while every other taxon sits under one child.
        node = self.adj[t][0][0]
        while node not in other_set:
            children = [w for w, _ in self.adj[node] if w != parent[node] and count[w] > 0]
            if len(children) != 1:
                break
            node = children[0]
        return node


def unifrac(otu: pd.DataFrame, tree: Tree, weighted: bool, rng: np.random.Generator | None = None,
            outgroup: str | None = None):
    """UniFrac distances as computed by phyloseq::UniFrac (normalized = TRUE for weighted).

    otu: samples x taxa counts. All taxa in ``otu`` are the object's taxa (the tree is
    implicitly pruned to them). Unless ``outgroup`` is given, a random taxon is drawn as
    outgroup, as phyloseq does for unrooted trees, so values depend on ``rng``.
    """
    taxa = list(otu.columns)
    if outgroup is None:
        outgroup = taxa[rng.integers(len(taxa))]
    root = tree.phyloseq_root(taxa, outgroup)
    parent, length, order = tree.rooted_at(root)

    prop = otu.to_numpy(float)
    prop = prop / prop.sum(axis=1, keepdims=True)
    tips = np.array([tree.tip_node[x] for x in taxa])

    # Abundance below every node: start at the tips, then add each node into its parent.
    below = np.zeros((len(parent), prop.shape[0]))
    below[tips] = prop.T
    for v in order[::-1][:-1]:
        below[parent[v]] += below[v]

    edges = order[1:]  # every node except the root owns the branch above it
    b = length[edges]
    E = below[edges]  # edges x samples
    keep = E.sum(axis=1) > 0
    b, E = b[keep], E[keep]

    if weighted:
        num = cdist(E.T * b, E.T * b, "cityblock")
        depth = np.zeros(len(parent))
        for v in order[1:]:
            depth[v] = depth[parent[v]] + length[v]
        tip_depth = (prop * depth[tips]).sum(axis=1)
        D = num / (tip_depth[:, None] + tip_depth[None, :])
    else:
        P = (E > 0).astype(float)
        s = (P * b[:, None]).sum(axis=0)
        shared = (P * b[:, None]).T @ P
        union = s[:, None] + s[None, :] - shared
        D = (union - shared) / union
    np.fill_diagonal(D, 0.0)
    return pd.DataFrame(D, index=otu.index, columns=otu.index)


##########################
# phyloseq-like container
##########################


@dataclass
class PS:
    """Minimal phyloseq replacement: counts (samples x taxa), taxonomy, sample data, tree."""

    otu: pd.DataFrame
    tax: pd.DataFrame
    sam: pd.DataFrame
    tree: Tree | None = None
    meta: dict = field(default_factory=dict)

    # --- phyloseq verbs -------------------------------------------------
    def subset_samples(self, mask) -> "PS":
        """subset_samples(): keep samples where mask is True (NA counts as False)."""
        mask = pd.Series(mask, index=self.sam.index).fillna(False).astype(bool)
        keep = self.sam.index[mask]
        return PS(self.otu.loc[keep], self.tax, self.sam.loc[keep], self.tree)

    def prune_taxa(self, taxa) -> "PS":
        """prune_taxa(): keep the given taxa, in the object's original order."""
        taxa = set(taxa)
        cols = [c for c in self.otu.columns if c in taxa]
        return PS(self.otu[cols], self.tax.loc[cols], self.sam, self.tree)

    def transform_sample_counts(self, fun) -> "PS":
        """transform_sample_counts(): apply fun to each sample's vector of counts."""
        vals = np.vstack([fun(row) for row in self.otu.to_numpy(float)]) if len(self.otu) \
            else self.otu.to_numpy(float)
        return PS(pd.DataFrame(vals, index=self.otu.index, columns=self.otu.columns),
                  self.tax, self.sam, self.tree)

    def relative(self) -> "PS":
        """transform_sample_counts(function(x) x / sum(x))."""
        with np.errstate(invalid="ignore", divide="ignore"):  # 0-read samples give NaN, as in R
            return self.transform_sample_counts(lambda x: x / x.sum())

    def sample_sums(self) -> pd.Series:
        return self.otu.sum(axis=1)

    def nsamples(self) -> int:
        return len(self.otu)

    def taxa_above(self, cutoff) -> list:
        """Taxa whose value exceeds cutoff in at least one sample (psmelt %>% filter(Abundance > cutoff))."""
        return list(self.otu.columns[(self.otu > cutoff).any(axis=0)])

    def psmelt(self) -> pd.DataFrame:
        """psmelt(): long table with OTU, Sample, Abundance + sample and taxonomy columns."""
        long = self.otu.rename_axis(index="Sample", columns="OTU").stack(future_stack=True)
        long = long.rename("Abundance").reset_index()
        long = long.merge(self.sam, left_on="Sample", right_index=True, how="left")
        long = long.merge(self.tax, left_on="OTU", right_index=True, how="left")
        return long.sort_values("Abundance", ascending=False, kind="stable").reset_index(drop=True)


RANK_COLS = ["Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]
TAX_COLS = RANK_COLS + ["fOTU", "Taxon", "Family2", "Color", "Feature"]


def _read_colors(sheet):
    """Custom colours from Family_colors.xlsx (sheet index as in R: 1 = SILVA, 3 = Meat, 4 = Plants)."""
    colors = read_excel_like_readxl(DATA_DIR / "Family_colors.xlsx", sheet_name=sheet - 1)
    hexes = colors["Color"].map(r_num_str)
    colors["Color"] = ("#" + hexes.str.zfill(6)).where(hexes.notna(), np.nan)
    return colors


def _order_by(values, reference):
    """arrange(match(values, reference)): stable sort by first position in reference, unmatched last.

    Like R's match(), NA matches the first NA in reference.
    """
    key = lambda v: "\0NA" if pd.isna(v) else v  # noqa: E731
    first = {}
    for i, v in enumerate(reference):
        first.setdefault(key(v), i)
    return pd.Series([first.get(key(v), np.nan) for v in values], index=getattr(values, "index", None))


def _lineage_taxa(directory, colors):
    """Taxonomy annotated by full lineage (setup_tables / setup_tables_meat)."""
    colors["fOTU"] = r_paste(*(colors[c] for c in ["Kingdom", "Phylum", "Class", "Order", "Family"]))
    assert colors["fOTU"].is_unique, "duplicate fOTU in Family_colors.xlsx would duplicate taxa"
    taxa = pd.read_csv(directory / "feature_data.txt", sep="\t")
    taxa["fOTU"] = r_paste(*(taxa[c] for c in RANK_COLS[:5]))  # add fOTU
    taxa["Taxon"] = [generate_taxon(*row) for row in taxa[RANK_COLS].itertuples(index=False)]
    fam_blank = taxa["Family"].isna() | (taxa["Family"] == "f__")
    taxa["Family2"] = np.where(fam_blank, taxa["Taxon"], taxa["Family"])  # add Family2 name to plot
    taxa = taxa.merge(colors[["fOTU", "Color"]], on="fOTU", how="left")  # add Family colors
    # taxa_order: taxa arranged in the row order of the colour sheet (unmatched last)
    pos = _order_by(taxa["fOTU"], colors["fOTU"])
    taxa_order = taxa.assign(_pos=pos).sort_values("_pos", kind="stable", na_position="last").drop(columns="_pos")
    return taxa, taxa_order


def _build_ps(directory, taxa, sample_sheet_path):
    """Read counts, tree and sample sheet, and assemble the phyloseq-like object."""
    # ASV read counts (samples x sequences) saved from R with saveRDS
    rds = [p for p in directory.iterdir() if p.name.lower() == "seqtab_all.rds"][0]
    seqtab = pyreadr.read_r(str(rds))[None]
    tree = Tree((directory / "dsvs_msa.tree").read_text())

    samdf = read_excel_like_readxl(sample_sheet_path, sheet_name=0)
    samdf.index = samdf["Sample"].str.replace("sample_", "", n=1)
    samdf = samdf.iloc[:, 1:]

    # phyloseq() keeps taxa/samples shared by every component. Taxa end up in the tree's
    # tip order (not the count-table order), so the new feature_%04d names (the OTU column)
    # differ from the Feature column of feature_data.txt, exactly as in R.
    in_both = set(seqtab.columns) & set(taxa["Sequence"])
    shared_taxa = [s for s in tree.tip_labels if s in in_both]
    shared_samples = [s for s in seqtab.index if s in samdf.index]
    otu = seqtab.loc[shared_samples, shared_taxa].astype(float)

    # rename taxa to short names, as R does with sprintf("feature_%04d", ...)
    names = [f"feature_{i + 1:04d}" for i in range(len(shared_taxa))]
    seq2name = dict(zip(shared_taxa, names))
    tree.tip_node = {seq2name[s]: node for s, node in tree.tip_node.items() if s in seq2name}
    tree.tip_labels = [seq2name[s] for s in tree.tip_labels if s in seq2name]
    otu.columns = names
    tax = taxa.set_index("Sequence").loc[shared_taxa]
    tax.index = names
    tax = tax[TAX_COLS]
    return PS(otu, tax, samdf.loc[shared_samples], tree), samdf


def setup_tables(directory: Path, sample_sheet_path: Path):
    """Build the phyloseq-like object (R: setup_tables in 0-config.R; SILVA family colours).

    Returns (ps, taxa_order, samdf) where samdf still contains samples that have no
    sequencing data (phyloseq drops those from ps, but the R code keeps output$samdf).
    """
    taxa, taxa_order = _lineage_taxa(directory, _read_colors(1))
    ps, samdf = _build_ps(directory, taxa, sample_sheet_path)
    return ps, taxa_order, samdf


def setup_tables_meat(directory: Path, sample_sheet_path: Path):
    """R: setup_tables_meat. Same as setup_tables but with the 'Meat' colour sheet."""
    taxa, taxa_order = _lineage_taxa(directory, _read_colors(3))
    ps, samdf = _build_ps(directory, taxa, sample_sheet_path)
    return ps, taxa_order, samdf


def setup_tables_plants(directory: Path, sample_sheet_path: Path):
    """R: setup_tables_plants. Plants are coloured and labelled by genus.

    Family2 is the genus ("NA" if missing); Taxon and fOTU are the genus' common name
    from the 'Plants' colour sheet (missing if the genus is not in the sheet).
    """
    colors = _read_colors(4)
    taxa = pd.read_csv(directory / "feature_data.txt", sep="\t")
    taxa["Genus"] = taxa["Genus"].fillna("NA")
    taxa["Family2"] = taxa["Genus"]  # add Family2 name to plot
    taxa = taxa.merge(colors[["Genus", "Common_name", "Color"]], on="Genus", how="left")  # add colors
    taxa["Taxon"] = taxa["Common_name"]
    taxa["fOTU"] = taxa["Common_name"]
    pos = _order_by(taxa["Genus"], colors["Genus"])  # arrange taxa in the colour sheet's genus order
    taxa_order = taxa.assign(_pos=pos).sort_values("_pos", kind="stable", na_position="last").drop(columns="_pos")
    ps, samdf = _build_ps(directory, taxa, sample_sheet_path)
    return ps, taxa_order, samdf


def set_family_order(df2plot, taxa_order):
    """Order rows by family (colour sheet order) and make Family2 an ordered factor."""
    df2plot = df2plot.assign(_pos=_order_by(df2plot["fOTU"], taxa_order["fOTU"]).to_numpy())
    df2plot = df2plot.sort_values("_pos", kind="stable", na_position="last").drop(columns="_pos")
    levels = list(dict.fromkeys(taxa_order["Family2"]))
    df2plot["Family2"] = pd.Categorical(df2plot["Family2"].astype(object), categories=levels)
    return df2plot.reset_index(drop=True)


def get_color_mapping(df2plot):
    """Family2 -> colour mapping in Family2 order (R: get_color_mapping)."""
    scale = df2plot[["Color", "Family2"]].drop_duplicates()
    for fam in scale.loc[scale["Color"].isna(), "Family2"]:
        print(f"Missing Family color:  {fam}")
    scale = scale.drop_duplicates("Family2")
    return pd.DataFrame({
        "values": scale["Color"].fillna(GREY50).to_numpy(),
        "breaks": scale["Family2"].astype(object).to_numpy(),
        "labels": scale["Family2"].astype(str).str.replace("f__", "", regex=False).to_numpy(),
    })


##########################
# Diversity, distances, ordination
##########################


def estimate_richness(otu: pd.DataFrame):
    """phyloseq::estimate_richness for Observed, Shannon (natural log) and Simpson."""
    x = otu.to_numpy(float)
    p = x / x.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        shannon = -np.nansum(np.where(p > 0, p * np.log(p), 0.0), axis=1)
    return pd.DataFrame({
        "Observed": (x > 0).sum(axis=1),
        "Shannon": shannon,
        "Simpson": 1 - (p ** 2).sum(axis=1),
    }, index=otu.index)


def distance(ps: PS, method: str, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """phyloseq::distance for the metrics used in the notebook."""
    otu = ps.otu
    if method in ("unifrac", "wunifrac"):
        rng = rng if rng is not None else np.random.default_rng()
        return unifrac(otu, ps.tree, weighted=(method == "wunifrac"), rng=rng)
    x = otu.loc[:, (otu > 0).any(axis=0)].to_numpy(float)
    if method == "bray":  # vegan::vegdist(method = "bray")
        D = cdist(x, x, "cityblock") / (x.sum(1)[:, None] + x.sum(1)[None, :])
    elif method == "canberra":  # vegan's Canberra: divided by number of non-double-zero taxa
        pres = (x > 0).astype(float)
        nz = pres.sum(1)[:, None] + pres.sum(1)[None, :] - pres @ pres.T
        D = cdist(x, x, "canberra") / nz
    elif method == "binary":  # stats::dist(method = "binary") == Jaccard on presence/absence
        D = cdist(x > 0, x > 0, "jaccard")
    else:
        raise ValueError(method)
    np.fill_diagonal(D, 0.0)
    return pd.DataFrame(D, index=otu.index, columns=otu.index)


def pcoa(D: pd.DataFrame):
    """ape::pcoa (no correction), as used by phyloseq::ordinate(method = 'MDS').

    Returns (vectors, eigenvalues). vectors has columns Axis.1, Axis.2, ...; eigenvalues
    are the 'Eigenvalues' column of pcoa_out$values (all n values when some are negative).
    """
    d = D.to_numpy()
    n = d.shape[0]
    A = -0.5 * d ** 2
    J = np.eye(n) - np.ones((n, n)) / n
    G = J @ A @ J
    vals, vecs = np.linalg.eigh(G)
    idx = np.argsort(vals)[::-1]
    vals, vecs = vals[idx], vecs[:, idx]
    eps = np.sqrt(np.finfo(float).eps)
    vals[np.abs(vals) < eps] = 0
    pos = vals > eps
    vectors = vecs[:, pos] * np.sqrt(vals[pos])
    evals = vals if vals.min() < -eps else vals[pos]
    cols = [f"Axis.{i + 1}" for i in range(vectors.shape[1])]
    return pd.DataFrame(vectors, index=D.index, columns=cols), evals


def get_evals(evals):
    """Percent variance explained by each axis (R: get_evals)."""
    return 100 * evals / evals.sum()


def clr(x):
    """compositions::clr applied to each row (sample)."""
    lx = np.log(x)
    return lx - lx.mean(axis=1, keepdims=True)


def rcorr(x):
    """Hmisc::rcorr Pearson correlations between columns, with two-sided p-values."""
    from scipy import stats

    n = x.shape[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.corrcoef(x, rowvar=False)
        t = r * np.sqrt((n - 2) / (1 - r ** 2))
        p = 2 * stats.t.sf(np.abs(t), n - 2)
    np.fill_diagonal(p, np.nan)
    return r, p


def p_adjust_fdr(p):
    """p.adjust(p, 'fdr') (Benjamini-Hochberg); NA values are ignored."""
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)[::-1]
    ranks = np.arange(m, 0, -1)
    adj = np.minimum.accumulate(pv[order] * m / ranks)
    res = np.empty(m)
    res[order] = np.minimum(adj, 1)
    out[ok] = res
    return out


def fdr_matrix(pmat):
    """FDR-adjust the upper triangle of a symmetric p-value matrix and mirror it."""
    n = pmat.shape[0]
    iu = np.triu_indices(n, 1)
    # R takes pmat[upper.tri(pmat)] in column-major order; BH does not depend on order
    padj = p_adjust_fdr(pmat[iu])
    out = np.full((n, n), np.nan)
    out[iu] = padj
    out[(iu[1], iu[0])] = padj
    return out


##########################
# Colours
##########################


def hcl_to_hex(h, c, l):
    """grDevices::hcl (polar CIE-LUV, D65 white) -> sRGB hex, clipped like fixup = TRUE."""
    xn, yn, zn = 95.047, 100.000, 108.883
    un = 4 * xn / (xn + 15 * yn + 3 * zn)
    vn = 9 * yn / (xn + 15 * yn + 3 * zn)
    hr = np.deg2rad(h)
    u, v = c * np.cos(hr), c * np.sin(hr)
    y = yn * (((l + 16) / 116) ** 3 if l > 8 else l / 903.3)
    uu, vv = u / (13 * l) + un, v / (13 * l) + vn
    x = 9.0 * y * uu / (4 * vv)
    z = -x / 3 - 5 * y + 3 * y / vv
    rgb = np.array([[3.240479, -1.537150, -0.498535],
                    [-0.969256, 1.875992, 0.041556],
                    [0.055648, -0.204043, 1.057311]]) @ (np.array([x, y, z]) / 100)
    rgb = np.where(rgb > 0.00304, 1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055, 12.92 * rgb)
    rgb = np.clip(rgb, 0, 1)
    return "#" + "".join(f"{int(round(v * 255)):02X}" for v in rgb)


def hue_pal(n, h=(15, 375), c=100, l=65):
    """scales::hue_pal()(n): ggplot2's default discrete colours."""
    if n == 0:
        return []
    if (h[1] - h[0]) % 360 < 1:
        h = (h[0], h[1] - 360 / n)
    hues = np.linspace(h[0], h[1], n)
    return [hcl_to_hex(hh % 360, c, l) for hh in hues]


def default_palette(levels):
    """Named default ggplot colours for the given factor levels."""
    return dict(zip(levels, hue_pal(len(levels))))


GRADIENT_WHITE_BLUE = LinearSegmentedColormap.from_list("white_blue", ["#FFFFFF", "#0000FF"])

##########################
# Plot styling (theme_grey + theme_custom_text)
##########################

PT_PER_MM = 72.27 / 25.4

plt.rcParams.update({
    "pdf.fonttype": 42,  # editable text in Illustrator
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 6,
    "axes.titlesize": 6,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "legend.fontsize": 6,
    "legend.title_fontsize": 6,
    "xtick.major.width": 0.25,
    "ytick.major.width": 0.25,
    "xtick.major.size": 2,
    "ytick.major.size": 2,
    "axes.titlelocation": "left",
    "legend.frameon": False,
})


def theme_grey(ax, grid=True):
    """ggplot2 default look: grey panel, white grid, no axis lines."""
    ax.set_facecolor("#EBEBEB")
    for s in ax.spines.values():
        s.set_visible(False)
    if grid:
        from matplotlib.ticker import AutoMinorLocator
        ax.grid(True, which="major", color="white", linewidth=0.5)
        ax.grid(True, which="minor", color="white", linewidth=0.25)
        ax.set_axisbelow(True)
        for axis in (ax.xaxis, ax.yaxis):
            if axis.get_scale() == "linear":
                axis.set_minor_locator(AutoMinorLocator(2))
        ax.tick_params(which="minor", length=0)


def theme_blank(ax):
    """panel.background = element_blank()"""
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)


def strip(ax, text, side="top", fontsize=6):
    """Grey facet strip label above (or right of) an axes."""
    if side == "top":
        ax.text(0.5, 1.0, str(text), transform=ax.transAxes, ha="center", va="bottom", fontsize=fontsize,
                bbox=dict(boxstyle="square,pad=0.3", fc="#D9D9D9", ec="none"))
    else:
        ax.text(1.02, 0.5, str(text), transform=ax.transAxes, ha="left", va="center", rotation=-90,
                fontsize=fontsize, bbox=dict(boxstyle="square,pad=0.3", fc="#D9D9D9", ec="none"))


def legend_patches(ax_or_fig, mapping, title=None, ncol=1, fontsize=6, loc="center left",
                   bbox=(1.02, 0.5), handlesize=0.8, **kw):
    handles = [Patch(facecolor=c, edgecolor="black", linewidth=0.2, label=str(k)) for k, c in mapping.items()]
    return ax_or_fig.legend(handles=handles, title=title, ncol=ncol, fontsize=fontsize, loc=loc,
                            bbox_to_anchor=bbox, handlelength=handlesize, handleheight=handlesize,
                            title_fontsize=fontsize, frameon=False, **kw)


def save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


##########################
# Plot building blocks
##########################


def gg_bins(values, bins=25, xlim_low=None):
    """Bin edges that match ggplot2's stat_bin(bins = n).

    ggplot centres the first bin on the lower end of the range; with
    scale_x_continuous(limits = c(0, NA)) the range starts at 0, and any bar extending
    below 0 is removed (ggplot warns "Removed rows containing missing values").
    Returns (edges, drop_first).
    """
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    lo = xlim_low if xlim_low is not None else v.min()
    hi = v.max()
    if hi == lo:
        width = 0.1
    else:
        width = (hi - lo) / (bins - 1)
    boundary = width / 2
    shift = np.floor((lo - boundary) / width)
    origin = boundary + shift * width
    edges = np.arange(origin, hi + (1 - 1e-8) * width + width * 1e-9, width)
    if edges[-1] < hi:
        edges = np.append(edges, edges[-1] + width)
    drop_first = xlim_low is not None and edges[0] < xlim_low
    return edges, drop_first


def stacked_hist(ax, df, x, fill, edges, palette, levels=None, drop_first=False, lw=0.2):
    """geom_histogram(aes(fill = ...), color = 'black'): stacked counts per bin.

    ggplot stacks the first fill level on top, so we draw from the last level upwards.
    """
    d = df[np.isfinite(df[x].astype(float))]
    levels = levels if levels is not None else level_order(d[fill])
    groups = list(levels) + ([np.nan] if d[fill].isna().any() else [])
    bottom = np.zeros(len(edges) - 1)
    for lev in groups[::-1]:
        vals = d.loc[d[fill].isna() if pd.isna(lev) else d[fill] == lev, x].astype(float)
        counts, _ = np.histogram(vals, bins=edges)
        if drop_first:
            counts[0] = 0
        if counts.sum() == 0:
            continue
        color = GREY50 if pd.isna(lev) else palette.get(lev, GREY50)
        ax.bar(edges[:-1], counts, width=np.diff(edges), bottom=bottom, align="edge", color=color,
               edgecolor="black", linewidth=lw, label=("NA" if pd.isna(lev) else str(lev)))
        bottom += counts
    present = [lev for lev in groups if (d[fill].isna().any() if pd.isna(lev) else (d[fill] == lev).any())]
    return {("NA" if pd.isna(lev) else lev): (GREY50 if pd.isna(lev) else palette.get(lev, GREY50))
            for lev in present}


def facet_layout(n, ncol=None):
    """ggplot2::wrap_dims"""
    if ncol is None:
        ncol = int(np.ceil(np.sqrt(n)))
    nrow = int(np.ceil(n / ncol))
    return nrow, ncol


def nested_panels(df, facet_cols):
    """Panels for facet_nested(cols = vars(...)): sorted tuples of facet values (NA last)."""
    keys = df[facet_cols].astype(object).drop_duplicates()
    sorters = []
    for c in facet_cols:
        lv = level_order(df[c])
        rank = {v: i for i, v in enumerate(lv)}
        sorters.append(lambda v, rank=rank: (1, 0) if pd.isna(v) else (0, rank.get(v, len(rank))))
    tuples = [tuple(r) for r in keys.itertuples(index=False)]
    return sorted(tuples, key=lambda t: [s(v) for s, v in zip(sorters, t)])


def fmt_facet(v):
    if pd.isna(v):
        return "NA"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _same(a, b):
    """Tuple equality where NA equals NA (facet values)."""
    return all((pd.isna(x) and pd.isna(y)) or x == y for x, y in zip(a, b))


def draw_nested_strips(fig, ax, panels, spans, y0, strip_h, gap):
    """Draw facet_nested strips: one row per facet level, merging adjacent panels with the same parent."""
    nlev = len(panels[0]) if panels else 0
    for lev in range(nlev):
        i = 0
        while i < len(panels):
            j = i
            while j + 1 < len(panels) and _same(panels[j + 1][:lev + 1], panels[i][:lev + 1]):
                j += 1
            x0, x1 = spans[i][0], spans[j][1]
            yb = y0 + (nlev - 1 - lev) * strip_h
            ax.add_patch(Rectangle((x0, yb), x1 - x0, strip_h * 0.92, transform=ax.get_xaxis_transform(),
                                   clip_on=False, facecolor="#D9D9D9", edgecolor="none"))
            ax.text((x0 + x1) / 2, yb + strip_h * 0.46, fmt_facet(panels[i][lev]),
                    transform=ax.get_xaxis_transform(), ha="center", va="center", fontsize=6, clip_on=False)
            i = j + 1


def r_interaction_order(df, cols):
    """Order of interaction(a, b, c) levels: the LAST factor varies slowest.

    As in R, a row with NA in any component gets the NA level, which sorts last.
    """
    any_na = df[cols].isna().any(axis=1).to_numpy()
    keys = []
    for c in cols:
        rank = {v: i for i, v in enumerate(level_order(df[c]))}
        k = df[c].map(lambda v, rank=rank: len(rank) if pd.isna(v) else rank.get(v, len(rank))).to_numpy()
        keys.append(np.where(any_na, 0, k))
    return np.lexsort(keys + [any_na])  # np.lexsort treats the last key as the primary sort key


def interaction_labels(df, cols):
    """Labels 'a.b.c' of interaction(a, b, c); 'NA' if any component is missing."""
    any_na = df[cols].isna().any(axis=1)
    labels = df[cols].astype(object).apply(lambda r: ".".join(fmt_facet(v) for v in r), axis=1)
    return labels.where(~any_na, "NA")


##########################
# ggplot-like figures
##########################

MARKERS = {21: "o", 22: "s", 23: "D", 24: "^"}
REGION_SHAPES = {"R1": 21, "R2": 22, "R3": 23, "R4": 24, "Saliva": 21, "Stool": 21}


def _panel_grid(panels, nrow, ncol, figsize, panel_w=None, panel_h=None, left=0.6, right=1.4,
                top=0.45, bottom=0.45, wspace=0.08, hspace=0.25, sharex=True, sharey=True):
    """Create a fig with an nrow x ncol grid of axes (inch-based margins)."""
    fig = plt.figure(figsize=figsize)
    W, H = figsize
    avail_w = W - left - right - wspace * (ncol - 1)
    avail_h = H - top - bottom - hspace * (nrow - 1)
    pw = panel_w if panel_w else avail_w / ncol
    ph = panel_h if panel_h else avail_h / nrow
    axes = {}
    first = None
    for k, key in enumerate(panels):
        r, c = divmod(k, ncol)
        x0 = left + c * (pw + wspace)
        y0 = H - top - (r + 1) * ph - r * hspace
        ax = fig.add_axes([x0 / W, y0 / H, pw / W, ph / H],
                          sharex=first if sharex else None, sharey=first if sharey else None)
        first = first or ax
        axes[key] = ax
    return fig, axes


def histogram(df, x, fill, palette, path, figsize, xlabel, ylabel="Counts", title=None, subtitle=None,
              levels=None, bins=25, xlim_low=None, xbreaks=None, aspect=None,
              wrap=None, ncol=None, rows=None, cols=None, legend_title=None, key_cm=0.3,
              legend_fontsize=6, vlines=None):
    """geom_histogram(bins = 25, aes(fill = ...), colour = 'black') with optional facets.

    wrap: column for facet_wrap; rows/cols: columns for facet_grid.
    vlines: dict panel_key -> x value for a red dashed mean line with 'Avg: ...' label.
    """
    d = df.copy()
    d[x] = d[x].astype(float)
    finite = d[np.isfinite(d[x])]
    if xlim_low is not None:
        finite = finite[finite[x] >= xlim_low]
    edges, drop_first = gg_bins(finite[x], bins, xlim_low)
    levels = levels if levels is not None else level_order(finite[fill])

    if wrap:
        keys = level_order(finite[wrap]) + ([np.nan] if finite[wrap].isna().any() else [])  # NA panel last
        nrow, ncol_ = facet_layout(len(keys), ncol)
        panels = [(k,) for k in keys]
        selector = {(k,): (finite[wrap].isna() if pd.isna(k) else finite[wrap] == k) for k in keys}
    elif rows or cols:
        rkeys = level_order(finite[rows]) if rows else [None]
        ckeys = level_order(finite[cols]) if cols else [None]
        nrow, ncol_ = len(rkeys), len(ckeys)
        panels = [(r, c) for r in rkeys for c in ckeys]
        selector = {(r, c): (finite[rows] == r if rows else True) & (finite[cols] == c if cols else True)
                    for r, c in panels}
    else:
        nrow = ncol_ = 1
        panels = [()]
        selector = {(): pd.Series(True, index=finite.index)}

    top = 0.08 + (0.14 if title else 0) + (0.14 if subtitle else 0) + (0.17 if (wrap or cols) else 0)
    fig, axes = _panel_grid(panels, nrow, ncol_, figsize, left=0.45, right=0.8 + (0.2 if rows else 0), top=top,
                            bottom=0.42, wspace=0.06, hspace=0.25 if wrap else 0.06)
    shown = {}
    for key in panels:
        ax = axes[key]
        theme_grey(ax)
        sel = finite[selector[key]] if not isinstance(selector[key], bool) else finite
        shown.update(stacked_hist(ax, sel, x, fill, edges, palette, levels, drop_first))
        if aspect:
            ax.set_box_aspect(aspect)
        if wrap:
            strip(ax, fmt_facet(key[0]))
        if cols and key[0] == panels[0][0]:
            strip(ax, key[1])
        if rows and key[1] == panels[ncol_ - 1][1]:
            strip(ax, key[0], side="right")
        if vlines is not None and key in vlines:
            m = vlines[key]
            ax.axvline(m, color="red", linestyle="--", linewidth=0.2)
            ax.text(m, 0.97, f"  Avg: {m:.2f}", transform=ax.get_xaxis_transform(), color="red",
                    fontsize=5.7, ha="left", va="top")
    for k, key in enumerate(panels):
        ax = axes[key]
        r, c = divmod(k, ncol_)
        if xbreaks is not None:
            ax.set_xticks(xbreaks)
        lo = edges[1] if drop_first else edges[0]
        ax.set_xlim(min(lo, xlim_low if xlim_low is not None else lo) - 0.045 * (edges[-1] - lo),
                    edges[-1] + 0.045 * (edges[-1] - lo))
        last_row = (r == nrow - 1) or (k + ncol_ >= len(panels))
        if not last_row:
            ax.tick_params(labelbottom=False)
        if c != 0:
            ax.tick_params(labelleft=False)
    from matplotlib.ticker import MaxNLocator
    ymax = max(ax.get_ylim()[1] for ax in axes.values())
    for ax in axes.values():
        ax.set_ylim(-0.045 * ymax, ymax)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10], integer=True))
    # axis titles hug the (aspect-adjusted) panel block, as in ggplot
    for ax in axes.values():
        ax.apply_aspect()
    boxes = [ax.get_position() for ax in axes.values()]
    x0, x1 = min(b.x0 for b in boxes), max(b.x1 for b in boxes)
    y0, y1 = min(b.y0 for b in boxes), max(b.y1 for b in boxes)
    fig.text((x0 + x1) / 2, y0 - 0.17 / figsize[1], xlabel, ha="center", va="top", fontsize=7)
    fig.text(x0 - 0.27 / figsize[0], (y0 + y1) / 2, ylabel, ha="right", va="center", rotation=90, fontsize=7)
    strip_pad = 0.17 / figsize[1] if (wrap or cols) else 0
    if subtitle:
        fig.text(x0, y1 + strip_pad + 0.06 / figsize[1], subtitle, fontsize=6, va="bottom")
    if title:
        fig.text(x0, y1 + strip_pad + (0.2 if subtitle else 0.06) / figsize[1], title, fontsize=6, va="bottom")
    if fill and shown:
        ordered = {k: shown[k] for k in list(levels) + ["NA"] if k in shown}
        fig.legend(handles=[Patch(facecolor=c, edgecolor="none", label=str(k)) for k, c in ordered.items()],
                   title=legend_title or fill, loc="center left", bbox_to_anchor=(1 - 0.85 / figsize[0], 0.5),
                   fontsize=legend_fontsize, title_fontsize=6, handlelength=key_cm / 0.35 * 0.8,
                   handleheight=key_cm / 0.35 * 0.8, frameon=False)
    save(fig, path)


def composition_plot(df, x_cols, facet_cols, scale, path, width, height, label_fn,
                     wrap=None, bar_lw=0.25, hide_y_text=False):
    """Stacked relative-abundance bars (geom_bar(position = 'stack')) per x category.

    Nested facets (facet_nested(cols = vars(...), scales = 'free', space = 'free')) are drawn
    on a single axis with merged strips; ``wrap`` gives facet_wrap(vars(wrap), scales = 'free').
    label_fn(label) -> (text, colour) formats x tick labels (red when < 10k reads).
    """
    colours = dict(zip(scale["breaks"], scale["values"]))
    fam_levels = list(df["Family2"].cat.categories)
    fam_rank = {f: i for i, f in enumerate(fam_levels)}

    def draw_bars(ax, d, x0):
        """Draw bars for d at positions x0, x0+1, ...; return positions and labels."""
        order = r_interaction_order(d, x_cols)
        keys = interaction_labels(d, x_cols)
        cats = list(dict.fromkeys(keys.iloc[order]))
        pos = {k: x0 + i for i, k in enumerate(cats)}
        xs, hs, bs, cs = [], [], [], []
        for k in cats:
            rows = d[keys == k]
            rows = rows[rows["Abundance"] > 0]
            # ggplot puts the first factor level on top: draw from the last level upwards;
            # within one level, rows stack in data order (most abundant ASV lowest)
            rank = rows["Family2"].map(lambda f: fam_rank.get(f, len(fam_rank))).to_numpy()
            idx = np.lexsort((np.arange(len(rows)), -rank))
            bottom = 0.0
            for (_, r) in rows.iloc[idx].iterrows():
                xs.append(pos[k]); hs.append(r["Abundance"]); bs.append(bottom)
                cs.append(colours.get(r["Family2"], GREY50))
                bottom += r["Abundance"]
        if xs:
            ax.bar(xs, hs, bottom=bs, width=0.9, color=cs, edgecolor="black", linewidth=bar_lw)
        return [pos[k] for k in cats], cats

    def style_ticks(ax, positions, labels):
        ax.set_xticks(positions)
        texts = [label_fn(l) for l in labels]
        ax.set_xticklabels([t for t, _ in texts], rotation=90, fontsize=6)
        for tick, (_, col) in zip(ax.get_xticklabels(), texts):
            tick.set_color(col)
        ax.tick_params(axis="x", length=0)
        ax.tick_params(axis="y", length=0)

    if wrap:
        keys = level_order(df[wrap])
        nrow, ncol = facet_layout(len(keys))
        fig, axes = _panel_grid(keys, nrow, ncol, (width, height), left=0.3, right=0.2, top=0.3,
                                bottom=0.5, wspace=0.12, hspace=0.6, sharex=False, sharey=True)
        for key in keys:
            ax = axes[key]
            theme_blank(ax)
            positions, labels = draw_bars(ax, df[df[wrap] == key], 0)
            style_ticks(ax, positions, labels)
            ax.set_xlim(-0.6, len(labels) - 0.4)
            ax.set_ylim(-0.05, 1.05)
            strip(ax, key)
            if hide_y_text:
                ax.tick_params(labelleft=False)
        save(fig, path)
        return

    facet_cols = list(facet_cols or [])
    panels = nested_panels(df, facet_cols) if facet_cols else [()]
    nlev = len(facet_cols)
    fig = plt.figure(figsize=(width, height))
    left, right, bottom, top = 0.55, 0.1, 0.75, 0.2 + 0.2 * nlev
    ax = fig.add_axes([left / width, bottom / height, 1 - (left + right) / width, 1 - (bottom + top) / height])
    theme_blank(ax)
    x0, gap = 0.0, 0.35
    spans, all_pos, all_lab = [], [], []
    for p in panels:
        mask = np.ones(len(df), bool)
        for c, v in zip(facet_cols, p):
            mask &= (df[c].isna() if pd.isna(v) else (df[c] == v)).to_numpy()
        positions, labels = draw_bars(ax, df[mask], x0)
        spans.append((x0 - 0.6, x0 + len(labels) - 0.4))
        all_pos += positions
        all_lab += labels
        x0 += len(labels) + 1.2 + gap
    ax.set_xlim(spans[0][0], spans[-1][1])
    ax.set_ylim(-0.05, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0.00", "0.25", "0.50", "0.75", "1.00"])
    ax.set_ylabel("Relative Abundance")
    style_ticks(ax, all_pos, all_lab)
    # white gaps between panels
    for (a, b), (c, _) in zip(spans[:-1], spans[1:]):
        ax.axvspan(b, c, color="white", zorder=3)
    ax_h = (1 - (bottom + top) / height) * height
    strip_h = 0.2 / ax_h
    if nlev:
        draw_nested_strips(fig, ax, panels, spans, 1.02, strip_h, gap)
    save(fig, path)


def legend_figure(scale, path, width, height, ncol=1, title="Family", fontsize=5, key_cm=0.2):
    """cowplot::get_legend() of the composition plot, saved on its own."""
    fig = plt.figure(figsize=(width, height))
    handles = [Patch(facecolor=c, edgecolor="black", linewidth=0.25, label=l)
               for c, l in zip(scale["values"], scale["labels"])]
    size = key_cm / 2.54 * 72 / fontsize  # key size in font-size units
    fig.legend(handles=handles, title=title, ncol=ncol, loc="center", fontsize=fontsize,
               title_fontsize=6, handlelength=size, handleheight=size, frameon=False,
               columnspacing=0.8, labelspacing=0.15)
    save(fig, path)


def nested_heatmap(df, x_cols, y_cols, facet_cols, path, width, height, vmin=-3, vmax=0):
    """geom_tile(fill = log10(Abundance)) with white->blue gradient; out-of-range/zero -> black."""
    ycats_order = r_interaction_order(df, y_cols)
    ykeys = interaction_labels(df, y_cols)
    ycats = list(dict.fromkeys(ykeys.iloc[ycats_order]))
    ypos = {k: i for i, k in enumerate(ycats)}
    panels = nested_panels(df, facet_cols)
    fig = plt.figure(figsize=(width, height))
    left, right, bottom, top = 2.6, 1.6, 0.75, 0.15 + 0.2 * len(facet_cols)
    ax = fig.add_axes([left / width, bottom / height, 1 - (left + right) / width,
                       max(0.05, 1 - (bottom + top) / height)])
    theme_grey(ax, grid=False)
    cmap = GRADIENT_WHITE_BLUE.copy()
    cmap.set_bad("black")
    x0, gap = 0.0, 0.35
    spans, all_pos, all_lab = [], [], []
    xkeys = interaction_labels(df, x_cols)
    mesh = None
    for p in panels:
        mask = np.ones(len(df), bool)
        for c, v in zip(facet_cols, p):
            mask &= (df[c].isna() if pd.isna(v) else (df[c] == v)).to_numpy()
        d = df[mask]
        order = r_interaction_order(d, x_cols)
        cats = list(dict.fromkeys(xkeys[mask].iloc[order]))
        M = np.full((len(ycats), len(cats)), np.nan)
        xi = {k: i for i, k in enumerate(cats)}
        with np.errstate(divide="ignore"):
            vals = np.log10(d["Abundance"].to_numpy(float))
        for xk, yk, v in zip(xkeys[mask], ykeys[mask], vals):
            M[ypos[yk], xi[xk]] = v
        M = np.ma.masked_where(~np.isfinite(M) | (M < vmin) | (M > vmax), M)
        xe = x0 - 0.5 + np.arange(len(cats) + 1)
        mesh = ax.pcolormesh(xe, np.arange(len(ycats) + 1) - 0.5, M, cmap=cmap, vmin=vmin, vmax=vmax)
        spans.append((x0 - 0.5, x0 + len(cats) - 0.5))
        all_pos += [x0 + i for i in range(len(cats))]
        all_lab += cats
        x0 += len(cats) + gap
    for (a, b), (c, _) in zip(spans[:-1], spans[1:]):
        ax.axvspan(b, c, color="white", zorder=3)
    ax.set_xlim(spans[0][0], spans[-1][1])
    ax.set_ylim(-0.5, len(ycats) - 0.5)
    ax.set_yticks(range(len(ycats)), ycats, fontsize=6)
    ax.set_xticks(all_pos, all_lab, rotation=90, fontsize=6)
    ax.tick_params(length=0)
    ax_h = max(0.05, 1 - (bottom + top) / height) * height
    draw_nested_strips(fig, ax, panels, spans, 1.0 + 0.02 / ax_h, 0.2 / ax_h, gap)
    cax = fig.add_axes([1 - 1.3 / width, 0.5 - 0.6 / height, 0.12 / width, 1.2 / height])
    cb = fig.colorbar(mesh, cax=cax)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6, length=0)
    cax.set_title("log10(Abundance)", fontsize=6, loc="left")
    save(fig, path)


def stat_ellipse_points(x, y, level=0.68, segments=51):
    """stat_ellipse(type = 'norm'): ellipse of a bivariate normal fit; None if < 3 points."""
    pts = np.column_stack([x, y]).astype(float)
    pts = pts[np.isfinite(pts).all(axis=1)]
    n = len(pts)
    if n < 3:
        return None
    from scipy import stats

    center = pts.mean(axis=0)
    cov = np.cov(pts, rowvar=False)
    try:
        chol = np.linalg.cholesky(cov).T
    except np.linalg.LinAlgError:
        return None
    radius = np.sqrt(2 * stats.f.ppf(level, 2, n - 1))
    theta = np.linspace(0, 2 * np.pi, segments)
    unit = np.column_stack([np.cos(theta), np.sin(theta)])
    return center + radius * unit @ chol


def scatter_panel(fig, panel_cm=5.0, left_in=0.6, bottom_in=0.5):
    W, H = fig.get_size_inches()
    s = panel_cm / 2.54
    return fig.add_axes([left_in / W, bottom_in / H, s / W, s / H])


def points(ax, x, y, fills, markers, size=1.5, stroke=0.5, zorder=3):
    """geom_point(shape = 21-24, colour = 'black', fill = ...) with ggplot's size in mm."""
    s = (size * PT_PER_MM + stroke * PT_PER_MM) ** 2 * 0.75
    for m in set(markers):
        sel = np.array([mm == m for mm in markers])
        ax.scatter(np.asarray(x)[sel], np.asarray(y)[sel], s=s, c=np.asarray(fills, object)[sel].tolist(),
                   marker=MARKERS.get(m, "o"), edgecolors="black", linewidths=stroke, zorder=zorder)


def violin(ax, data, pos, color, width=0.9, lw=0.2):
    """geom_violin (Gaussian KDE, bw.nrd0, trimmed to the data range); returns max density."""
    v = np.asarray(data, float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        return None
    sd = v.std(ddof=1)
    iqr = np.subtract(*np.percentile(v, [75, 25]))
    lo = min(sd, iqr / 1.34) if iqr > 0 else sd
    bw = 0.9 * (lo if lo > 0 else (sd if sd > 0 else abs(v[0]) or 1)) * len(v) ** -0.2
    grid = np.linspace(v.min(), v.max(), 512)
    dens = np.exp(-0.5 * ((grid[:, None] - v[None, :]) / bw) ** 2).sum(1) / (len(v) * bw * np.sqrt(2 * np.pi))
    return grid, dens


def draw_violins(ax, groups, colors, lw=0.2):
    """groups: list of (label, values). Uses scale = 'area' (equal areas across violins)."""
    curves = {lab: violin(ax, vals, i, colors.get(lab, GREY50)) for i, (lab, vals) in enumerate(groups)}
    dmax = max((c[1].max() for c in curves.values() if c is not None), default=1)
    for i, (lab, vals) in enumerate(groups):
        c = curves[lab]
        if c is None:
            continue
        grid, dens = c
        half = dens / dmax * 0.45
        ax.fill_betweenx(grid, i - half, i + half, facecolor=colors.get(lab, GREY50), edgecolor="black",
                         linewidth=lw, zorder=2)


def tile_heatmap(ax, mat, xlabels, ylabels, cmap, vmin, vmax, edgecolor="black", lw=0.5, bad="black"):
    """geom_tile(colour = 'black') for a matrix (rows = y from bottom, cols = x)."""
    cm = cmap.copy()
    cm.set_bad(bad)
    m = np.ma.masked_invalid(np.asarray(mat, float))
    mesh = ax.pcolormesh(np.arange(len(xlabels) + 1) - 0.5, np.arange(len(ylabels) + 1) - 0.5, m, cmap=cm,
                         vmin=vmin, vmax=vmax, edgecolors=edgecolor, linewidth=lw)
    ax.set_xticks(range(len(xlabels)), xlabels)
    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.tick_params(length=0)
    return mesh


def black_framed_colorbar(fig, mesh, rect, title=None):
    cax = fig.add_axes(rect)
    cb = fig.colorbar(mesh, cax=cax)
    cb.outline.set_edgecolor("black")
    cb.outline.set_linewidth(0.2)
    cb.ax.tick_params(labelsize=6, color="black", length=2, width=0.25)
    if title:
        cax.set_title(title, fontsize=6, loc="left")
    return cb


def log_ticks(ax, axis, lo_exp, hi_exp, step=1):
    """Axis ticks labelled 10^x (trans_format('log10', math_format(10^.x)))."""
    exps = list(range(hi_exp, lo_exp - 1, -step))[::-1]
    ticks = [10.0 ** e for e in exps]
    labels = [f"$10^{{{e}}}$" for e in exps]
    if axis == "y":
        ax.set_yticks(ticks, labels)
    else:
        ax.set_xticks(ticks, labels)
