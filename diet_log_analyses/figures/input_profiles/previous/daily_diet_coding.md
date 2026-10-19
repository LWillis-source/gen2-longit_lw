# daily_diet_coding

- File: `/Users/lisa/Documents/GitHub/gen2-longit/diet_log_analyses/daily_diet_coding.xlsx`
- Modified: 2026-10-18 20:53
- Size: 203,360 bytes
- SHA-256: `bc1c8859c84a1c29fcab93c0c0d2754f0a1808ec208f51d5cd0756e05abed299`
- Profiled: 2026-10-18 20:54 by `diet_log_analyses/scripts/profile_inputs.py`

Sheets (7): `README`, `daily_diet_coding`, `source_diet_text`, `ingredient_lexicon`, `needs_review`, `collapse_groups`, `informative_changes`

## Sheet `README`

- 62 rows x 1 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| daily_diet_coding.xlsx | str | 10 | 52 | (assumed): 3 | e.g. Coding of free-text daily diet logs (We…; Tabs; daily_diet_coding: one row per separate…; source_diet_text: original free text pe… |

## Sheet `daily_diet_coding`

- 1461 rows x 10 columns

- Key Day_key + Entry_no: unique

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | int | 0 | 19 | — | 1 (109); 10 (25); 12 (64); 13 (86); 14 (102); 15 (66); 16 (90); 17 (60); 18 (112); 19 (56); 20 (80); 21 (78); 3 (103); 4 (62); 5 (70); 6 (85); 7 (52); 8 (83); 9 (78) |
| Date (MM-DD) | str | 0 | 17 | — | 08-03 (66); 08-04 (81); 08-05 (97); 08-06 (75); 08-07 (65); 08-08 (69); 08-09 (61); 08-10 (141); 08-11 (133); 08-12 (130); 08-13 (97); 08-14 (93); 08-15 (90); 08-16 (102); 08-17 (70); 08-18 (59); 08-19 (32) |
| Entry_no | int | 0 | 27 | — | range 1–27; e.g. 1; 2; 3; 4 |
| Time/meal as logged | str | 866 | 57 | — | e.g. 7:30; 9am; 11am; 2pm |
| Food entry (as logged) | str | 0 | 992 | — | e.g. decaf coffee; croissant omelette cheese and lamb saus…; peanut dressing cole slaw Trader Joe's …; 3 choc PB cups from TJ's |
| Ingredients | str | 0 | 596 | (assumed): 522 | e.g. coffee; wheat (assumed); butter (assumed); egg;…; cabbage; carrot (assumed); peanut; whea…; cacao; peanut; cow milk (assumed); suga… |
| Species (scientific name) | str | 0 | 549 | (assumed): 520 | e.g. Coffea arabica (species); Gallus gallus (species); Bos taurus (sp…; Brassica oleracea var. capitata (variet…; Theobroma cacao (species); Arachis hypo… |
| Marker that can detect it | str | 0 | 23 | — | 12SV5 (199); 12SV5 (fish part only) (1); 12SV5 (fish part only); trnL (1); 12SV5; none (3); 12SV5; none; trnL (5); 12SV5; trnL (105); 12SV5; trnL; none (21); none (29); none; 12SV5 (2); none; 12SV5; trnL (3); none; trnL (4); none; trnL; 12SV5 (4); trnL (738); trnL / 12SV5 (9); trnL / 12SV5; trnL (3); trnL; 12SV5 (174); trnL; 12SV5 (fish part only) (1); trnL; 12SV5 (fish part only); 12SV5 (1); trnL; 12SV5; none (57); trnL; none (68); trnL; none; 12SV5 (28); trnL; unknown (1); unknown (4) |
| Needs review | str | 1341 | 20 | — | unspecified: beans (unspecified) (7); unspecified: beans (unspecified), mixed… (1); unspecified: berries (mixed) (3); unspecified: fish (12); unspecified: fruit (unspecified) (8); unspecified: grain cereal (15); unspecified: grain-free cereal (2); unspecified: jam (6); unspecified: mixed vegetables (28); unspecified: nuts (unspecified) (4); unspecified: plant-based mince (1); unspecified: protein powder (12); unspecified: seafood (mixed) (4); unspecified: shellfish, mixed vegetables (1); unspecified: stone fruit (1); unspecified: stone fruit, berries (mixe… (1); unspecified: trail mix (4); unspecified: unknown (5); unspecified: vegan caesar dressing (3); unspecified: white fish (2) |
| Day_key | str | 0 | 167 | — | e.g. 1_08-03; 1_08-04; 1_08-05; 1_08-06 |

## Sheet `source_diet_text`

- 167 rows x 6 columns

- Key Subject_ID + Date (MM-DD): unique

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | int | 0 | 19 | — | 1 (9); 10 (4); 12 (9); 13 (8); 14 (8); 15 (8); 16 (10); 17 (7); 18 (10); 19 (10); 20 (10); 21 (8); 3 (10); 4 (10); 5 (8); 6 (10); 7 (9); 8 (10); 9 (9) |
| Date (MM-DD) | str | 0 | 17 | — | 08-03 (8); 08-04 (9); 08-05 (9); 08-06 (9); 08-07 (8); 08-08 (8); 08-09 (8); 08-10 (16); 08-11 (17); 08-12 (15); 08-13 (10); 08-14 (10); 08-15 (10); 08-16 (10); 08-17 (9); 08-18 (7); 08-19 (4) |
| Event_name | str | 0 | 10 | — | Day 01 ingestion  (18); Day 02 ingestion (18); Day 03 ingestion (19); Day 04 ingestion (19); Day 05 ingestion (18); Day 06 ingestion (18); Day 07 ingestion (17); Day 08 (16); Day 09 (14); Day 10 (10) |
| Diet (original free text) | str | 0 | 167 | — | e.g. 7:30 decaf coffee 9am a few bites of a …; 6:15 decaf coffee 8am croissant sandwic…; 7:15am decaf coffee 7:45am croissant sa…; 8/6: 6:15 decaf coffee Breakfast asiago… |
| n_coded_entries | — | 167 | 0 | — | e.g.  |
| Day_key | str | 0 | 167 | — | e.g. 1_08-03; 1_08-04; 1_08-05; 1_08-06 |

## Sheet `ingredient_lexicon`

- 227 rows x 31 columns

- Key Ingredient: unique

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Ingredient | str | 0 | 227 | — | e.g. acai; agave; almond; almond milk |
| Species (scientific name) | str | 0 | 183 | (assumed): 2 | e.g. Euterpe oleracea; Agave spp.; Prunus dulcis; mixed botanicals (unspecified) |
| Genus | str | 27 | 128 | — | e.g. Euterpe; Agave; Prunus; Engraulis |
| Family | str | 22 | 85 | — | e.g. Arecaceae; Asparagaceae; Rosaceae; Engraulidae |
| Order | str | 20 | 63 | — | e.g. Arecales; Asparagales; Rosales; Clupeiformes |
| Class | str | 17 | 28 | — | e.g. Liliopsida; Magnoliopsida; Actinopteri; Mammalia |
| Taxonomy source (higher ranks) | str | 0 | 5 | — | e.g. Claude's general taxonomic knowledge (A…; n/a (no single taxon); Finest group from needs_review (my assi…; Lab DADA2 meat feature_data.txt (projec… |
| Marker that can detect it | str | 0 | 6 | — | 12SV5 (33); 12SV5 (fish part only) (1); none (26); trnL (165); trnL / 12SV5 (1); unknown (1) |
| Notes (resolution / DNA caveats) | str | 93 | 84 | — | e.g. refined sweetener: little DNA; Prunus may not be separable from other …; processed: little DNA; distilled liqueur: no DNA expected |
| Source of species assignment | str | 0 | 2 | — | General taxonomy knowledge; not yet che… (48); Petrone 2025 Table S5 (same genus/speci… (179) |
| Genus/family assigned in your DADA2 weeklong outp… | str | 0 | 4 | — | genus/family in lab DADA2 output (143); n/a (37); not found in lab DADA2 output (37); some genera in lab DADA2 output (10) |
| Rows using it (at build time) | int | 0 | 47 | — | range 0–286; e.g. 4; 1; 5; 0 |
| Informative for sequencing? (Yes / Uncertain / No) | str | 0 | 3 | — | No (35); Uncertain (50); Yes (142) |
| Reason category | str | 0 | 12 | — | Composite product (5); Distilled (7); Hydrolysed / isolated / fat (5); Low DNA (2); No food DNA (2); No marker in pipeline (17); Partly unspecified (3); Processed: DNA reduced (15); Refined / purified (5); Trace amount (11); Unspecified taxon (13); Whole or lightly processed food (142) |
| Reasoning | str | 0 | 100 | (assumed): 3 | e.g. Whole or lightly processed plant food, …; Refined or purified product: little DNA…; Whole or lightly processed plant food, …; Filtered nut slurry: DNA reduced. |
| Collapse group(s) (sequencing cannot separate) | str | 173 | 23 | — | Apple + pear (2); Apple + pear (via a component of this p… (1); Brassica oleracea cultivars (5); Carrot + parsley + cumin (Apiaceae) (3); Carrot + parsley + cumin (Apiaceae) (vi… (1); Onion vs leek (2); Other Apiaceae (possible) (2); Potato + goji berry + other nightshades (1); Potato + goji berry + other nightshades… (1); Potato + goji berry + other nightshades… (1); Prunus species (6); Rice (conflicting) (3); Rice (conflicting) (via a component of … (2); Soybean + guar bean (10); Soybean + guar bean (via a component of… (2); Strawberry + raspberry/blackberry (3); Strawberry + raspberry/blackberry (via … (1); Tomato / eggplant vs potato (2); Tomato / eggplant vs potato (via a comp… (1); Wheat + rye (1); Wheat + rye (via a component of this pr… (1); Wheat + rye (via a component of this pr… (1); Wheat + rye (via a component of this pr… (2) |
| Other lexicon ingredients in the same group | str | 173 | 39 | — | e.g. cherry, peach, plum, stone fruit [named…; asian pear; apple; blackberry, raspberry, strawberry [name… |
| Label sequencing is expected to report | str | 0 | 27 | — | e.g. Own species/genus label expected only i…; Prunus (genus); none (no marker); Unknown - run the 12SV5 reference throu… |
| Collapse evidence (source) | str | 156 | 19 | — | e.g. Taberlet 2007: P6 cannot distinguish mo…; Reese 2019 Discussion: Malus and Pyrus …; Petrone 2025 Table S4 lists this specie…; Petrone 2023: a second Rosaceae variant… |
| Collapse evidence strength | str | 0 | 16 | — | e.g. Not documented - species-level label on…; Documented: identical published sequenc…; Not applicable (log names no single tax…; Unknown (animal): needs the 12SV5 refer… |
| Informative: value before 17 Oct 2026 review | str | 0 | 3 | — | No (47); Uncertain (38); Yes (142) |
| Informative: evidence basis | str | 0 | 14 | — | e.g. Marker design (land-plant trnL), whole …; General knowledge - processing (no sour…; General knowledge - processing/amount (…; Log names no single taxon (unspecified … |
| Informative: review note | str | 137 | 34 | — | e.g. Moved from No to Uncertain: the claim t…; Rosaceae (apple/pear) prevalence 17 (Pe…; Beef/cow prevalence 22 (Petrone 2025, T…; Peppers reliably detected by FoodSeq an… |
| Fermented? (Yes / No / Variable / Unknown) | str | 0 | 4 | — | No (199); Unknown (2); Variable (12); Yes (14) |
| Fermented: reasoning | str | 0 | 68 | — | e.g. Plant (or fungal) food eaten fresh, coo…; Water extract of almonds; no fermentati…; Alcoholic infusion in a distilled spiri…; Salt-cured and matured by enzymatic and… |
| Fibrous? (Yes / No / Variable / Unknown) | str | 0 | 4 | — | No (80); Unknown (3); Variable (10); Yes (134) |
| Fibrous: reasoning | str | 0 | 182 | — | e.g. ≈2 g fibre and ≈70 kcal per 100 g (froz…; ≈0 g fibre and ≈310 kcal per 100 g (syr…; ≈12.5 g fibre and ≈579 kcal per 100 g (…; Liquid or condiment: about 0.3 g fibre/… |
| Likely live microbes? (Yes / Variable / No / Unkn… | str | 0 | 4 | — | No (209); Unknown (2); Variable (13); Yes (3) |
| Live microbes: reasoning | str | 0 | 32 | — | e.g. Not a fermented food, so no fermentatio…; Distilled-spirit infusion; no viable mi…; Salt-cured or canned; not a live-cultur…; Vinegar is listed among fermented foods… |
| Dairy? (Yes / No / Variable / Unknown) | str | 0 | 3 | — | No (215); Variable (1); Yes (11) |
| Dairy: reasoning | str | 0 | 15 | — | Animal food, but not a milk product (6); Butter is made from milk fat (1); Cheese is made from milk (1); Fermented milk (1); Fresh milk cheese (1); Goat milk cheese (1); Made from milk and cream (1); May be whey (dairy) or plant protein; t… (1); Milk (1); Milk fat (1); Milk protein (by-product of cheese maki… (1); Not a milk product (205); Plant-based alternative; contains no mi… (4); Sheep/goat milk cheese (1); Soft milk cheese (1) |

## Sheet `needs_review`

- 120 rows x 11 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | int | 0 | 18 | — | 1 (7); 12 (8); 13 (11); 14 (7); 15 (5); 16 (13); 17 (4); 18 (5); 19 (2); 20 (12); 21 (4); 3 (6); 4 (12); 5 (1); 6 (11); 7 (7); 8 (1); 9 (4) |
| Date (MM-DD) | str | 0 | 17 | — | 08-03 (3); 08-04 (5); 08-05 (3); 08-06 (3); 08-07 (7); 08-08 (9); 08-09 (9); 08-10 (6); 08-11 (7); 08-12 (8); 08-13 (14); 08-14 (8); 08-15 (6); 08-16 (14); 08-17 (9); 08-18 (6); 08-19 (3) |
| Entry_no | int | 0 | 14 | — | 1 (17); 10 (3); 11 (4); 12 (1); 13 (1); 14 (1); 2 (10); 3 (19); 4 (18); 5 (13); 6 (11); 7 (12); 8 (6); 9 (4) |
| Food entry (as logged) | str | 0 | 100 | — | e.g. paella with mixed seafood; steamed vegetables; jams; jam |
| Ingredients | str | 0 | 65 | (assumed): 44 | e.g. rice; seafood (mixed); olive oil (assum…; mixed vegetables; jam; berries (mixed) |
| What is unspecified | str | 0 | 20 | — | unspecified: beans (unspecified) (7); unspecified: beans (unspecified), mixed… (1); unspecified: berries (mixed) (3); unspecified: fish (12); unspecified: fruit (unspecified) (8); unspecified: grain cereal (15); unspecified: grain-free cereal (2); unspecified: jam (6); unspecified: mixed vegetables (28); unspecified: nuts (unspecified) (4); unspecified: plant-based mince (1); unspecified: protein powder (12); unspecified: seafood (mixed) (4); unspecified: shellfish, mixed vegetables (1); unspecified: stone fruit (1); unspecified: stone fruit, berries (mixe… (1); unspecified: trail mix (4); unspecified: unknown (5); unspecified: vegan caesar dressing (3); unspecified: white fish (2) |
| Finest assignment (item → taxon) | str | 0 | 20 | — | beans (unspecified) → Fabaceae (7); beans (unspecified) → Fabaceae \| mixed… (1); berries (mixed) → Eudicots (3); fish → Actinopterygii (ray-finned fishe… (12); fruit (unspecified) → Angiospermae (flo… (8); grain cereal → Poaceae (15); grain-free cereal → Angiospermae (flowe… (2); jam → Angiospermae (flowering plants) (6); mixed vegetables → Angiospermae (flower… (28); nuts (unspecified) → Angiospermae (flow… (4); plant-based mince → Viridiplantae (plan… (1); protein powder → Eukaryota (12); seafood (mixed) → Animalia (Metazoa) (4); shellfish → Protostomia (molluscs and c… (1); stone fruit → Prunus (1); stone fruit → Prunus \| berries (mixed)… (1); trail mix → Angiospermae (flowering pla… (4); unknown → Not assignable (5); vegan caesar dressing → Viridiplantae (… (3); white fish → Actinopterygii (ray-finned… (2) |
| Taxonomic rank | str | 0 | 10 | — | clade (55); clade \| clade (1); class (14); domain (12); family (22); family \| clade (1); genus (1); genus \| clade (1); kingdom (8); none (5) |
| Confidence | str | 0 | 4 | — | Certain (24); Probable (88); Probable \| Probable (3); n/a (5) |
| Marker that could detect it | str | 0 | 7 | — | 12SV5 (14); 12SV5 (fish only; invertebrates not cov… (4); none (5); none (invertebrates not covered by 12SV… (1); trnL (82); trnL or 12SV5, depending on source (12); trnL \| trnL (2) |
| Note | str | 0 | 20 | — | e.g. Fish, shellfish and cephalopods are all…; Common vegetables are flowering plants;…; Fruit-based; fruit type unknown. Sugar-…; Strawberry, raspberry, blueberry, cranb… |

## Sheet `collapse_groups`

- 18 rows x 6 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Group | str | 1 | 17 | — | Animal foods: no published list of coll… (1); Apple + pear (1); Brassica oleracea cultivars (1); Carrot + parsley + cumin (Apiaceae) (1); Notes (1); Onion vs leek (1); Other Apiaceae (possible) (1); Potato + goji berry + other nightshades (1); Prunus species (1); Rice (conflicting) (1); Rules for adding a group: it needs a pu… (1); Soybean + guar bean (1); Strawberry + raspberry/blackberry (1); The apple/pear variant and the strawber… (1); Tomato / eggplant vs potato (1); Verify with the lab reference: run each… (1); Wheat + rye (1) |
| Lexicon ingredients in the group | str | 6 | 12 | — | almond, almond milk, cherry, peach, plu… (1); apple, asian pear (1); black soybean, edamame, miso, natto, so… (1); blackberry, raspberry, strawberry (1); broccoli, brussels sprouts, cabbage, ca… (1); carrot, cumin, parsley (1); celery, dill (1); eggplant, tomato (1); glutinous rice, rice, soju (1); leek, onion (1); potato (1); wheat (1) |
| Partner foods named in papers but not in lexicon | str | 11 | 7 | — | apricot (1); bramble berries (1); guar bean (guar gum) (1); kohlrabi, collards (1); parsnip (1); rye (Secale cereale) (1); tomatillo, tamarillo, cutleaf groundche… (1) |
| Label sequencing is expected to report | str | 6 | 12 | — | 'guar bean, soybean' (Aqeel 2025 label) (1); Apiaceae (Aqeel 2025 label: 'carrot and… (1); Brassica oleracea (Aqeel 2025 label: 'c… (1); Own taxon expected (1-base difference f… (1); Own taxon expected (1-base difference) (1); Poaceae (family) (1); Possibly Apiaceae (1); Possibly Poaceae with wheat + rye; othe… (1); Prunus (genus) (1); Rosaceae (a second, separate variant); … (1); Rosaceae (one sequence variant) (1); Shared 'potato family' variant (Aqeel 2… (1) |
| Evidence (source) | str | 6 | 12 | — | e.g. Taberlet 2007 Table 4: identical P6 seq…; Reese 2019 Discussion: rice, rye and wh…; Reese 2019 Discussion: Malus and Pyrus …; Petrone 2023: a second Rosaceae variant… |
| Evidence strength | str | 6 | 6 | — | Conflicting evidence - check the lab re… (1); Documented: identical published sequenc… (1); Documented: identical published sequenc… (1); Documented: shared label in FoodSeq pap… (6); Near-identical (1 base) - usually separ… (2); Possible: same family as a documented g… (1) |

## Sheet `informative_changes`

- 16 rows x 6 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Ingredient | str | 0 | 16 | — | agave (1); bourbon (1); butter (1); collagen (1); gelatin (1); limoncello (1); maple syrup (1); nori (1); pea protein (1); seaweed (1); soju (1); sugar (1); tapioca (1); vegetable oil (1); whey (1); whiskey (1) |
| Before | str | 0 | 2 | — | No (14); Uncertain (2) |
| After | str | 0 | 2 | — | No (2); Uncertain (14) |
| Reason category (unchanged unless noted) | str | 0 | 4 | — | Distilled (4); Hydrolysed / isolated / fat (5); Partly unspecified (2); Refined / purified (5) |
| Why changed | str | 0 | 2 | — | e.g. Moved from No to Uncertain: the claim t…; Moved from Uncertain to No on published… |
| Evidence basis | str | 0 | 3 | — | General knowledge - processing (no sour… (13); Marker design - no marker covers this g… (2); Published: Jeffrey 2026 preprint (citin… (1) |

