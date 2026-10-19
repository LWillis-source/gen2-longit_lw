"""Check that the ingredient_lexicon mapping (ingredient -> Species) agrees with the
'Species (scientific name)' column of the daily_diet_coding tab.  Read-only.

For every row the expected taxa are rebuilt from the row's Ingredients and the lexicon;
vague ingredients (the groups on the needs_review tab) are expected as their needs_review
group instead, by design.  Comparison is on taxon names (rank and qualifier brackets removed);
the tab lists each taxon once per row, so the order is not compared.

Output: summary on screen and lexicon_vs_diet_species_check.csv (rows needing a look).
Run:  python check_lexicon_species_consistency.py
"""
import re, collections
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
X = HERE.parent / 'daily_diet_coding.xlsx'
rd = lambda t: pd.read_excel(X, sheet_name=t, keep_default_na=False, na_values=[''])
d, lex_df, nr = rd('daily_diet_coding'), rd('ingredient_lexicon'), rd('needs_review')

BR = re.compile(r'\([^()]*(?:\([^()]*\))?[^()]*\)')          # bracket group, one nesting level
def base(s): return re.sub(r'\s+', ' ', BR.sub('', s)).replace(' spp.', '').strip().lower()
RANKS = {'species', 'species (hybrid)', 'variety', 'subspecies', 'genus', 'family', 'order', 'infraorder', 'subfamily',
         'class', 'clade', 'kingdom', 'domain', 'unranked'}
def parts(e):
    """-> (base, rank, qualifiers, assumed)"""
    groups = [g[1:-1] for g in re.findall(r'\((?:[^()]|\([^()]*\))*\)', e)]
    rank = next((g for g in groups if g in RANKS), None)
    assumed = '(assumed)' in e
    qual = [g for g in groups if g not in RANKS and g != 'assumed']
    return base(e), rank, qual, assumed

lex = {r['Ingredient']: str(r['Species (scientific name)']) for _, r in lex_df.iterrows()}
grp = {}                                                     # vague item -> needs_review group
for s in nr['Finest assignment (item → taxon)'].dropna():
    for p in s.split(' | '):
        if '→' in p:
            it, tx = p.split('→', 1); grp[it.strip()] = tx.strip()

issues, by_design_rows = [], 0
rank_of = collections.defaultdict(set); qual_bad = []
unknown_tokens = collections.Counter(); used = set()
for i, r in d.iterrows():
    toks = [t.strip() for t in str(r['Ingredients']).split(';') if t.strip()]
    exp = collections.OrderedDict(); vague = []
    for t in toks:
        a = t.endswith('(assumed)'); n = re.sub(r'\s*\(assumed\)$', '', t).strip(); used.add(n)
        if n in grp and n != 'unknown': vague.append(n); sp = [grp[n]]   # 'unknown' stays as in the lexicon
        elif n in lex: sp = lex[n].split(';')
        else: unknown_tokens[n] += 1; continue
        for e in sp:
            b = base(e); ea = a or '(assumed)' in e      # lexicon can itself mark the species as assumed
            exp[b] = (exp[b] and ea) if b in exp else ea
    act = collections.OrderedDict(); dup = []
    for e in str(r['Species (scientific name)']).split(';'):
        e = e.strip()
        if not e: continue
        b, rk, ql, a = parts(e); rank_of[b].add(rk)
        if b in act: dup.append(b)
        act[b] = (act[b] and a) if b in act else a
        for q in ql:
            lexs = ' '.join(lex.get(re.sub(r'\s*\(assumed\)$', '', t).strip(), '') for t in toks)
            if not (any(q in t for t in toks) or ('(' + q + ')') in lexs): qual_bad.append((i + 2, e))
    miss = [k for k in exp if k not in act]; extra = [k for k in act if k not in exp]
    flag = [k for k in exp if k in act and exp[k] != act[k]]
    if vague: by_design_rows += 1
    if miss or extra or flag or dup:
        issues.append(dict(excel_row=i + 2, subject=r['Subject_ID'], date=r['Date (MM-DD)'], entry=r['Entry_no'],
                           ingredients=r['Ingredients'], species_in_tab=r['Species (scientific name)'],
                           expected_not_in_tab='; '.join(miss), in_tab_not_expected='; '.join(extra),
                           assumed_flag_differs='; '.join(flag), duplicated_taxon='; '.join(dup)))

print('rows checked:', len(d))
print('rows containing a vague ingredient (expected = needs_review group, by design):', by_design_rows)
print('rows with any difference:', len(issues))
print('ingredient tokens not in lexicon:', dict(unknown_tokens) or 'none')
print('lexicon ingredients never used in the tab:', sorted(set(lex) - used))
multi = {k: sorted(map(str, v)) for k, v in rank_of.items() if len(v) > 1}
print('taxa with more than one rank label:', multi or 'none')
print('qualifier brackets with no matching ingredient:', qual_bad or 'none')
print('--- vague lexicon ingredients whose lexicon Species differs from the tab (by design):')
for k, v in grp.items():
    if k in lex and k != 'unknown' and base(lex[k]) != base(v): print(f'   {k}: lexicon "{lex[k]}"  ->  tab "{v}"')
pd.DataFrame(issues, columns=['excel_row','subject','date','entry','ingredients','species_in_tab','expected_not_in_tab','in_tab_not_expected','assumed_flag_differs','duplicated_taxon']).to_csv(HERE / 'lexicon_vs_diet_species_check.csv', index=False)
# lexicon internal: does Genus column agree with the Species string?
bad = []
for _, r in lex_df.iterrows():
    sp, g = str(r['Species (scientific name)']), r['Genus']
    if pd.isna(g) or ';' in sp or not re.match(r'^[A-Z][a-z]+ [a-z]', sp): continue
    if sp.split()[0] != str(g).split(';')[0].strip(): bad.append((r['Ingredient'], sp, g))
print('lexicon rows where Genus column differs from the genus in Species:', bad or 'none')
