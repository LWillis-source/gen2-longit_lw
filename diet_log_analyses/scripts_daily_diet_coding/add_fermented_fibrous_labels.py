"""Add Fermented / Fibrous labels + reasoning to ingredient_lexicon (columns X-AA).
Fermented definition: ISAPP consensus (Marco et al. 2021, doi:10.1038/s41575-020-00390-5):
 'foods made through desired microbial growth and enzymatic conversions of food components'.
Fibrous definition: EU Reg. 1924/2006 'source of fibre' = >=3 g/100 g OR >=1.5 g/100 kcal
 (per-kcal test applied to solid foods only). 'High' = >=6 g/100 g or >=3 g/100 kcal.
Fibre/kcal values are approximate, typical USDA-style values recalled by Claude, NOT looked up.
"""
import openpyxl, copy
from pathlib import Path
from openpyxl.styles import Alignment
SRC = str(Path(__file__).resolve().parents[1] / 'daily_diet_coding.xlsx')  # diet_log_analyses/daily_diet_coding.xlsx

# ---------- FIBRE: name -> (fibre g/100g, kcal/100g, form note)
F = {
'acai':(2.0,70,'frozen unsweetened pulp'),'agave':(0,310,'syrup'),'almond':(12.5,579,'whole'),
'apple':(2.4,52,'raw with skin'),'arugula':(1.6,25,'raw'),'asian pear':(3.6,42,'raw'),
'artichoke':(5.7,53,'cooked'),'asparagus':(2.1,22,'cooked'),'avocado':(6.7,160,'raw'),
'bamboo shoot':(2.2,27,'cooked'),'banana':(2.6,89,'raw'),'basil':(1.6,23,'fresh'),
'bean sprouts':(1.8,30,'raw mung sprouts'),'beet':(2.8,43,'cooked'),'bell pepper':(2.1,31,'raw'),
'berries (mixed)':(3.5,45,'mixed berries, typical'),'black bean':(8.7,132,'cooked'),
'black pepper':(25,251,'ground'),'black soybean':(6.0,173,'cooked'),'black-eyed pea':(6.5,116,'cooked'),
'blackberry':(5.3,43,'raw'),'blueberry':(2.4,57,'raw'),'bok choy':(1.0,13,'raw'),
'broccoli':(3.3,35,'cooked'),'broccoli rabe':(2.7,22,'raw'),'brussels sprouts':(2.6,36,'cooked'),
'buckwheat':(2.7,92,'cooked groats'),'burdock':(3.3,72,'raw root'),'butternut squash':(2.0,40,'cooked'),
'cabbage':(2.5,25,'raw'),'cacao':(13,480,'nibs; cocoa powder ~30 g, milk chocolate ~3 g'),
'caper':(3.2,23,'brined'),'carrot':(2.8,41,'raw'),'cashew':(3.3,553,'raw'),'cassava':(1.8,160,'cooked'),
'cauliflower':(2.0,25,'raw'),'celery':(1.6,14,'raw'),'chanterelle':(3.8,32,'raw'),'cherry':(2.1,63,'raw'),
'chia':(34,486,'dry seed'),'chickpea':(7.6,164,'cooked'),'chili pepper':(1.5,40,'raw'),
'cinnamon':(53,247,'ground'),'coconut':(9.0,354,'raw flesh'),'corn':(2.4,96,'cooked sweet corn'),
'cranberry':(4.6,46,'raw'),'cucumber':(0.5,15,'raw'),'cumin':(10.5,375,'ground'),
'curry spices':(22,330,'turmeric/coriander/cumin mix'),'daikon':(1.6,18,'raw'),'dill':(2.1,43,'fresh'),
'edamame':(5.2,121,'cooked'),'eggplant':(2.5,35,'cooked'),'enoki':(2.7,37,'raw'),'fig':(2.9,74,'raw'),
'garlic':(2.1,149,'raw'),'ginger':(2.0,80,'raw'),'glutinous rice':(0.5,97,'cooked'),
'granola':(5.0,470,'typical'),'grape':(0.9,69,'raw'),'grapefruit':(1.6,42,'raw'),'green bean':(2.7,31,'cooked'),
'guava':(5.4,68,'raw'),'hoisin sauce':(2.8,220,'sauce'),'huel':(7.0,400,'powder; label value recalled, check pack'),
'imitation crab':(0.3,95,'surimi'),'impossible meat':(2.7,220,'cooked patty; label value recalled'),
'jam':(0.6,250,'fruit jam'),'kale':(3.6,49,'raw'),'kimchi':(1.6,15,'prepared'),'kiwi':(3.0,61,'raw'),
'konjac':(3.0,10,'shirataki-type; glucomannan, soluble'),'leek':(1.8,61,'raw'),'lemon':(2.8,29,'raw'),
'lentil':(7.9,116,'cooked'),'lettuce':(1.3,15,'raw'),'lime':(2.8,30,'raw'),'lotus root':(4.9,74,'raw'),
'luffa':(1.1,20,'cooked; value uncertain'),'lychee':(1.3,66,'raw'),'macadamia':(8.6,718,'raw'),
'mandarin':(1.8,53,'raw'),'mango':(1.6,60,'raw'),'melon':(0.9,34,'cantaloupe, raw'),
'miso':(5.4,199,'paste'),'mung bean':(7.6,105,'cooked'),'mushroom':(1.0,22,'raw white button'),
'mustard':(4.0,66,'prepared yellow mustard'),'napa cabbage':(1.2,12,'raw'),'natto':(5.4,212,'prepared'),
'nori':(36,35,'dried sheet'),'nutritional yeast':(25,350,'flakes; label value recalled'),
'nuts (unspecified)':(7.0,600,'typical tree nuts'),'oat':(1.7,71,'cooked porridge'),
'okra':(3.2,33,'raw'),'olive':(3.3,115,'brined'),'onion':(1.7,40,'raw'),'orange':(2.4,47,'raw'),
'oyster mushroom':(2.3,33,'raw'),'parsley':(3.3,36,'fresh'),'passionfruit':(10.4,97,'raw'),
'pea':(5.5,84,'cooked green peas'),'pea protein':(2.0,380,'isolate; brand dependent'),'peach':(1.5,39,'raw'),
'peanut':(8.5,567,'raw'),'pecan':(9.6,691,'raw'),'pine nut':(3.7,673,'raw'),'pineapple':(1.4,50,'raw'),
'pistachio':(10.3,560,'raw'),'plantain':(2.3,122,'raw'),'plum':(1.4,46,'raw'),'potato':(1.8,87,'boiled with skin'),
'pumpkin':(1.1,20,'cooked'),'pumpkin seed':(6.0,559,'dry'),'quinoa':(2.8,120,'cooked'),'radish':(1.6,16,'raw'),
'raisin':(3.7,299,'dried'),'raspberry':(6.5,52,'raw'),'red bean':(7.3,128,'cooked adzuki'),
'rice':(0.4,130,'cooked white; brown rice ~1.8 g'),'saffron':(3.9,310,'dried threads'),
'scallion':(2.6,32,'raw'),'seaweed':(0.5,45,'wakame, raw/rehydrated; dried seaweed is far higher'),
'sesame':(11.8,573,'seeds'),'shiitake':(2.1,56,'cooked'),'soybean':(6.0,173,'cooked'),
'soybean paste':(5.4,199,'paste'),'spinach':(2.4,23,'cooked'),'squash':(1.8,20,'cooked summer squash'),
'stone fruit':(1.6,45,'peach/plum/cherry range'),'strawberry':(2.0,32,'raw'),'sweet potato':(2.5,76,'boiled'),
'tapioca':(0.9,358,'dry pearls'),'teff':(2.8,101,'cooked'),'thousand island dressing':(0.5,380,'dressing'),
'tofu':(0.9,76,'firm; USDA-type entries differ (0.3-2.3)'),'tofu skin':(0.7,200,'value uncertain'),
'tomato':(1.2,18,'raw'),'trail mix':(5.0,460,'typical nut/fruit mix'),'turmeric':(22.7,312,'ground'),
'urad dal':(4.0,105,'cooked'),'walnut':(6.7,654,'raw'),'wasabi':(7.8,109,'true wasabi root; paste is often horseradish/mustard'),
'watermelon':(0.4,30,'raw'),'wild rice':(1.8,101,'cooked'),'wood ear':(6.5,25,'value uncertain'),
'yam':(4.1,116,'cooked'),'zucchini':(1.0,17,'raw'),
}
LIQUID = {'almond milk':0.3,'oat milk':0.8,'soy milk':0.4,'soy sauce':0.8,'balsamic vinegar':0.0}
ZERO_ANIMAL = {'beef','butter','cheese','chicken','cod','collagen','cow milk','crab','cream','cream cheese','duck','egg','feta','fish',
 'gelatin','goat cheese','hamachi','ice cream','lamb','octopus','paneer','pork','quail egg','rockfish','salmon','sardine','scallop',
 'seafood (mixed)','shellfish','shrimp','squid','tuna','turkey','unagi','veal','whey','white fish','yogurt','anchovy'}
ZERO_OTHER = {
 'amaro':'Alcoholic liqueur; no dietary fibre as consumed.','beer':'Beverage; negligible fibre (<1 g/100 mL).',
 'bourbon':'Distilled spirit; distillation removes fibre.','whiskey':'Distilled spirit; distillation removes fibre.',
 'soju':'Distilled spirit; no fibre.','spirits':'Distilled spirits; no fibre.','herbal liqueur':'Alcoholic infusion; no fibre as consumed.',
 'limoncello':'Alcoholic infusion; no fibre as consumed.','wine':'Beverage; negligible fibre.','coffee':'Brewed beverage; ~0 g/100 mL.',
 'tea':'Brewed beverage; ~0 g/100 mL.','diet soda':'Carbonated sweetened beverage; 0 g fibre.','sugar':'Refined sugar (sucrose); 0 g fibre.',
 'maple syrup':'Syrup; 0 g fibre.','olive oil':'Pure fat; 0 g fibre.','vegetable oil':'Pure fat; 0 g fibre.',
 'honey':'Sugars only; 0 g fibre.',
 'vanilla':'Used as extract or trace flavouring; negligible fibre contributed.',
 'bergamot':'Most likely a flavouring (e.g. Earl Grey tea, peel oil); negligible fibre as consumed.'}
FOV = {
 'unknown':('Unknown','Ingredient not identified in the diet log, so fibre content cannot be assessed.'),
 'fruit (unspecified)':('Yes','Most whole fruits contain 1.5-6 g fibre/100 g and 2-8 g/100 kcal, so nearly all pass the EU "source of fibre" test; individual fruits (e.g. watermelon, grape) can fall below. Treat as probable, not certain.'),
 'mixed vegetables':('Yes','Mixed vegetables are typically 2-4 g fibre/100 g and >5 g/100 kcal (low energy density), passing the EU "source of fibre" test; exact mix unknown.'),
 'beans (unspecified)':('Yes','Cooked beans are 6-9 g fibre/100 g in all common types (black ~8.7, kidney ~6.4, white ~6.3); meets the "high fibre" tier.'),
 'grain cereal':('Variable','Whole-grain cereals are often >6 g/100 g, but refined cereals (e.g. cornflakes) are ~1-3 g/100 g. Product not specified, so not assignable.'),
 'grain-free cereal':('Variable','Nut/seed-based cereals are usually fibre-rich (3-10 g/100 g) but the product is not identified; not assignable.'),
 'gluten-free flour':('Variable','Blends of rice, tapioca and corn starch are low (~1-3 g/100 g), but blends with sorghum, buckwheat or legume flours are higher. Brand not specified.'),
 'ikea plant balls':('Variable','Pea/oat/potato-based product; fibre value not recalled and not looked up. Possibly ~3 g/100 g (borderline); check the pack label.'),
 'plant-based mince':('Variable','Soy/pea-protein mince ranges roughly 1-5 g fibre/100 g depending on brand; not specified.'),
 'soy meat':('Variable','Textured soy protein is ~13-17 g/100 g dry but ~3-5 g/100 g once hydrated; form not specified.'),
 'vegan caesar dressing':('Variable','Oil/emulsion-based dressing with nuts, seeds or capers possible; fibre likely <1 g/100 g but recipe not specified.'),
 'vegan cheese':('Variable','Coconut-oil/starch-based types ~0-1 g/100 g; cashew/almond-based types ~1-4 g/100 g. Product not specified.'),
 'wheat':('Variable','Whole-wheat flour ~12 g/100 g (passes "high fibre"), white flour ~2.7 g/100 g (borderline). Refinement level not specified.'),
 'protein powder':('Variable','Whey isolate has 0 g fibre; pea or blended powders ~0-5 g/100 g. Type not specified.'),
 'supplement':('Unknown','Content of the supplement is not recorded; could be a fibre product (e.g. psyllium) or not.'),
 'truffle':('Unknown','No reliable fibre value recalled for truffles (Tuber spp.); eaten only as shavings, so the contribution is negligible either way.'),
}

# ---------- FERMENTED
FY = {
 'beer':'Brewed by yeast fermentation of malted-barley wort; meets the ISAPP definition (microbes are removed or inactivated in most products).',
 'wine':'Yeast fermentation of grape juice is the defining production step.',
 'balsamic vinegar':'Traditional balsamic: grape must undergoes alcoholic then acetic fermentation. Cheap commercial versions may be wine vinegar plus must (still fermentation-derived).',
 'bourbon':'Mash of fermented corn, rye and barley, then distilled. Fermentation is a core step; distillation leaves no live microbes. Whether distilled spirits count as "fermented foods" is a classification choice not settled by the ISAPP text.',
 'whiskey':'Fermented grain mash, then distilled (see bourbon note on distillation).',
 'soju':'Distilled from fermented rice or other starch; see bourbon note on distillation.',
 'spirits':'Distilled from fermented sugar/starch substrates; see bourbon note on distillation.',
 'cheese':'Milk acidified and ripened by starter lactic acid bacteria (and moulds in some types); cultures are central to the product.',
 'cream cheese':'Cream/milk cultured with lactic acid bacteria before draining; some commercial brands use acidulants, so cultured status can vary by brand.',
 'feta':'Brined cheese made with lactic acid bacteria starter cultures and ripened.',
 'goat cheese':'Milk coagulated with starter cultures and/or rennet; lactic acid bacteria are part of production.',
 'yogurt':'Milk fermented by Streptococcus thermophilus and Lactobacillus delbrueckii subsp. bulgaricus; the textbook example of a fermented food.',
 'kimchi':'Vegetables fermented by lactic acid bacteria (Leuconostoc, Lactobacillus, Weissella).',
 'miso':'Soybeans fermented with koji (Aspergillus oryzae), then yeasts and lactic acid bacteria.',
 'natto':'Soybeans fermented by Bacillus subtilis var. natto.',
 'soy sauce':'Soy and wheat fermented with koji mould followed by salt-brine fermentation (cheaper chemically hydrolysed versions exist).',
 'soybean paste':'Fermented soybean paste (doenjang/doubanjiang type); koji and bacterial fermentation.',
 'cacao':'Cocoa beans are routinely fermented for several days (yeasts, lactic and acetic acid bacteria) before drying. Raw or unfermented cacao exists, so check the product.',
}
FV = {
 'butter':'Cultured butter is made from fermented cream; common US sweet-cream butter is not fermented. Type not recorded.',
 'whey':'Whey from cheesemaking is a by-product of a fermented process (acid whey) or a rennet process (sweet whey); powders are not themselves live-cultured.',
 'hoisin sauce':'Often contains fermented soybean paste, but many commercial recipes use soy flour, sugar and vinegar. Varies by brand.',
 'thousand island dressing':'May contain vinegar and pickles (fermented or brined); not itself a fermented food. Varies.',
 'vegan caesar dressing':'Recipe unknown; may include miso, vinegar or capers (fermented ingredients). Not assignable.',
 'vegan cheese':'Some nut-based cheeses are cultured with lactic acid bacteria; many starch/coconut-oil types are not.',
 'protein powder':'Whey is a by-product of cheesemaking; pea protein is not fermented. Some powders add probiotics. Type not specified.',
 'olive':'Table olives are often fermented in brine (Spanish/Greek style), but lye-cured canned black olives are not.',
 'caper':'Brined capers undergo lactic fermentation in the brine; salt- or vinegar-packed capers may not.',
 'coffee':'Wet-processing of coffee cherries involves a fermentation step before drying, but beans are then roasted (no live microbes) and coffee is not usually treated as a fermented food.',
 'anchovy':'Salt-cured and matured by enzymatic and microbial activity; whether this counts as microbial fermentation is debated. Fresh anchovy is not fermented.',
 'amaro':'Herbal liqueur: infusion in alcohol made from a distilled fermented base. The product itself is an infusion, not a ferment.',
 'herbal liqueur':'Infusion in alcohol made from a distilled fermented base; not itself fermented.',
 'limoncello':'Lemon-peel infusion in neutral spirit (distilled from fermented material); not itself fermented.',
 'mustard':'Prepared mustard contains vinegar (a fermentation product) but the mustard itself is not fermented.',
 'supplement':'Probiotic supplements contain live microbes or fermentation products; others do not. Content unknown.',
}
FN = {
 'paneer':'Fresh cheese curdled with acid (lemon juice or vinegar) or heat; no microbial fermentation step.',
 'cream':'Fresh pasteurised cream. Cultured cream (crème fraîche, sour cream) would be fermented but is a different product.',
 'cow milk':'Fresh milk; fermentation (yogurt, kefir) would be a different product.',
 'ice cream':'Frozen dairy dessert; no fermentation step.',
 'tofu':'Soy milk coagulated with calcium or magnesium salts; microbial fermentation is not involved (fermented tofu is a different product).',
 'tofu skin':'Film skimmed from heated soy milk; not microbially fermented.',
 'nutritional yeast':'Deactivated Saccharomyces cerevisiae biomass grown on molasses. It is the microbe itself, not a food transformed by one; arguably borderline.',
 'tea':'Black/green tea is processed by enzymatic oxidation and drying, not microbial fermentation. Post-fermented teas (pu-erh) and kombucha are exceptions, not specified here.',
 'vanilla':'Beans are cured by heating and sweating (largely enzymatic); not classed as microbial fermentation.',
 'honey':'Produced by bees via enzymes and evaporation; not microbial fermentation (mead would be).',
 'impossible meat':'Plant-based patty; its heme protein is made by recombinant yeast (precision fermentation), which is not what is usually meant by a fermented food. Recalled from company information, not verified here.',
 'sugar':'Crystallised sucrose from cane or beet; no fermentation step.',
 'bean sprouts':'Germinated seeds (plant growth), not microbial fermentation.',
 'urad dal':'Dry split lentils; fermented idli/dosa batter is a different preparation.',
 'cassava':'Raw or cooked root; fermented cassava products (gari, fufu) are different preparations.',
 'teff':'Grain; injera (fermented teff batter) is a different preparation.',
 'imitation crab':'Surimi (washed, minced fish paste) with starch and flavouring; no fermentation step.',
 'gelatin':'Collagen extracted from animal tissue by heat and acid/alkali; no fermentation.',
 'collagen':'Hydrolysed animal collagen; no fermentation.',
 'sardine':'Fresh or canned fish; salting or fermentation is not part of normal canning.',
 'pork':'Fresh pork; fermented sausages and cured hams are different products.',
 'beef':'Fresh or cooked beef; dry-ageing is enzymatic and surface growth is trimmed, so it is not a fermented food.',
 'wheat':'Cereal grain or flour; bread or sourdough made from it would be fermented but is a different product.',
 'granola':'Baked oat mix; no fermentation step.',
 'oat milk':'Enzyme-treated oat extract; enzymes alone are insufficient under the ISAPP definition.',
 'almond milk':'Water extract of almonds; no fermentation.',
 'soy milk':'Water extract of soybeans; no fermentation (soy yogurt would be).',
 'jam':'Fruit cooked with sugar; no fermentation.',
 'huel':'Powdered nutritionally complete drink; no fermentation (some added ingredients may be of fermented origin).',
 'ikea plant balls':'Plant-protein formed product; no fermentation step known (recipe not checked).',
 'plant-based mince':'Textured plant protein; no fermentation step known, unless it uses mycoprotein or tempeh (unspecified).',
 'soy meat':'Textured soy protein; no fermentation step (tempeh would be).',
 'pea protein':'Protein isolate extracted from peas; no fermentation.',
 'diet soda':'Carbonated, chemically sweetened beverage; carbonation is not fermentation.',
 'trail mix':'Dried fruit and nut mix; no fermentation.',
 'seaweed':'Harvested and dried seaweed; no fermentation.',
}
# 17 Oct 2026 decision (Lisa): distilled spirits and liqueurs are NOT counted as fermented
for _k in ('bourbon','whiskey','soju','spirits','amaro','herbal liqueur','limoncello'):
    FY.pop(_k, None); FV.pop(_k, None)
_d = 'Made from a fermented mash or base but then distilled; distillation removes live microbes. Not counted as fermented by project decision (17 Oct 2026).'
FN.update({k: _d for k in ('bourbon','whiskey','soju','spirits')})
_l = 'Alcoholic infusion in a distilled spirit; distilled base and no live microbes. Not counted as fermented by project decision (17 Oct 2026).'
FN.update({k: _l for k in ('amaro','herbal liqueur','limoncello')})
ANIMALS = {'beef','chicken','cod','crab','duck','egg','fish','hamachi','lamb','octopus','pork','quail egg','rockfish','salmon',
 'sardine','scallop','seafood (mixed)','shellfish','shrimp','squid','tuna','turkey','unagi','veal','white fish'}
PLANT_DEFAULT = ('Plant (or fungal) food eaten fresh, cooked or dried; microbial fermentation is not part of normal '
                 'production. A pickled or fermented version would be a different product.')
ANIMAL_DEFAULT = ('Animal muscle, egg or seafood eaten fresh or cooked; no fermentation step in normal production '
                  '(fermented or cured versions such as fermented sausage or fish sauce would be different products).')
SMALL = {'black pepper','cinnamon','cumin','saffron','turmeric','curry spices','wasabi','basil','dill','parsley','caper','cacao','nori'}


def fibre(n):
    if n in FOV: return FOV[n]
    if n in ZERO_ANIMAL:
        return ('No', 'Animal-derived or non-plant product: contains no dietary fibre (fibre is plant, fungal or algal cell-wall material). 0 g/100 g.')
    if n in ZERO_OTHER: return ('No', ZERO_OTHER[n])
    if n in LIQUID:
        return ('No', f'Liquid or condiment: about {LIQUID[n]:g} g fibre/100 g (approximate), below the 3 g/100 g threshold. The per-kcal test is not applied to liquids and condiments.')
    if n in F:
        f, k, form = F[n]
        d = f / k * 100 if k else 0
        pass_g, pass_k = f >= 3, d >= 1.5
        yes = pass_g or pass_k
        tier = 'high' if (f >= 6 or d >= 3) else 'source'
        # borderline = within ~20% of the deciding threshold
        bord = (not (f >= 3.6 or d >= 1.8)) if yes else (f >= 2.4 or d >= 1.2)
        txt = f'≈{f:g} g fibre and ≈{k:g} kcal per 100 g ({form}); ≈{d:.1f} g/100 kcal. '
        if yes:
            how = []
            if pass_g: how.append('≥3 g/100 g')
            if pass_k: how.append('≥1.5 g/100 kcal')
            txt += f'Meets EU "source of fibre" ({" and ".join(how)}); tier: {tier}.'
        else:
            txt += 'Below both EU "source of fibre" thresholds.'
        if bord: txt += ' Borderline: small changes in variety or preparation could flip the label.'
        if n in SMALL: txt += ' Composition label only: usual portions are small, so practical fibre intake is low.'
        return ('Yes' if yes else 'No', txt)
    return None


def ferm(n):
    if n == 'unknown': return ('Unknown', 'Ingredient not identified in the diet log, so fermentation status cannot be assessed.')
    if n in FY: return ('Yes', FY[n])
    if n in FV: return ('Unknown' if n == 'supplement' else 'Variable', FV[n])
    if n in FN: return ('No', FN[n])
    if n in ANIMALS: return ('No', ANIMAL_DEFAULT)
    return ('No', PLANT_DEFAULT)


wb = openpyxl.load_workbook(SRC)
ws = wb['ingredient_lexicon']
hdr = [c.value for c in ws[1]]
assert len(hdr) == 23 and hdr[22].startswith('Informative: review note'), hdr
names = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
heads = ['Fermented? (Yes / No / Variable / Unknown)', 'Fermented: reasoning',
         'Fibrous? (Yes / No / Variable / Unknown)', 'Fibrous: reasoning']
for i, h in enumerate(heads):
    c = ws.cell(1, 24 + i, h); s = ws.cell(1, 23)
    c.font = copy.copy(s.font); c.fill = copy.copy(s.fill); c.alignment = copy.copy(s.alignment); c.border = copy.copy(s.border)

miss = []; counts = {'ferm': {}, 'fibre': {}}
for r, n in enumerate(names, start=2):
    a = ferm(n); b = fibre(n)
    if b is None:
        miss.append(n); b = ('Unknown', 'No fibre value assigned.')
    for j, v in enumerate([a[0], a[1], b[0], b[1]]):
        c = ws.cell(r, 24 + j, v); c.font = copy.copy(ws.cell(r, 15).font)
        c.alignment = Alignment(wrap_text=True, vertical='top')
    counts['ferm'][a[0]] = counts['ferm'].get(a[0], 0) + 1
    counts['fibre'][b[0]] = counts['fibre'].get(b[0], 0) + 1
print('missing fibre:', miss); print(counts)
for col, w in zip(['X', 'Y', 'Z', 'AA'], [16, 60, 16, 70]): ws.column_dimensions[col].width = w
ws.auto_filter.ref = f'A1:AA{ws.max_row}'

rd = wb['README']; r = rd.max_row + 2
lines = [
 'Lexicon Fermented and Fibrous labels (added 17 Oct 2026; columns X-AA of ingredient_lexicon)',
 'Fermented? uses the ISAPP consensus definition: "foods made through desired microbial growth and enzymatic conversions of food components" (Marco et al. 2021, doi:10.1038/s41575-020-00390-5). Enzymes alone are insufficient.',
 'Fermented values: Yes = fermentation is a core production step; No = not part of normal production; Variable = depends on product type or brand; Unknown = ingredient not identified. Distilled spirits and liqueurs are labelled No: distillation removes live microbes, and they are excluded by project decision (17 Oct 2026).',
 'Fibrous? uses the EU nutrition-claim criterion for "source of fibre" (Regulation (EC) 1924/2006): >=3 g fibre/100 g OR >=1.5 g fibre/100 kcal. "High fibre" = >=6 g/100 g or >=3 g/100 kcal. The per-kcal test is applied to solid foods only, not to liquids or condiments.',
 'The fibre and kcal numbers in the reasoning are approximate typical USDA-style values recalled by Claude for the food as usually eaten (cooked or raw, as stated). They were NOT looked up in a database. Check borderline rows before relying on them.',
 'Fibrous labels describe the food per 100 g, not the amount eaten. Spices and herbs can be Yes by composition although portions are tiny. Variable and Unknown rows (unspecified products) are not assignable.',
 'Script that wrote these columns: add_fermented_fibrous_labels.py (backup: daily_diet_coding_backup_before_fermented_fibrous_2026-10-17.xlsx).']
for i, t in enumerate(lines):
    rd.cell(r + i, 1, t)
wb.save(SRC)
print('saved')
