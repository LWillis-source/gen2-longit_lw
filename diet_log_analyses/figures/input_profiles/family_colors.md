# family_colors

- File: `/Users/lisa/Documents/GitHub/gen2-longit/1-data/Family_colors.xlsx`
- Modified: 2026-10-09 14:07
- Size: 53,653 bytes
- SHA-256: `60854cb0279d00fecc948b599593fd1d4cad79028a80326ed6554f07b80f73d2`
- Profiled: 2026-10-18 21:01 by `diet_log_analyses/scripts/profile_inputs.py`

Sheets (6): `SILVA`, `Green-genes`, `Meat`, `Plants`, `Plant_common_names`, `MAGs`

## Sheet `SILVA`

- 159 rows x 6 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Kingdom | str | 0 | 4 | NA: 1 | Archaea (2); Bacteria (155); Cyanobacteriota (1); NA (1) |
| Phylum | str | 0 | 23 | NA: 2 | Actinomycetota (26); Aquificota (1); Bacillota (42); Bacteroidota (19); Bdellovibrionota (1); Campylobacterota (2); Chlamydiota (1); Cyanobacteriia (1); Cyanobacteriota (5); Deferribacterota (1); Deinococcota (2); Fusobacteriota (2); Halobacteriota (1); Methanobacteriota (1); Myxococcota (1); NA (2); Patescibacteria (4); Planctomycetota (1); Pseudomonadota (39); Spirochaetota (1); Synergistota (1); Thermodesulfobacteriota (1); Verrucomicrobiota (4) |
| Class | str | 0 | 34 | NA: 4 | e.g. Halobacteria; Methanobacteria; Acidimicrobiia; Actinobacteria |
| Order | str | 0 | 75 | NA: 13 | e.g. Halobacterales; Methanobacteriales; Microtrichales; Actinomycetales |
| Family | str | 0 | 135 | NA: 25 | e.g. Haloferacaceae; Methanobacteriaceae; Iamiaceae; Actinomycetaceae |
| Color | str | 0 | 157 | — | e.g. DBDB8D; 00002B; 232308; 9EC1FF |

## Sheet `Green-genes`

- 327 rows x 6 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Kingdom | str | 0 | 4 | — | Unassigned (1); k__ (1); k__Archaea (4); k__Bacteria (321) |
| Phylum | str | 0 | 33 | — | e.g. p__Firmicutes; p__; p__Crenarchaeota; p__Euryarchaeota |
| Class | str | 0 | 84 | NA: 1 | e.g. c__Bacilli; c__; c__Thaumarchaeota; c__Halobacteria |
| Order | str | 0 | 139 | NA: 2 | e.g. NA; o__; o__Nitrososphaerales; o__Halobacteriales |
| Family | str | 0 | 214 | NA: 5 | e.g. NA; f__; f__Nitrososphaeraceae; f__Halobacteriaceae |
| Color | str | 0 | 320 | — | e.g. 666666; 000000; FF0000; 00FF00 |

## Sheet `Meat`

- 35 rows x 6 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Kingdom | str | 0 | 1 | — | Eukaryota (35) |
| Phylum | str | 0 | 2 | NA: 1 | Chordata (34); NA (1) |
| Class | str | 0 | 4 | NA: 2 | Actinopteri (18); Aves (3); Mammalia (12); NA (2) |
| Order | str | 0 | 18 | NA: 6 | Anabantiformes (1); Anguilliformes (1); Anseriformes (1); Artiodactyla (5); Carangiformes (1); Carnivora (4); Clupeiformes (2); Gadiformes (1); Galliformes (1); Istiophoriformes (1); NA (6); Osmeriformes (1); Perciformes (3); Primates (1); Rodentia (1); Salmoniformes (1); Scombriformes (2); Siluriformes (2) |
| Family | str | 0 | 28 | NA: 8 | e.g. Channidae; Anguillidae; Carangidae; Clupeidae |
| Color | str | 0 | 35 | — | e.g. 4682B4; 6A5ACD; CD853F; 8B795E |

## Sheet `Plants`

- 146 rows x 8 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Kingdom | str | 0 | 1 | NA: 146 | NA (146) |
| Phylum | str | 0 | 1 | NA: 146 | NA (146) |
| Class | str | 0 | 1 | NA: 146 | NA (146) |
| Order | str | 0 | 1 | NA: 146 | NA (146) |
| Family | str | 0 | 1 | NA: 146 | NA (146) |
| Genus | str | 0 | 146 | NA: 1 | e.g. Abelmoschus; Abutilon; Achillea; Actinidia |
| Common_name | str | 0 | 146 | NA: 1 | e.g. Okra; Flowering Maple; Yarrow; Kiwi |
| Color | str | 0 | 146 | — | e.g. 8B4513; D45E9B; 2F4F4F; 556B2F |

## Sheet `Plant_common_names`

- 224 rows x 3 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Genus | str | 0 | 146 | NA: 1 | e.g. Abelmoschus; Abutilon; Achillea; Actinidia |
| Species | str | 0 | 149 | NA: 67 | e.g. esculentus; NA; theophrasti; arguta |
| Common_name | str | 0 | 191 | NA: 1 | e.g. Okra; Velvetleaf; Yarrow; Hardy Kiwi |

## Sheet `MAGs`

- 81 rows x 2 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Family | str | 0 | 81 | NA: 1 | e.g. f__Coriobacteriaceae; f__Staphylococcaceae; NA; f__Veillonellaceae |
| Color | str | 0 | 80 | — | e.g. 131313; 444444; 000000; 0000CC |

