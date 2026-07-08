# Safe Example Artifact Pack

Guidelines for creating example artifacts that are safe to distribute.

## Rules
- Use only synthetic or public-domain data.
- Label all data as `example`, `demo`, or `synthetic`.
- No real candidate sequences from unpublished work.
- No lab results from real experiments.
- No PII (personally identifiable information).
- All example artifacts should pass `check_claims.py` and `check_doc_links.py`.

## Current Examples
| Artifact | Type | Safety Check |
|----------|:----:|:------------:|
| demo_candidates.csv | synthetic | ✅ Synthetic, no real data |
| demo_known_amps.csv | public | ✅ Public AMP sequences |
| lab_results/ | synthetic | ✅ Labeled SYNTHETIC |

## Related
- `docs/evidence/SYNTHETIC_DATA_POLICY.md`
- `docs/evidence/GUIDE_TOY_DATA_MARKERS.md`
