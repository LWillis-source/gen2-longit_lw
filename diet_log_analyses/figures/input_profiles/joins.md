# Join coverage

Profiled 2026-10-18 21:01. Each row: a join documented in diet_log_analyses/CLAUDE.md and how many keys find a partner.

| Join | Left keys | Matched | Unmatched (examples) |
|---|---|---|---|
| diet subjects -> sample-sheet subjects | 19 | 19 | 0 |
| sample-sheet subjects -> diet subjects | 20 | 19 | 1 (11) |
| diet ingredients -> lexicon Ingredient | 226 | 226 | 0 |
| diet subject-days -> Daily-Nutrient days | 167 | 49 | 118 (('01', '08-03'), ('01', '08-04'), ('01', '08-05'), ('01', '08-06')) |
| 16S info-sheet libraries -> count table | 645 | 644 | 1 (16S-P10-B2-G12-L2_P3-G12-CapS…) |
| 16S count-table rows -> info sheet | 753 | 644 | 109 (16S-P10-B2-D09-L7_P8-D09-Stoo…, 16S-P10-B2-D10-L7_P8-D10-Stoo…, 16S-P10-B2-D11-L7_P8-D11-Stoo…, 16S-P10-B2-D12-L7_P8-D12-Stoo…) |
| 16S info-sheet Sample_ID -> sample sheet | 645 | 645 | 0 |
| Plant info-sheet libraries -> count table | 768 | 768 | 0 |
| Plant count-table rows -> info sheet | 768 | 768 | 0 |
| Plant LONGIT Sample_ID -> sample sheet | 649 | 649 | 0 |
| Meat info-sheet libraries -> count table | 768 | 763 | 5 (LD-16S-P15-B2-G05_S1229, LD-16S-P15-B2-G07_S1231, LD-16S-P15-B2-G08_S1232, LD-16S-P15-B2-G09_S1233) |
| Meat count-table rows -> info sheet | 763 | 763 | 0 |
| Meat LONGIT Sample_ID -> sample sheet | 649 | 649 | 0 |
| plants LONGIT Sample_ID -> meat LONGIT Sample_ID | 649 | 649 | 0 |
| meat LONGIT Sample_ID -> plants LONGIT Sample_ID | 649 | 649 | 0 |

