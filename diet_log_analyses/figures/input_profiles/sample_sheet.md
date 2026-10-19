# sample_sheet

- File: `/Users/lisa/Documents/GitHub/gen2_capScan_sanitized00/data/work-in-progress-meta/LONGITWeeklong-samplesheet-FINAL.xlsx`
- Modified: 2026-10-17 11:12
- Size: 55,527,957 bytes
- SHA-256: `8da2c38411675ea165e96fa06b3cf2c64a93dae42103f8c591ab13fedd9b6629`
- Profiled: 2026-10-18 21:01 by `diet_log_analyses/scripts/profile_inputs.py`

Sheets (17): `Kit_ID`, `Sample_ID`, `PANAS`, `decontamination`, `humann`, `metaphlan`, `Orientation`, `Pre-ingestion-PSS`, `Pre-ingestion-RomeIV`, `Pre-ingestion-Lifestyle`, `Pre-ingestion-GSRS-IBS`, `Daily-diet`, `Daily-PANAS`, `Daily-Nutrient`, `Food-category`, `Questions-for-Leila`, `Study_notes`

## Sheet `Kit_ID`

- 178 rows x 17 columns

- Key Kit_ID: unique

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Kit_ID | str | 0 | 178 | — | e.g. LS100; LS101; LS102; LS103 |
| Study | str | 0 | 1 | — | LONGITWeeklong (178) |
| Subject_ID | str | 0 | 20 | — | 01 (17); 03 (8); 04 (8); 05 (8); 06 (8); 07 (9); 08 (10); 09 (8); 10 (8); 11 (10); 12 (10); 13 (8); 14 (7); 15 (8); 16 (8); 17 (8); 18 (8); 19 (9); 20 (10); 21 (8) |
| Diagnosis | str | 0 | 1 | — | Healthy (178) |
| Ingestion_date | str | 0 | 19 | NR: 11 | 250731 (10); 250802 (1); 250803 (9); 250804 (10); 250805 (11); 250806 (12); 250807 (16); 250808 (12); 250809 (10); 250810 (10); 250811 (10); 250812 (11); 250813 (10); 250814 (12); 250815 (10); 250816 (8); 250817 (4); 250818 (1); NR (11) |
| Ingestion_time | str | 0 | 101 | NR: 11 | e.g. 22:45; 22:05; 21:10; NR |
| Collection_date | str | 0 | 22 | NR: 18 | 250801 (1); 250802 (4); 250803 (4); 250804 (2); 250805 (5); 250806 (12); 250807 (4); 250808 (16); 250809 (12); 250810 (11); 250811 (14); 250812 (8); 250813 (9); 250814 (9); 250815 (6); 250816 (16); 250817 (13); 250818 (6); 250819 (5); 250820 (2); 250822 (1); NR (18) |
| Collection_time | str | 0 | 89 | NR: 19 | e.g. 21:45; 08:30; 16:30; NR |
| Transit_time_h | str | 0 | 144 | NR: 19 | e.g. 71; 58.42; 115.33; NR |
| Sample_fate | str | 0 | 2 | — | fresh (19); frozen (159) |
| BSS | str | 0 | 9 | NA: 3, NR: 20 | 1 (3); 2 (18); 3 (18); 4 (75); 5 (16); 6 (24); 7 (1); NA (3); NR (20) |
| Sampling_no | str | 0 | 20 | — | 0 (19); 1 (20); 2 (20); 3 (20); 3.5 (5); 4 (20); 4.5 (1); 5 (20); 5.5 (1); 6 (20); 6.5 (5); 7 (19); 8 (1); CapscanExtra1 (1); CapscanExtra2 (1); CapscanExtra3 (1); ExtraSaliva (1); StoolExtra1 (1); StoolExtra2 (1); StoolNoCapscan (1) |
| Saliva | str | 0 | 168 | — | e.g. LS1000; LS1001; LS1002; LS1003 |
| Cap_R1 | str | 0 | 164 | — | e.g. LS1168; LS1171; LS1174; No-sample |
| Cap_R2 | str | 0 | 123 | — | e.g. LS1169; LS1172; LS1175; No-sample |
| Cap_R3 | str | 0 | 63 | — | e.g. No-sample; LS1173; LS1227; LS1230 |
| Stool | str | 0 | 137 | — | e.g. LS1672; LS1673; LS1674; No-sample |

## Sheet `Sample_ID`

- 654 rows x 22 columns

- Key Sample_ID: unique

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Sample_ID | str | 0 | 654 | — | e.g. LS1636; LS1633; LS1890; LS1615 |
| Kit_ID | str | 0 | 193 | — | e.g. LS256; LS255; LS283; LS249 |
| Cap_ID | str | 0 | 162 | NA: 307 | e.g. D2D6D; D606E; TBD; 7839E |
| Tip_color | str | 0 | 2 | NA: 307 | NA (307); white (347) |
| Sample_origin | str | 0 | 3 | — | capscan (347); saliva (167); stool (140) |
| Region | str | 0 | 5 | — | R1 (163); R2 (122); R3 (62); saliva (167); stool (140) |
| pH | str | 0 | 11 | NM: 312 | 5.5 (94); 5.8 (63); 6 (32); 6.2 (31); 6.4 (13); 6.6 (6); 6.8 (12); 7 (1); 7.6 (2); <5.5 (88); NM (312) |
| gDNA_concentration | str | 0 | 624 | NM: 5 | e.g. 0.09386; 0.09638; 0.09656; 0.09852 |
| Prediction | str | 0 | 5 | NA: 314 | AC (28); NA (314); SI (201); SI_dark (66); SI_light (45) |
| Drops | str | 0 | 26 | NA: 307 | e.g. 10; 6; 9; 8 |
| GS | str | 0 | 4 | — | N (596); Y (55); Y_1Copy (2); Y_1copy (1) |
| A_SEQ | str | 0 | 65 | — | e.g. Y; Y_141mg; Y_138mg; Y_172mg |
| B_MB | str | 0 | 79 | — | e.g. Y; less_20uL; N; Y_169mg |
| E_BA | str | 0 | 85 | — | e.g. Y; less_25uL; less_30uL; N |
| D_PL | str | 1 | 105 | — | e.g. Y; N; Y_194mg; Y_93mg |
| pH_type | str | 0 | 2 | NA: 307 | NA (307); strips (347) |
| Processing_date | int | 0 | 21 | — | 250805 (2); 250806 (22); 250807 (4); 250812 (34); 250813 (24); 250814 (8); 250815 (41); 250820 (47); 250821 (32); 250825 (52); 250827 (13); 250828 (49); 250829 (36); 250904 (37); 250914 (15); 250915 (46); 250916 (93); 250917 (27); 250918 (54); 251008 (3); 280821 (15) |
| Notes | str | 0 | 48 | NA: 542 | e.g. NA; Capscan5; Capscan6E, no paired stool; Capscan3E |
| No | int | 0 | 654 | — | range 1–678; e.g. 482; 479; 663; 467 |
| Capscan_ID | str | 0 | 162 | NA: 307 | e.g. D2D6DF07530104E0; D606E007530104E0; TBD; 7839E107530104E0 |
| 16S_filename | str | 0 | 650 | — | e.g. sample_16S-P10-B2-B03-L3_Run15-LONGITWe…; sample_16S-P10-B2-A12-L3_Run15-LONGITWe…; sample_16S-P10-B2-E05-L3_Run15-LONGITWe…; sample_16S-P10-B2-A02-L3_Run15-LONGITWe… |
| MGX_filename | str | 0 | 632 | NA: 19 | e.g. P4-B03-CapScan4-LS1636-21-Cap4-R1; P4-A12-CapScan4-LS1633-21-Cap3-R1; P4-E05-CapScan4-LS1890-01; P4-A02-CapScan4-LS1615-20-Cap5-R1 |

## Sheet `PANAS`

- 170 rows x 25 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Survey | str | 0 | 10 | — | day_10_arm_1 (10); day_1_ingestion_arm_1 (19); day_2_ingestion_arm_1 (19); day_3_ingestion_arm_1 (20); day_4_ingestion_arm_1 (19); day_5_ingestion_arm_1 (18); day_6_ingestion_arm_1 (18); day_7_ingestion_arm_1 (17); day_8_arm_1 (16); day_9_arm_1 (14) |
| Subject_ID | str | 0 | 20 | — | 01 (9); 03 (10); 04 (10); 05 (8); 06 (10); 07 (9); 08 (10); 09 (9); 10 (4); 11 (3); 12 (9); 13 (8); 14 (8); 15 (8); 16 (10); 17 (7); 18 (10); 19 (10); 20 (10); 21 (8) |
| Day | str | 0 | 10 | — | 01 (19); 02 (19); 03 (20); 04 (19); 05 (18); 06 (18); 07 (17); 08 (16); 09 (14); 10 (10) |
| Interested | int | 0 | 5 | — | 1 (4); 2 (43); 3 (78); 4 (40); 5 (5) |
| Distressed | int | 0 | 5 | — | 1 (74); 2 (59); 3 (25); 4 (11); 5 (1) |
| Excited | int | 0 | 5 | — | 1 (23); 2 (45); 3 (57); 4 (41); 5 (4) |
| Upset | int | 0 | 4 | — | 1 (122); 2 (28); 3 (15); 4 (5) |
| Strong | int | 0 | 5 | — | 1 (43); 2 (46); 3 (52); 4 (25); 5 (4) |
| Guilty | int | 0 | 4 | — | 1 (136); 2 (28); 3 (5); 5 (1) |
| Scared | int | 0 | 4 | — | 1 (140); 2 (27); 3 (2); 4 (1) |
| Hostile | int | 0 | 3 | — | 1 (150); 2 (18); 3 (2) |
| Enthusiastic | int | 0 | 5 | — | 1 (18); 2 (63); 3 (52); 4 (31); 5 (6) |
| Proud | int | 0 | 5 | — | 1 (47); 2 (52); 3 (45); 4 (23); 5 (3) |
| Irritable | int | 0 | 5 | — | 1 (106); 2 (40); 3 (19); 4 (4); 5 (1) |
| Alert | int | 0 | 5 | — | 1 (48); 2 (57); 3 (45); 4 (19); 5 (1) |
| Ashamed | int | 0 | 4 | — | 1 (147); 2 (14); 3 (8); 5 (1) |
| Inspired | int | 0 | 5 | — | 1 (44); 2 (66); 3 (33); 4 (24); 5 (3) |
| Nervous | int | 0 | 4 | — | 1 (97); 2 (48); 3 (17); 4 (8) |
| Determined | int | 0 | 5 | — | 1 (36); 2 (52); 3 (47); 4 (26); 5 (9) |
| Attentive | int | 0 | 5 | — | 1 (33); 2 (50); 3 (59); 4 (26); 5 (2) |
| Jittery | int | 0 | 4 | — | 1 (151); 2 (13); 3 (5); 5 (1) |
| Active | int | 0 | 5 | — | 1 (38); 2 (48); 3 (53); 4 (23); 5 (8) |
| Afraid | int | 0 | 4 | — | 1 (149); 2 (19); 3 (1); 4 (1) |
| Positive_affect_score | int | 0 | 35 | — | range 10–46; e.g. 39; 40; 32; 46 |
| Negative_affect_score | int | 0 | 17 | — | 10 (43); 11 (24); 12 (19); 13 (18); 14 (10); 15 (13); 16 (10); 17 (11); 18 (8); 19 (2); 20 (4); 21 (2); 23 (2); 24 (1); 28 (1); 30 (1); 32 (1) |

## Sheet `decontamination`

- 630 rows x 7 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Sample_ID | str | 0 | 630 | — | e.g. LS1168; LS1169; LS1171; LS1172 |
| MGX_filename | str | 0 | 630 | — | e.g. P1-A01-CapScan1-LS1168-01-Cap0-R1; P1-A02-CapScan1-LS1169-01-Cap0-R2; P1-A03-CapScan1-LS1171-01-Cap1-R1; P1-A04-CapScan1-LS1172-01-Cap1-R2 |
| host | str | 0 | 1 | — | human (630) |
| total_reads | int | 0 | 630 | — | range 960–2.72097e+08; e.g. 2456886; 11696292; 200405; 40737595 |
| mapped_reads | int | 0 | 605 | — | range 13–5.53371e+07; e.g. 214; 685; 1290; 121 |
| mapped_rate_pct | float | 0 | 228 | — | range 0–92.35; e.g. 0.01; 0.64; 0.0; 0.16 |
| clean_reads | int | 0 | 630 | — | range 920–2.7208e+08; e.g. 2456661; 11695494; 199077; 40737178 |

## Sheet `humann`

- 630 rows x 10100 columns

- Wide sheet: first columns `Sample_ID`, `Filename`, `UNMAPPED`, `UNGROUPED`, `PF00001`; numeric cells 6,361,740 of 6,363,000

## Sheet `metaphlan`

- 630 rows x 1687 columns

- Wide sheet: first columns `Sample_ID`, `Filename`, `UNCLASSIFIED`, `Bacteria,Actinobacteria,Actinomycetia,Actinomycetales,Actinomycetaceae,Actinobaculum,Actinobaculum_sp_oral_taxon_183`, `Bacteria,Actinobacteria,Actinomycetia,Actinomycetales,Actinomycetaceae,Actinomyces,Actinomyces_bouchesdurhonensis`; numeric cells 1,061,550 of 1,062,810

## Sheet `Orientation`

- 20 rows x 16 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (1); 03 (1); 04 (1); 05 (1); 06 (1); 07 (1); 08 (1); 09 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 20 (1); 21 (1) |
| Age | int | 0 | 12 | — | 21 (1); 23 (2); 24 (1); 27 (1); 28 (4); 29 (2); 30 (2); 31 (1); 34 (1); 37 (1); 40 (3); 46 (1) |
| Sex | str | 0 | 2 | — | Female (10); Male (10) |
| Weight_lb | int | 0 | 16 | — | 114 (1); 125 (1); 126 (1); 130 (1); 133 (1); 135 (2); 136 (1); 140 (1); 142 (1); 144 (2); 145 (1); 150 (2); 155 (2); 165 (1); 178 (1); 245 (1) |
| Height_cm | int | 0 | 12 | — | 160 (1); 164 (1); 166 (2); 167 (2); 168 (3); 170 (3); 171 (1); 174 (1); 178 (2); 180 (2); 182 (1); 188 (1) |
| Medication_supplements | str | 0 | 9 | — | 2000 ug vitamin B12 once a week (1); Allegra, Folate, Magnesium (1); Atorvastatin (1); Levothyroxine 137 mcg,  Setlaking estra… (1); None (12); Vitamin Supplements, Wegovy. (1); Whole Foods multivitamin  Ketotifen fum… (1); multivitamins, calcium supplements (1); supplements: multivitamin, fish oil, bi… (1) |
| Medical_history | str | 1 | 8 | — | Atopic dermatitis, otitis media, pneumo… (1); D&C for fibroids 02/25  open myomectomy… (1); Giardia and pancreatic exocrine insuffi… (1); Hypothyroidism (1); None (12); Wisdom tooth removal 2-3 years ago (1); anal sphincterotomy surgery 3/26/25  (1); duodenal ulcer caused by H pylori infec… (1) |
| Last_antibiotic_date | str | 0 | 17 | — | 19950701 (1); 20010101 (1); 20020101 (1); 20151001 (1); 20180106 (1); 20210930 (1); 20220101 (1); 20220924 (1); 20230401 (1); 20230701 (1); 20230711 (1); 20240101 (1); 20240701 (1); 20250113 (1); 20250315 (1); 20250507 (1); None (4) |
| Antibiotic | str | 0 | 10 | — | 10 different types (1); AMPCCVA (1); Amoxicillin (4); Amoxycyclin (1); Augmentin (1); Ciprofloxacin (1); Doxycycline (1); Nil (1); None (4); Unsure (5) |
| Last_probiotic | str | 0 | 4 | — | 20200701 (1); 20220601 (1); 20250724 (1); None (17) |
| Probiotic | str | 0 | 4 | — | Kombucha, Greek Yoghurt (1); Lactobacillus (1); None (17); VSL-3 (1) |
| Colonoscopy | str | 0 | 2 | — | No (17); Yes (3) |
| Last_colonoscopy | str | 0 | 4 | — | 20211018 (1); 20220707 (1); 20250619 (1); None (17) |
| Colonoscopy_result | str | 0 | 4 | — | No polyps, some internal hemorrhoids (1); None (17); Normal (1); Normal  (1) |
| Record ID | int | 0 | 20 | — | 1 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 2 (1); 20 (1); 3 (1); 4 (1); 5 (1); 6 (1); 7 (1); 8 (1); 9 (1) |
| Event Name | str | 0 | 1 | — | Orientation (20) |

## Sheet `Pre-ingestion-PSS`

- 20 rows x 35 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (1); 03 (1); 04 (1); 05 (1); 06 (1); 07 (1); 08 (1); 09 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 20 (1); 21 (1) |
| 01 | int | 0 | 3 | — | 0 (1); 1 (13); 2 (6) |
| 02 | int | 0 | 4 | — | 0 (6); 1 (4); 2 (8); 3 (2) |
| 03 | int | 0 | 5 | — | 0 (1); 1 (5); 2 (6); 3 (5); 4 (3) |
| 04 | int | 0 | 3 | — | 2 (3); 3 (11); 4 (6) |
| 05 | int | 0 | 4 | — | 0 (1); 2 (8); 3 (7); 4 (4) |
| 06 | int | 0 | 4 | — | 0 (1); 1 (12); 2 (6); 3 (1) |
| 07 | int | 0 | 5 | — | 0 (1); 1 (1); 2 (6); 3 (8); 4 (4) |
| 08 | int | 0 | 4 | — | 1 (2); 2 (6); 3 (10); 4 (2) |
| 09 | int | 0 | 4 | — | 0 (6); 1 (8); 2 (3); 3 (3) |
| 10 | int | 0 | 4 | — | 0 (5); 1 (10); 2 (4); 3 (1) |
| Score | int | 0 | 12 | — | 10 (3); 11 (2); 14 (1); 16 (4); 17 (1); 19 (2); 23 (1); 24 (1); 5 (1); 6 (1); 7 (2); 8 (1) |
| Perceived_stress | str | 0 | 3 | — | Lmoderate (1); Low (10); Moderate (9) |
| Interested | str | 0 | 4 | — | A little (1); Extremely (3); Moderately (2); Quite a bit (14) |
| Distressed | str | 0 | 4 | — | A little (7); Moderately (2); Quite a bit (6); Very slightly or Not at all (5) |
| Excited | str | 0 | 4 | — | A little (1); Extremely (2); Moderately (6); Quite a bit (11) |
| Upset | str | 0 | 3 | — | A little (6); Moderately (3); Very slightly or Not at all (11) |
| Strong | str | 0 | 4 | — | A little (2); Moderately (8); Quite a bit (8); Very slightly or Not at all (2) |
| Guilty | str | 0 | 3 | — | A little (5); Moderately (2); Very slightly or Not at all (13) |
| Scared | str | 0 | 4 | — | A little (5); Moderately (1); Quite a bit (1); Very slightly or Not at all (13) |
| Hostile | str | 0 | 3 | — | A little (4); Moderately (1); Very slightly or Not at all (15) |
| Enthusiastic | str | 0 | 3 | — | A little (2); Moderately (5); Quite a bit (13) |
| Proud | str | 0 | 4 | — | A little (4); Extremely (1); Moderately (9); Quite a bit (6) |
| Irritable | str | 0 | 5 | — | A little (7); Extremely (1); Moderately (1); Quite a bit (3); Very slightly or Not at all (8) |
| Alert | str | 0 | 4 | — | A little (1); Moderately (8); Quite a bit (8); Very slightly or Not at all (3) |
| Ashamed | str | 0 | 3 | — | A little (3); Moderately (1); Very slightly or Not at all (16) |
| Inspired | str | 0 | 4 | — | A little (1); Extremely (1); Moderately (7); Quite a bit (11) |
| Nervous | str | 0 | 4 | — | A little (10); Moderately (3); Quite a bit (4); Very slightly or Not at all (3) |
| Determined | str | 0 | 5 | — | A little (1); Extremely (5); Moderately (5); Quite a bit (8); Very slightly or Not at all (1) |
| Attentive | str | 0 | 4 | — | A little (1); Extremely (1); Moderately (10); Quite a bit (8) |
| Jittery | str | 0 | 4 | — | A little (3); Moderately (2); Quite a bit (1); Very slightly or Not at all (14) |
| Active | str | 0 | 4 | — | A little (2); Extremely (3); Moderately (6); Quite a bit (9) |
| Afraid | str | 0 | 3 | — | A little (8); Quite a bit (1); Very slightly or Not at all (11) |
| Record ID | int | 0 | 20 | — | 1 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 2 (1); 20 (1); 3 (1); 4 (1); 5 (1); 6 (1); 7 (1); 8 (1); 9 (1) |
| Event Name | str | 0 | 1 | — | Pre-ingestion (20) |

## Sheet `Pre-ingestion-RomeIV`

- 20 rows x 26 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (1); 03 (1); 04 (1); 05 (1); 06 (1); 07 (1); 08 (1); 09 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 20 (1); 21 (1) |
| 01 | str | 0 | 1 | — | No (20) |
| 02 | — | 20 | 0 | — | e.g.  |
| 03 | — | 20 | 0 | — | e.g.  |
| 04 | — | 20 | 0 | — | e.g.  |
| 05 | str | 0 | 1 | — | No (20) |
| 06 | str | 0 | 2 | — | No (19); Yes (1) |
| 07 | str | 0 | 2 | — | No (16); Yes (4) |
| 08 | str | 0 | 2 | — | No (19); Yes (1) |
| 09 | str | 0 | 1 | — | No (20) |
| 10 | str | 0 | 1 | — | No (20) |
| 11 | str | 0 | 1 | — | No (20) |
| 12 | str | 0 | 2 | — | No (11); Yes (9) |
| 13 | str | 0 | 1 | — | No (20) |
| 14 | str | 0 | 2 | — | No (17); Yes (3) |
| 15 | str | 0 | 2 | — | No (17); Yes (3) |
| 16 | str | 2 | 2 | — | No (15); Yes (3) |
| 17 | str | 0 | 2 | — | No (19); Yes (1) |
| 18 | str | 0 | 2 | — | No (17); Yes (3) |
| 19 | str | 0 | 1 | — | No (20) |
| 20 | str | 0 | 1 | — | No (20) |
| 21 | str | 0 | 2 | — | No (17); Yes (3) |
| 22 | str | 0 | 2 | — | No (19); Yes (1) |
| 23 | str | 0 | 1 | — | No (20) |
| Record ID | int | 0 | 20 | — | 1 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 2 (1); 20 (1); 3 (1); 4 (1); 5 (1); 6 (1); 7 (1); 8 (1); 9 (1) |
| Event Name | str | 0 | 1 | — | Pre-ingestion (20) |

## Sheet `Pre-ingestion-Lifestyle`

- 20 rows x 40 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (1); 03 (1); 04 (1); 05 (1); 06 (1); 07 (1); 08 (1); 09 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 20 (1); 21 (1) |
| Have you ever smoked cigarettes? | str | 0 | 2 | — | No (19); Yes (1) |
| Do you currently smoke cigarettes? | str | 3 | 1 | — | No (17) |
| If no, cigarette quit date:  | — | 20 | 0 | — | e.g.  |
| How often do you smoke cigarettes? | — | 20 | 0 | — | e.g.  |
| Have you ever used e-cigarettes or vaping product… | str | 0 | 1 | — | No (20) |
| Do you currently use e-cigarettes or vaping produ… | str | 5 | 1 | — | No (15) |
| If no, e-cigarette/vaping quit date:  | — | 20 | 0 | — | e.g.  |
| How often do you use e-cigarettes/vaping products? | — | 20 | 0 | — | e.g.  |
| Have you ever smoked cannabis? | str | 0 | 2 | — | No (13); Yes (7) |
| Do you currently smoke cannabis? | str | 3 | 2 | — | No (15); Yes (2) |
| If no, cannabis quit date:  | — | 20 | 0 | — | e.g.  |
| How often do you smoke cannabis? | str | 16 | 2 | — | 2-4 times per month (1); Monthly or less (3) |
| How often do you have a drink containing alcohol?  | str | 0 | 4 | — | 2-4 times per month (7); 4 or more times a week (1); Monthly or less (11); Never (1) |
| How many standard drinks containing alcohol do yo… | str | 4 | 3 | — | 1 or 2 (13); 3 to 4 (2); 5 to 6 (1) |
| How often do you consume more than 6 drinks on on… | str | 3 | 2 | — | Less than monthly (7); Never (10) |
| Have you ever tested positive for COVID-19? | str | 0 | 2 | — | No (3); Yes (17) |
| If yes, enter date of positive COVID test: | — | 20 | 0 | — | e.g.  |
| None | str | 0 | 2 | — | No (6); Yes (14) |
| Vegan | str | 0 | 2 | — | No (19); Yes (1) |
| Vegetarian | str | 0 | 2 | — | No (17); Yes (3) |
| Pescatarian | str | 0 | 1 | — | No (20) |
| Gluten_free | str | 0 | 1 | — | No (20) |
| Keto | str | 0 | 1 | — | No (20) |
| Mediterranean | str | 0 | 1 | — | No (20) |
| Specific_Carbohydrate_Diet | str | 0 | 1 | — | No (20) |
| Low_FODMAP | str | 0 | 1 | — | No (20) |
| Intermittent_Fasting_time | str | 0 | 2 | — | No (18); Yes (2) |
| Intermittent_reduced_calorie | str | 0 | 1 | — | No (20) |
| Other | str | 0 | 1 | — | No (20) |
| If another diet, specify: | — | 20 | 0 | — | e.g.  |
| Dairy_consumption | str | 0 | 5 | — | 2-3 times per week (1); 2-4 times per month (2); 4 or more times per week (5); Daily (at least once a day) (11); Never (1) |
| Fermented_food_consumption | str | 0 | 6 | — | 2-3 times per week (2); 2-4 times per month (6); 4 or more times per week (4); Daily (at least once a day) (4); Monthly or less (3); Never (1) |
| Comments | — | 20 | 0 | — | e.g.  |
| Do you have a regular physical activity or exerci… | str | 0 | 2 | — | No (2); Yes (18) |
| What types of activities do you do for exercise o… | str | 2 | 18 | — | Badminton (1); Basketball, running, peloton, strength … (1); Biking (1); Lifting weights  Treadmill desk (1); Rock climbing approximately 2x per week (1); Running (1); Running, Pilates, yoga  (1); Running, biking, strength training (1); Strength training  Rowing  (1); Swim  Long hiking weekly (1); Walking, running, hiking, climbing, wei… (1); Weight lifting (1); Weight lifting, running, swimming, bask… (1); hiking (1); running, biking, strength training, str… (1); running, bouldering (1); running, walking, hiking, lifting (1); weightlifting 5x a week and cardio once… (1) |
| How many days of the week are you physically acti… | int | 0 | 7 | — | 1 (3); 2 (2); 3 (4); 4 (2); 5 (5); 6 (1); 7 (3) |
| How long do you usually exercise (per session of … | str | 0 | 4 | — | 30 minutes (1); 30-60 minutes (11); 60 minutes or more (5); Less than 30 minutes (3) |
| Record ID | int | 0 | 20 | — | 1 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 2 (1); 20 (1); 3 (1); 4 (1); 5 (1); 6 (1); 7 (1); 8 (1); 9 (1) |
| Event Name | str | 0 | 1 | — | Pre-ingestion (20) |

## Sheet `Pre-ingestion-GSRS-IBS`

- 20 rows x 16 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (1); 03 (1); 04 (1); 05 (1); 06 (1); 07 (1); 08 (1); 09 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 20 (1); 21 (1) |
| 01 | int | 0 | 3 | — | 1 (15); 2 (3); 3 (2) |
| 02 | int | 0 | 4 | — | 1 (13); 2 (3); 3 (3); 4 (1) |
| 03 | int | 0 | 4 | — | 1 (13); 2 (4); 3 (2); 4 (1) |
| 04 | int | 0 | 4 | — | 1 (11); 2 (6); 3 (1); 4 (2) |
| 05 | int | 0 | 3 | — | 1 (14); 2 (5); 3 (1) |
| 06 | int | 0 | 4 | — | 1 (14); 2 (4); 3 (1); 5 (1) |
| 07 | int | 0 | 2 | — | 1 (15); 2 (5) |
| 08 | int | 0 | 3 | — | 1 (15); 2 (4); 4 (1) |
| 09 | int | 0 | 5 | — | 1 (11); 2 (5); 3 (2); 4 (1); 5 (1) |
| 10 | int | 0 | 3 | — | 1 (14); 2 (4); 3 (2) |
| 11 | int | 0 | 3 | — | 1 (16); 2 (3); 3 (1) |
| 12 | int | 0 | 2 | — | 1 (17); 2 (3) |
| 13 | int | 0 | 3 | — | 1 (18); 3 (1); 4 (1) |
| Record ID | int | 0 | 20 | — | 1 (1); 10 (1); 11 (1); 12 (1); 13 (1); 14 (1); 15 (1); 16 (1); 17 (1); 18 (1); 19 (1); 2 (1); 20 (1); 3 (1); 4 (1); 5 (1); 6 (1); 7 (1); 8 (1); 9 (1) |
| Event Name | str | 0 | 1 | — | Pre-ingestion (20) |

## Sheet `Daily-diet`

- 170 rows x 7 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject_ID | str | 0 | 20 | — | 01 (9); 03 (10); 04 (10); 05 (8); 06 (10); 07 (9); 08 (10); 09 (9); 10 (4); 11 (3); 12 (9); 13 (8); 14 (8); 15 (8); 16 (10); 17 (7); 18 (10); 19 (10); 20 (10); 21 (8) |
| Date | str | 0 | 18 | NA: 3 | 08-03 (8); 08-04 (9); 08-05 (9); 08-06 (9); 08-07 (8); 08-08 (8); 08-09 (8); 08-10 (16); 08-11 (17); 08-12 (15); 08-13 (10); 08-14 (10); 08-15 (10); 08-16 (10); 08-17 (9); 08-18 (7); 08-19 (4); NA (3) |
| Event_name | str | 0 | 10 | — | Day 01 ingestion  (19); Day 02 ingestion (19); Day 03 ingestion (20); Day 04 ingestion (19); Day 05 ingestion (18); Day 06 ingestion (18); Day 07 ingestion (17); Day 08 (16); Day 09 (14); Day 10 (10) |
| Diet | str | 0 | 168 | — | e.g. 7:30 decaf coffee  9am a few bites of a…; 6:15 decaf coffee  8am croissant sandwi…; 7:15am decaf coffee  7:45am croissant s…; 8/6: 6:15 decaf coffee  Breakfast asiag… |
| Exercise | str | 0 | 83 | NA: 84 | e.g. Strength exercises from 9:30-10, strenu…; 6:30-7:40am basketball  4-4:30pm 3 mi r…; Basketball 12-1  Peloton 4:30-5  Streng…; 6:30-7:40 basketball  11:45-12:20 Tempe… |
| GI_symptoms | str | 1 | 23 | NA: 147 | Bad gas tonight (1); Bloating (1); Bloating  (1); Bowel movement (1); Bowel movements more hard than normal, … (1); Continued bloating and some irregularit… (1); Had a lot of gas after I ate McDonalds (1); Had a regular seeming bowel movement fi… (1); I got my period last night so I had cra… (1); Increased regularity - pooped twice.  (1); Mild bloating (1); Mild bloating  (1); Minor stomach aching (1); More bloating than normal and some irre… (1); More gas (1); NA (147); Pooped three times within the morning (1); Slower bowel movements for the past two… (1); Still bloated, gassy, and constipated, … (1); Still quite constipated/bloated, lots o… (1); mild constipation I think (1); none (1); some minor bloating (1) |
| Record ID | int | 0 | 20 | — | 1 (9); 10 (3); 11 (9); 12 (8); 13 (8); 14 (8); 15 (10); 16 (7); 17 (10); 18 (10); 19 (10); 2 (10); 20 (8); 3 (10); 4 (8); 5 (10); 6 (9); 7 (10); 8 (9); 9 (4) |

## Sheet `Daily-PANAS`

- 170 rows x 23 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Subject number (cfr excel Beverly) | str | 0 | 20 | — | 01 (9); 03 (10); 04 (10); 05 (8); 06 (10); 07 (9); 08 (10); 09 (9); 10 (4); 11 (3); 12 (9); 13 (8); 14 (8); 15 (8); 16 (10); 17 (7); 18 (10); 19 (10); 20 (10); 21 (8) |
| Interested | str | 0 | 5 | — | A little (43); Extremely (5); Moderately (78); Quite a bit (40); Very slightly or Not at all (4) |
| Distressed | str | 0 | 5 | — | A little (59); Extremely (1); Moderately (25); Quite a bit (11); Very slightly or Not at all (74) |
| Excited | str | 0 | 5 | — | A little (45); Extremely (4); Moderately (57); Quite a bit (41); Very slightly or Not at all (23) |
| Upset | str | 0 | 4 | — | A little (28); Moderately (15); Quite a bit (5); Very slightly or Not at all (122) |
| Strong | str | 0 | 5 | — | A little (46); Extremely (4); Moderately (52); Quite a bit (25); Very slightly or Not at all (43) |
| Guilty | str | 0 | 4 | — | A little (28); Extremely (1); Moderately (5); Very slightly or Not at all (136) |
| Scared | str | 0 | 4 | — | A little (27); Moderately (2); Quite a bit (1); Very slightly or Not at all (140) |
| Hostile | str | 0 | 3 | — | A little (18); Moderately (2); Very slightly or Not at all (150) |
| Enthusiastic | str | 0 | 5 | — | A little (63); Extremely (6); Moderately (52); Quite a bit (31); Very slightly or Not at all (18) |
| Proud | str | 0 | 5 | — | A little (52); Extremely (3); Moderately (45); Quite a bit (23); Very slightly or Not at all (47) |
| Irritable | str | 0 | 5 | — | A little (40); Extremely (1); Moderately (19); Quite a bit (4); Very slightly or Not at all (106) |
| Alert | str | 0 | 5 | — | A little (57); Extremely (1); Moderately (45); Quite a bit (19); Very slightly or Not at all (48) |
| Ashamed | str | 0 | 4 | — | A little (14); Extremely (1); Moderately (8); Very slightly or Not at all (147) |
| Inspired | str | 0 | 5 | — | A little (66); Extremely (3); Moderately (33); Quite a bit (24); Very slightly or Not at all (44) |
| Nervous | str | 0 | 4 | — | A little (48); Moderately (17); Quite a bit (8); Very slightly or Not at all (97) |
| Determined | str | 0 | 5 | — | A little (52); Extremely (9); Moderately (47); Quite a bit (26); Very slightly or Not at all (36) |
| Attentive | str | 0 | 5 | — | A little (50); Extremely (2); Moderately (59); Quite a bit (26); Very slightly or Not at all (33) |
| Jittery | str | 0 | 4 | — | A little (13); Extremely (1); Moderately (5); Very slightly or Not at all (151) |
| Active | str | 0 | 5 | — | A little (48); Extremely (8); Moderately (53); Quite a bit (23); Very slightly or Not at all (38) |
| Afraid | str | 0 | 4 | — | A little (19); Moderately (1); Quite a bit (1); Very slightly or Not at all (149) |
| Record ID | int | 0 | 20 | — | 1 (9); 10 (3); 11 (9); 12 (8); 13 (8); 14 (8); 15 (10); 16 (7); 17 (10); 18 (10); 19 (10); 2 (10); 20 (8); 3 (10); 4 (8); 5 (10); 6 (9); 7 (10); 8 (9); 9 (4) |
| Event Name | str | 0 | 10 | — | Day 1 ingestion  (19); Day 10 (10); Day 2 ingestion (19); Day 3 ingestion (20); Day 4 ingestion (19); Day 5 ingestion (18); Day 6 ingestion (18); Day 7 ingestion (17); Day 8 (16); Day 9 (14) |

## Sheet `Daily-Nutrient`

- 184 rows x 54 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Date_reformat | str | 0 | 60 | — | e.g. 08-01; 08-02; 08-03; 08-04 |
| Subject_ID | str | 0 | 19 | — | 03 (3); 04 (3); 05 (15); 06 (4); 07 (4); 08 (4); 09 (4); 10 (11); 11 (34); 12 (3); 13 (7); 14 (6); 15 (3); 16 (4); 17 (4); 18 (13); 19 (3); 20 (50); 21 (9) |
| Energy_kcal | float | 0 | 183 | — | range 0–3956.62; e.g. 2842.92; 3257.67; 3168.79; 1804.78 |
| Alcohol_g | float | 0 | 29 | — | range 0–69.61; e.g. 0.0; 0.03; 0.06; 0.04 |
| Caffeine_mg | float | 0 | 79 | — | range 0–416.8; e.g. 0.0; 120.0; 89.1; 127.85 |
| Water_g | float | 0 | 183 | — | range 0–8977.69; e.g. 2547.62; 2675.57; 1894.41; 2758.75 |
| B1_Thiamine_mg | float | 0 | 119 | — | range 0–8.83; e.g. 0.83; 1.44; 1.45; 0.93 |
| B2_Riboflavin_mg | float | 0 | 126 | — | range 0–12.59; e.g. 1.66; 1.3; 1.96; 0.74 |
| B3_Niacin_mg | float | 0 | 177 | — | range 0–53.92; e.g. 6.3; 9.34; 18.06; 10.96 |
| B5_Pantothenic_Acid_mg | float | 0 | 156 | — | range 0–33.61; e.g. 2.35; 2.81; 2.61; 2.37 |
| B6_Pyridoxine_mg | float | 0 | 137 | — | range 0–9.12; e.g. 0.88; 1.13; 1.32; 1.1 |
| B12_Cobalamin_ug | float | 0 | 149 | — | range 0–1006.35; e.g. 2.4; 1.23; 1006.35; 1.44 |
| Folate_ug | float | 0 | 178 | — | range 0–1500.61; e.g. 450.98; 546.39; 351.49; 343.57 |
| Vitamin_A_ug | float | 0 | 180 | — | range 0–7039.82; e.g. 640.2; 639.38; 7039.82; 246.94 |
| Vitamin_C_mg | float | 0 | 178 | — | range 0–439.15; e.g. 130.75; 145.02; 106.57; 53.44 |
| Vitamin_D_IU | float | 0 | 161 | — | range 0–2000; e.g. 507.91; 344.0; 394.26; 0.0 |
| Vitamin_E_mg | float | 0 | 168 | — | range 0–138.28; e.g. 3.4; 9.67; 4.32; 7.24 |
| Vitamin_K_ug | float | 0 | 176 | — | range 0–1504.32; e.g. 237.74; 103.21; 109.03; 170.46 |
| Calcium_mg | float | 0 | 182 | — | range 0–2528.91; e.g. 2528.91; 2076.79; 2260.92; 937.04 |
| Copper_mg | float | 0 | 128 | — | range 0–3.86; e.g. 1.45; 1.08; 0.64; 1.18 |
| Iron_mg | float | 0 | 172 | — | range 0–37.39; e.g. 20.25; 21.45; 24.11; 13.45 |
| Magnesium_mg | float | 0 | 177 | — | range 0–899.43; e.g. 371.44; 313.81; 178.65; 226.22 |
| Manganese_mg | float | 0 | 156 | — | range 0–10.55; e.g. 4.52; 4.07; 1.69; 4.58 |
| Phosphorus_mg | float | 0 | 178 | — | range 0–2162.81; e.g. 1922.43; 1600.69; 1777.8; 750.94 |
| Potassium_mg | float | 0 | 183 | — | range 0–6299.39; e.g. 4596.07; 4012.25; 4655.11; 2529.52 |
| Selenium_ug | float | 0 | 178 | — | range 0–184.67; e.g. 81.89; 57.45; 76.59; 44.03 |
| Sodium_mg | float | 0 | 183 | — | range 0–7591.62; e.g. 4752.4; 4976.54; 3410.96; 2682.66 |
| Zinc_mg | float | 0 | 171 | — | range 0–25.65; e.g. 10.82; 9.3; 13.55; 7.45 |
| Carbs_g | float | 0 | 182 | — | range 0–468.12; e.g. 290.68; 468.12; 421.81; 198.96 |
| Fiber_g | float | 0 | 178 | — | range 0–74.72; e.g. 35.64; 40.16; 38.31; 23.22 |
| Starch_g | float | 0 | 172 | — | range 0–202.94; e.g. 39.19; 98.64; 79.43; 45.19 |
| Sugars_g | float | 0 | 181 | — | range 0–205.94; e.g. 119.94; 86.56; 111.38; 60.72 |
| Added_Sugars_g | float | 0 | 164 | — | range 0–128.88; e.g. 67.74; 29.41; 32.02; 25.08 |
| Net_Carbs_g | float | 0 | 183 | — | range 0–427.46; e.g. 251.23; 427.46; 383.33; 175.13 |
| Fat_g | float | 0 | 179 | — | range 0–205.54; e.g. 133.55; 104.01; 107.02; 93.43 |
| Cholesterol_mg | float | 0 | 176 | — | range 0–824.8; e.g. 109.8; 112.45; 310.65; 0.0 |
| Monounsaturated_g | float | 0 | 176 | — | range 0–57.65; e.g. 15.57; 23.26; 21.19; 33.21 |
| Polyunsaturated_g | float | 0 | 171 | — | range 0–32.11; e.g. 15.06; 18.74; 14.18; 9.89 |
| Saturated_g | float | 0 | 179 | — | range 0–63.37; e.g. 31.2; 32.64; 29.27; 16.77 |
| Trans_Fats_g | float | 0 | 96 | — | range 0–4.48; e.g. 0.53; 0.75; 1.01; 0.06 |
| Omega_3_g | float | 0 | 122 | — | range 0–8.42; e.g. 2.04; 1.0; 1.16; 1.05 |
| Omega_6_g | float | 0 | 172 | — | range 0–28.27; e.g. 12.64; 9.03; 9.8; 8.45 |
| Cystine_g | float | 0 | 94 | — | range 0–2.09; e.g. 0.81; 0.57; 0.51; 0.27 |
| Histidine_g | float | 0 | 123 | — | range 0–4.63; e.g. 1.38; 1.01; 0.83; 0.93 |
| Isoleucine_g | float | 0 | 148 | — | range 0–7.64; e.g. 2.35; 1.72; 1.42; 1.8 |
| Leucine_g | float | 0 | 154 | — | range 0–13.35; e.g. 3.91; 3.11; 2.47; 3.0 |
| Lysine_g | float | 0 | 155 | — | range 0–12.52; e.g. 3.1; 2.26; 1.96; 1.89 |
| Methionine_g | float | 0 | 112 | — | range 0–3.74; e.g. 0.69; 0.66; 0.52; 0.4 |
| Phenylalanine_g | float | 0 | 146 | — | range 0–7.58; e.g. 2.52; 2.01; 1.61; 1.84 |
| Protein_g | float | 0 | 179 | — | range 0–186.65; e.g. 141.57; 128.63; 142.28; 61.3 |
| Threonine_g | float | 0 | 135 | — | range 0–6.48; e.g. 1.93; 1.56; 1.16; 1.71 |
| Tryptophan_g | float | 0 | 88 | — | range 0–1.99; e.g. 0.73; 0.47; 0.39; 0.5 |
| Tyrosine_g | float | 0 | 136 | — | range 0–5.73; e.g. 1.56; 1.24; 1.2; 1.43 |
| Valine_g | float | 0 | 142 | — | range 0–8.27; e.g. 2.61; 2.08; 1.73; 1.97 |

## Sheet `Food-category`

- 52 rows x 3 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Nutrient | str | 0 | 52 | — | e.g. Energy_kcal; Alcohol_g; Caffeine_mg; Water_g |
| Category | str | 0 | 6 | — | Carbohydrates (6); Fats (8); Minerals (10); Other (4); Protein (12); Vitamins (12) |
| Daily_amount | str | 0 | 40 | NA: 6 | e.g. 2000; NA; 400; 3700 |

## Sheet `Questions-for-Leila`

- 2 rows x 2 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Questions for Leila | str | 0 | 2 | — | Double check all of KC's data with me (1); LS1888 LS1889 LS1890 LS1891 (1) |
| Unnamed: 1 | str | 1 | 1 | — | Do you know the capID? (1) |

## Sheet `Study_notes`

- 8 rows x 1 columns

| Column | Types | Missing | Distinct | Tokens | Values |
|---|---|---|---|---|---|
| Unnamed: 0 | str | 0 | 8 | — | Subject 1's notes are a mess (1); Subject 10 has duplicate stool for same… (1); Subject 14 did not ingest cap7 as it wa… (1); Subject 16 has duplicate stool for same… (1); Subject 18 has duplicate stool for same… (1); Subject 19 didn't do Cap0 or complete E… (1); Subject 20's notes are a mess (1); Subject 7 ingested cap1 on the wrong da… (1) |

