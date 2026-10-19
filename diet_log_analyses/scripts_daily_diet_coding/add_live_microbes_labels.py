"""Add 'Likely live microbes?' + reasoning to ingredient_lexicon (columns AB-AC).
Rule: Yes = the product as usually eaten is expected to contain viable fermentation microbes
(starter cultures or ferment microbes); Variable = depends on brand, pasteurisation or cooking;
No = none expected; Unknown = ingredient not identified. Surface microbes on raw produce or meat
are NOT counted. Classification follows review statements in Patel 2023 (doi:10.3390/foods12040687)
and Siddiqui 2023 (doi:10.1186/s40643-023-00702-y); product-level calls are from general knowledge.
"""
import openpyxl, copy
from pathlib import Path
from openpyxl.styles import Alignment
SRC = str(Path(__file__).resolve().parents[1] / 'daily_diet_coding.xlsx')  # diet_log_analyses/daily_diet_coding.xlsx

YES = {
 'yogurt': 'Defined by live starter cultures; fermented-milk rules set minimum live counts (Siddiqui 2023, citing legislation) and many labels state live cultures. Exceptions: yogurt heat-treated after culturing, and yogurt that is cooked or baked.',
 'kimchi': 'Non-heated fermented vegetables are listed among foods with viable microorganisms (Patel 2023). Cooked kimchi (stews, fried rice) or heat-treated jarred kimchi would not be live.',
 'natto': 'Listed among fermented foods with viable microorganisms (Patel 2023; Siddiqui 2023). Cooking would kill them.',
}
VAR = {
 'cheese': 'Most cheeses are listed as containing viable microorganisms (Patel 2023), but processed cheese, cooked or melted cheese, and heat-treated products do not. Type and cooking not recorded.',
 'feta': 'Brined cheese usually carries viable lactic acid bacteria, but pasteurised-after-ripening or cooked feta would not. Product not recorded.',
 'goat cheese': 'Cheeses are generally listed as live (Patel 2023); heat-treated or baked goat cheese is not. Product not recorded.',
 'cream cheese': 'Cultured, but many brands are heat-treated or acidified after culturing, which removes live microbes. Brand not recorded.',
 'miso': 'Listed among foods with viable microorganisms (Patel 2023), but many commercial misos are pasteurised and boiling in soup kills microbes. Product and cooking not recorded.',
 'soybean paste': 'Traditional unpasteurised pastes can be live; pasteurised or cooked pastes are not. Product and cooking not recorded.',
 'beer': 'Most beers have no viable microbes (filtered or pasteurised; Patel 2023) but some beers do (Siddiqui 2023), e.g. unfiltered bottle-conditioned. Type not recorded.',
 'butter': 'Cultured butter can contain lactic acid bacteria; common sweet-cream butter has no fermentation microbes. Type not recorded.',
 'vegan cheese': 'Only cultured nut-based cheeses would carry live bacteria; starch/coconut-oil types have none. Product not recorded.',
 'protein powder': 'Some powders add probiotics; spray-dried whey or pea protein has no live microbes. Type not recorded.',
 'olive': 'Naturally fermented, unpasteurised table olives may carry live lactic acid bacteria; heat-sterilised canned olives do not.',
 'caper': 'Brine-fermented capers may carry live lactic acid bacteria if unpasteurised; shelf-stable jarred capers are usually heat-treated (general knowledge, not verified).',
 'supplement': 'Only probiotic supplements contain live microbes; the supplement content is not recorded.',
}
NO_FERM = {
 'wine': 'Typically filtered and sulfite-treated, so no viable microbes expected (Patel 2023 lists most wine as non-viable). Unfiltered "natural" wine may differ.',
 'balsamic vinegar': 'Vinegar is listed among fermented foods without viable microorganisms (Patel 2023).',
 'soy sauce': 'Heat-treated after fermentation, so not live (Patel 2023; Siddiqui 2023).',
 'cacao': 'Beans are roasted after fermentation, killing the microbes (Patel 2023; Siddiqui 2023).',
 'hoisin sauce': 'Cooked or acidified sauce; any fermented component is heat-treated or diluted.',
 'thousand island dressing': 'Emulsified, acidified dressing; any pickle or vinegar component is not a live culture.',
 'coffee': 'Beans are roasted and the drink is brewed hot; no viable microbes.',
 'anchovy': 'Salt-cured or canned; not a live-culture food.',
 'mustard': 'Contains vinegar (non-viable) and mustard seed; no live cultures.',
 'whey': 'Dried whey powder; no viable fermentation microbes expected.',
 'nutritional yeast': 'The yeast is heat-deactivated before sale, so it is not viable.',
 'bourbon': 'Distilled; distillation removes viable microbes.', 'whiskey': 'Distilled; distillation removes viable microbes.',
 'soju': 'Distilled; distillation removes viable microbes.', 'spirits': 'Distilled; distillation removes viable microbes.',
 'amaro': 'Distilled-spirit infusion; no viable microbes.', 'herbal liqueur': 'Distilled-spirit infusion; no viable microbes.',
 'limoncello': 'Distilled-spirit infusion; no viable microbes.',
}
UNK = {
 'unknown': 'Ingredient not identified in the diet log, so live-microbe status cannot be assessed.',
 'vegan caesar dressing': 'Recipe unknown; it may contain miso or other fermented items, but dressings are rarely live-cultured. Not assignable.',
}
DEFAULT = ('Not a fermented food, so no fermentation microbes expected. Surface microbes on raw produce, meat or '
           'seafood are not counted here.')

wb = openpyxl.load_workbook(SRC)
ws = wb['ingredient_lexicon']
hdr = [c.value for c in ws[1]]
assert len(hdr) == 27 and hdr[26].startswith('Fibrous: reasoning'), hdr
names = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
heads = ['Likely live microbes? (Yes / Variable / No / Unknown)', 'Live microbes: reasoning']
for i, h in enumerate(heads):
    c = ws.cell(1, 28 + i, h); s = ws.cell(1, 27)
    c.font = copy.copy(s.font); c.fill = copy.copy(s.fill); c.alignment = copy.copy(s.alignment); c.border = copy.copy(s.border)
counts = {}
for r, n in enumerate(names, start=2):
    if n in YES: v = ('Yes', YES[n])
    elif n in VAR: v = ('Variable', VAR[n])
    elif n in NO_FERM: v = ('No', NO_FERM[n])
    elif n in UNK: v = ('Unknown', UNK[n])
    else: v = ('No', DEFAULT)
    for j, t in enumerate(v):
        c = ws.cell(r, 28 + j, t); c.font = copy.copy(ws.cell(r, 25).font)
        c.alignment = Alignment(wrap_text=True, vertical='top')
    counts[v[0]] = counts.get(v[0], 0) + 1
print(counts)
ws.column_dimensions['AB'].width = 18; ws.column_dimensions['AC'].width = 70
ws.auto_filter.ref = f'A1:AC{ws.max_row}'

rd = wb['README']; r = rd.max_row + 2
lines = [
 'Lexicon "Likely live microbes?" (added 17 Oct 2026; columns AB-AC of ingredient_lexicon)',
 'Question asked: is the product, as usually eaten, likely to contain viable fermentation microbes (starter cultures or ferment microbes)? Surface microbes on raw produce or meat are not counted.',
 'Values: Yes = usually live; Variable = depends on brand, pasteurisation or cooking; No = none expected; Unknown = ingredient not identified.',
 'Basis: review statements that non-heated fermented vegetables, most cheeses, miso, yoghurt and natto contain viable microbes, while vinegar, soy sauce, most beer and wine, roasted cacao and distilled spirits do not (Patel 2023, doi:10.3390/foods12040687; Siddiqui 2023, doi:10.1186/s40643-023-00702-y). Product-level calls (brand, pasteurisation, cooking) are general knowledge, not tested.',
 'Distilled spirits and liqueurs are Fermented? = No (project decision) and Likely live microbes = No.',
 'Script: add_live_microbes_labels.py (backup: daily_diet_coding_backup_before_live_microbes_2026-10-17.xlsx).']
for i, t in enumerate(lines):
    rd.cell(r + i, 1, t)
wb.save(SRC)
print('saved')
