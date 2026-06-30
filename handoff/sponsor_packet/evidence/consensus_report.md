# External Validation — Consensus Report

Candidates: 450 | independent tools run: 7 (AMP×4, hemo×2, off-target×1)

## Per-tool summary

**AMP-activity tools:**
  camp4_results.csv: 450 scored, 445 positive (99%)
  ampscanner_results.csv: 450 scored, 334 positive (74%)
  ampactipred_results.csv: 450 scored, 374 positive (83%)
  macrel_web_results.csv: 450 scored, 450 positive (100%)

**Hemolysis tools (positive = non-hemolytic):**
  hemofinder_results.csv: 450 scored, 379 positive (84%)
  macrel_web_results.csv: 450 scored, 31 positive (7%)

**Off-target (positive = Non-AntiCP):**
  anticp2_results.csv: 450 scored, 322 positive (72%)

## AMP-positive agreement distribution

(out of 4 AMP tools)

  4/4 AMP tools positive: 309 candidates
  3/4 AMP tools positive: 87 candidates
  2/4 AMP tools positive: 52 candidates
  1/4 AMP tools positive: 2 candidates

## Strict consensus shortlist: 21 candidates

Criteria: AMP-positive on ≥2/4 tools AND non-hemolytic (all hemo tools) AND Non-AntiCP.

| Rank | ID | Sequence | AMP calls | camp4 | ampscanner | ampactipred | macrel | NonHemo | NonAntiCP | final |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | XPRT_0010 | `LGKALIPKPTKWTGRYAKYDKDVI` | 4/4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.7478 |
| 2 | XPRT_0021 | `ILRINLSKLNPKVPDRWERFWRPG` | 4/4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.7232 |
| 3 | XPRT_0053 | `GIDNGGNKFFYETVRKPLKVGFK` | 4/4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.7056 |
| 4 | XPRT_0004 | `IWEARYWSFVLKRLPRDFDKQKAS` | 3/4 | · | ✓ | ✓ | ✓ | ✓ | ✓ | 0.7617 |
| 5 | XPRT_0008 | `AGKGLKDYIRPVLENRFLGVR` | 3/4 | ✓ | ✓ | · | ✓ | ✓ | ✓ | 0.7551 |
| 6 | XPRT_0011 | `IIKIGKYNGTKENGFDRWIRLTVK` | 3/4 | ✓ | · | ✓ | ✓ | ✓ | ✓ | 0.7469 |
| 7 | XPRT_0081 | `ILERFGARGKDHGGRFATRFSPF` | 3/4 | ✓ | ✓ | · | ✓ | ✓ | ✓ | 0.6935 |
| 8 | XPRT_0248 | `ITGARGAAKGPRGVRRPWTIEFFT` | 3/4 | ✓ | ✓ | · | ✓ | ✓ | ✓ | 0.6445 |
| 9 | XPRT_0001 | `LVRDARKRGRDIVPLFVKGFPDPN` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7953 |
| 10 | XPRT_0003 | `IVRGEGQKFPDKLFRAPKQLYGSI` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7633 |
| 11 | XPRT_0005 | `GAKGNFNKGRFLIERINRIDYIP` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7608 |
| 12 | XPRT_0006 | `VLRITYIYKRELPRGIKKPSDEFL` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7583 |
| 13 | XPRT_0007 | `WGEYVQKEIKVSPWIPRVGRK` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7563 |
| 14 | XPRT_0012 | `VLKLADLETFRQWRVGKTIPKRPW` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7422 |
| 15 | XPRT_0017 | `IKHADHPLYRDTGRTAIRIALTIK` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7285 |
| 16 | XPRT_0028 | `VFKIVIPYRATGVRASKKVEDPV` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7174 |
| 17 | XPRT_0042 | `GFNVDEVYPKGLNARKIFRSIVRG` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7108 |
| 18 | XPRT_0064 | `AFTKKPALVYRINEFYDKPIRKIA` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7027 |
| 19 | XPRT_0069 | `IADWPGGFKQKVRFTRRGIDLTI` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.7007 |
| 20 | XPRT_0078 | `LLGIPGRGKRKVFNFDRNADA` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.6947 |
| 21 | XPRT_0120 | `AVYPERGFELISKLVRLKPKV` | 2/4 | ✓ | · | · | ✓ | ✓ | ✓ | 0.6768 |

## ★ Recommended antibacterial shortlist: 225 candidates

Criteria: **AMPActiPred ABP+** (antibacterial-specific) AND **HemoFinder non-hemolytic** (primary hemolysis model) AND **Non-AntiCP** AND ≥2 general AMP tools. Macrel-hemo is treated as advisory only — it over-flags hemolysis (419/450 called hemolytic vs HemoFinder's much lower rate), so gating on it (the strict list below) is needlessly punishing. Ranked by internal final_score.

| Rank | ID | Sequence | AMP calls | NonHemo(HF) | ABP | final |
|---|---|---|---|---|---|---|
| 1 | XPRT_0004 | `IWEARYWSFVLKRLPRDFDKQKAS` | 3/4 | ✓ | ✓ | 0.7617 |
| 2 | XPRT_0010 | `LGKALIPKPTKWTGRYAKYDKDVI` | 4/4 | ✓ | ✓ | 0.7478 |
| 3 | XPRT_0011 | `IIKIGKYNGTKENGFDRWIRLTVK` | 3/4 | ✓ | ✓ | 0.7469 |
| 4 | XPRT_0014 | `IVKQARGRVGKIRTNWHRLFHRIG` | 4/4 | ✓ | ✓ | 0.7352 |
| 5 | XPRT_0015 | `VAVKLPRFFIKTSRPYRGRPHRGV` | 4/4 | ✓ | ✓ | 0.7296 |
| 6 | XPRT_0019 | `VVIRAFPKYITKIKRGKAGETRRP` | 4/4 | ✓ | ✓ | 0.7253 |
| 7 | XPRT_0021 | `ILRINLSKLNPKVPDRWERFWRPG` | 4/4 | ✓ | ✓ | 0.7232 |
| 8 | XPRT_0022 | `IWRILWKFGNHEYKIIKSKGRKD` | 4/4 | ✓ | ✓ | 0.7202 |
| 9 | XPRT_0023 | `IRKKDRKFKRIKPWERYWLLVYN` | 3/4 | ✓ | ✓ | 0.7197 |
| 10 | XPRT_0027 | `LLKGEFRVKLNLPRKEVYKFARSI` | 3/4 | ✓ | ✓ | 0.7178 |
| 11 | XPRT_0029 | `LKKGYNIFKRYVDNRIAA` | 3/4 | ✓ | ✓ | 0.7174 |
| 12 | XPRT_0031 | `LLIQKVFRPYFREWKELPKRRY` | 4/4 | ✓ | ✓ | 0.716 |
| 13 | XPRT_0035 | `IVREFIRRFPRGHREKYLRPIYNP` | 4/4 | ✓ | ✓ | 0.7149 |
| 14 | XPRT_0037 | `WIVRKVYSRAFRREFKYGASGEKT` | 3/4 | ✓ | ✓ | 0.7133 |
| 15 | XPRT_0039 | `IDEAKRIFKGLKRSVWIHRIN` | 4/4 | ✓ | ✓ | 0.7124 |
| 16 | XPRT_0040 | `KIKWKPTRVPRATGRAIYWEKKVI` | 4/4 | ✓ | ✓ | 0.712 |
| 17 | XPRT_0050 | `LKIVLKSFNGNRKAVNRYNELIR` | 3/4 | ✓ | ✓ | 0.706 |
| 18 | XPRT_0051 | `GRGRRFPRFWYKDAINLS` | 4/4 | ✓ | ✓ | 0.706 |
| 19 | XPRT_0052 | `IRKAGKIRRVFPYRAVRQLIKLS` | 4/4 | ✓ | ✓ | 0.7057 |
| 20 | XPRT_0053 | `GIDNGGNKFFYETVRKPLKVGFK` | 4/4 | ✓ | ✓ | 0.7056 |
| 21 | XPRT_0058 | `LFGKAFQPFVIRWRPSQRPVKRKR` | 4/4 | ✓ | ✓ | 0.7037 |
| 22 | XPRT_0059 | `AGKFRKQFGRALTRLRTLIGSFNK` | 4/4 | ✓ | ✓ | 0.7035 |
| 23 | XPRT_0063 | `KVKPRKTRLFFRAVKPINLVLHP` | 4/4 | ✓ | ✓ | 0.703 |
| 24 | XPRT_0066 | `GLKGRLANRNFKRVPDAFLAG` | 4/4 | ✓ | ✓ | 0.7024 |
| 25 | XPRT_0067 | `ARKIVTGWTRKLNPFKGRAQRFLS` | 4/4 | ✓ | ✓ | 0.7019 |
| 26 | XPRT_0068 | `AAKINRAWKKPTREPKFTLLREGF` | 3/4 | ✓ | ✓ | 0.7009 |
| 27 | XPRT_0075 | `VIHRVIKNLSKPKRYELP` | 4/4 | ✓ | ✓ | 0.6979 |
| 28 | XPRT_0076 | `AVRTGKRFLLQPYRVWGIGSDKRG` | 3/4 | ✓ | ✓ | 0.6958 |
| 29 | XPRT_0079 | `VRGKKRVFAIFWAWPPKKPSRGIR` | 4/4 | ✓ | ✓ | 0.6937 |
| 30 | XPRT_0082 | `LSLRKPLRVIWRYGEITLKVYKEK` | 3/4 | ✓ | ✓ | 0.6927 |
| 31 | XPRT_0087 | `LKGVWTRIRGRVHHAWRNAKKAI` | 4/4 | ✓ | ✓ | 0.6915 |
| 32 | XPRT_0090 | `VKGVIDHFKVKGRFTKKVNEFWKA` | 4/4 | ✓ | ✓ | 0.6907 |
| 33 | XPRT_0091 | `GRNANRVAKPTYRFKSAIIA` | 4/4 | ✓ | ✓ | 0.6905 |
| 34 | XPRT_0092 | `VKNWKRDWPRLYNVKAKI` | 4/4 | ✓ | ✓ | 0.6903 |
| 35 | XPRT_0093 | `WRAIKWVKFNASPVRPKTRKFVRP` | 4/4 | ✓ | ✓ | 0.6899 |
| 36 | XPRT_0095 | `GGASHQIQRLLGGFTRIARRLNGK` | 4/4 | ✓ | ✓ | 0.6892 |
| 37 | XPRT_0096 | `LGQVGSKWGRAFKRLKGRFQKFRS` | 4/4 | ✓ | ✓ | 0.6879 |
| 38 | XPRT_0102 | `VGAPIFSFTPKWTKRPKR` | 4/4 | ✓ | ✓ | 0.6844 |
| 39 | XPRT_0106 | `FRNKAVITSKGFRRVRFLGNAFKP` | 4/4 | ✓ | ✓ | 0.6813 |
| 40 | XPRT_0109 | `ILGTFKKKWTRFTPRLKGIVRTWK` | 4/4 | ✓ | ✓ | 0.6801 |

## Headline

- 396/450 are AMP-positive on ≥3 independent tools.
- **225/450 recommended** (ABP+ ∩ HemoFinder-NonHemo ∩ Non-AntiCP ∩ ≥2 general AMP) — the practical wet-lab pool.
- 21/450 ultra-strict (also non-hemolytic by Macrel, which over-flags).
- Top recommended candidate: **XPRT_0004** (IWEARYWSFVLKRLPRDFDKQKAS) — antibacterial (ABP+), 3/4 AMP tools, HemoFinder non-hemolytic, Non-AntiCP, internal final=0.7617.
