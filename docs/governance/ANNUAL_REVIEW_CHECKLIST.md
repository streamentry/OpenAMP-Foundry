# Annual Safety and Benchmark Review Checklist

> **Scope:** Dry-lab only. No wet-lab or in-vivo claims.
> **Cadence:** Annually, or after any major pipeline version change.
> **Purpose:** Ensure safety policy, benchmark thresholds, calibration, governance decisions,
> and data governance remain current and honest.

---

## 1. Safety Policy Review

- [ ] Re-read `SAFETY.md` and confirm all dual-use safeguards remain in effect.
- [ ] Confirm `dry_lab_only: True` is enforced on all result and report dataclasses.
- [ ] Confirm that `evidence_level > 4` with `dry_lab_only=True` still raises an error.
- [ ] Confirm public releases with `safety_review_status: pending` are still blocked.
- [ ] Confirm the toxicity and hemolysis filter thresholds have not been weakened.
- [ ] Document any safety policy changes with a new `GOV-XXX` decision log entry.

## 2. Benchmark Threshold Review

- [ ] Re-read `docs/evidence/BENCHMARK_GOVERNANCE.md` for threshold rationale.
- [ ] Confirm benchmark thresholds have not been silently loosened.
- [ ] Check whether any benchmark has been deprecated without replacement.
- [ ] Confirm all benchmarks include an easy-baseline comparison.
- [ ] Confirm selectivity benchmarks are still present and passing.
- [ ] Document any threshold changes with a `GOV-XXX` decision log entry and rationale.

## 3. Calibration Status Review

- [ ] Run `make bench-calibration` and confirm no calibration regression.
- [ ] Confirm the calibration decision checklist has been reviewed.
- [ ] Confirm the recalibration gate is still active.
- [ ] Confirm calibration rollback plan is documented and up to date.

## 4. Governance Decisions Review

- [ ] Run `make decision-log` and confirm all governance decisions are `active` or `superseded` with rationale.
- [ ] Confirm no governance decision is in `under_review` status for more than 30 days without action.
- [ ] Confirm COI disclosures are filed for all maintainers and external advisors.
- [ ] Confirm maintainer rotation plan is up to date (`make rotation-plan-check`).

## 5. Data Governance Review

- [ ] Confirm `DATA_LICENSE_NOTICE.md` is current.
- [ ] Confirm no proprietary data has entered the pipeline without a `contact_required` license flag.
- [ ] Confirm all external data sources are documented in the data governance log.

## 6. Action Items

After completing each section, record findings using `make annual-review-check`.
Any `finding_count > 0` must have a corresponding `action_items_count > 0`.
Critical findings halt the next candidate release until resolved.

---

*This checklist is machine-validated. See `src/openamp_foundry/governance/annual_review.py`.*
