# Documentation Readiness Checklist

Before sharing a project update or preparing a public release, verify
documentation health with this checklist.

---

## Link Health

- [ ] `python scripts/check_doc_links.py` reports 0 broken links
- [ ] All cross-references between docs resolve correctly
- [ ] External links (APD6, DRAMP, UniProt) are still accessible

## Freshness

- [ ] `docs/evidence/METRICS_CURRENT.md` matches current benchmark outputs
- [ ] `docs/research/ROADMAP.md` reflects completed and in-progress work
- [ ] `docs/evidence/SIMULATION_BENCHMARK.md` matches current gate verdict
- [ ] Version numbers in docs match the current pipeline version

## Claim Wording

- [ ] `python scripts/safety/check_claims.py` reports no overclaiming language
- [ ] No document claims biological validation without wet-lab data
- [ ] Terms like "proven", "drug candidate", "safe in humans" are absent or quoted
- [ ] All benchmark claims reference honest limitations (charge-domination, no wet-lab data)

## Quickstart Accuracy

- [ ] `make demo` succeeds
- [ ] `python3 -m pytest -q` passes
- [ ] Quickstart instructions match actual commands
- [ ] Setup steps work from a clean checkout

## Release Readiness

- [ ] `docs/review/PUBLICATION_PACK.md` checklist is complete
- [ ] `docs/review/RELEASE_DRY_RUN_GUIDE.md` is up to date
- [ ] `make full-reproducibility-report` succeeds

## Governance

- [ ] `AGENT_TASKS.json` task categories are current
- [ ] `docs/evidence/SYNTHETIC_DATA_POLICY.md` is referenced where synthetic data is used
- [ ] `docs/evidence/LIMITATIONS_OVERVIEW.md` is accurate

## Blocker vs Warning

| Severity | Example | Action |
|----------|---------|--------|
| 🔴 Blocker | Broken link in quickstart | Fix before sharing |
| 🔴 Blocker | Overclaiming language in public-facing doc | Rewrite before release |
| 🟡 Warning | Stale ROADMAP entry | Update when possible |
| 🟡 Warning | METRICS_CURRENT.md minor version mismatch | Update when possible |

A blocker must be resolved before any public update. A warning should be
resolved but is not a release gate.
