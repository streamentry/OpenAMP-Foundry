"""Tests for Wave 0.5 scaffold diversification gate checker."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from openamp_foundry.gates.wave0_5_gate_checker import (
    W05GateResult,
    check_w05_1_family_diversity,
    check_w05_2_family_redundancy,
    check_w05_3_activity_consensus,
    check_w05_4_safety_annotation,
    check_w05_5_novelty_qualification,
    check_w05_6_control_integrity,
    check_w05_7_claim_safety,
    run_all_gates,
    MIN_FAMILIES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PANEL_FIELDNAMES = [
    "candidate_id", "sequence", "seed_family", "source", "panel_role",
    "openamp_activity", "openamp_safety", "novelty_class",
    "synthesis_flags", "reason_for_inclusion", "reason_for_exclusion",
]

CONSENSUS_FIELDNAMES = [
    "candidate_id", "sequence", "seed_family",
    "campr4_vote", "ampscanner_vote", "macrel_amp_vote", "ampactipred_abp_vote",
    "activity_votes", "total_activity_predictors", "activity_consensus",
    "anticp2_class", "hemofinder_risk", "macrel_hemolysis_flag", "safety_risk_level",
    "openamp_activity_score", "openamp_safety_score", "shortlist_role",
]

NOVELTY_FIELDNAMES = [
    "candidate_id", "sequence", "seed_family",
    "best_database", "best_hit_id", "best_hit_sequence",
    "best_identity", "best_similarity",
    "novelty_class", "patent_risk", "action", "shortlist_role",
]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _make_panel(
    n_families: int = 10,
    leads_per_family: int = 2,
    extra_rows: list[dict] | None = None,
) -> list[dict]:
    rows = []
    for i in range(n_families):
        for j in range(leads_per_family):
            rows.append({
                "candidate_id": f"SEED-{10 + i:03d}_VAR_{j:03d}",
                "sequence": "AKRKFGYK" + ("KK" * i),
                "seed_family": f"SEED-{10 + i:03d}",
                "panel_role": "BALANCED_LEAD",
                "novelty_class": "HIGH_CONFIDENCE_NOVEL",
            })
    # Add required control
    rows.append({
        "candidate_id": "SEED-001_VAR_064",
        "sequence": "KWKLFRKIGAVLRVL",
        "seed_family": "SEED-001",
        "panel_role": "POSITIVE_CONTROL",
        "novelty_class": "KNOWN_VARIANT",
    })
    if extra_rows:
        rows.extend(extra_rows)
    return rows


# ---------------------------------------------------------------------------
# Gate W0.5-1: Family Diversity
# ---------------------------------------------------------------------------
class TestGateW051FamilyDiversity:
    def test_pass_with_enough_families(self, tmp_path):
        rows = _make_panel(n_families=MIN_FAMILIES)
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_1_family_diversity(p)
        assert result.status == "PASS"
        assert int(result.value) >= MIN_FAMILIES

    def test_fail_with_too_few_families(self, tmp_path):
        # _make_panel always adds a SEED-001 control, so use n_families=1 to get 2 total
        rows = _make_panel(n_families=1)
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_1_family_diversity(p)
        assert result.status == "FAIL"

    def test_counts_unique_families_not_candidates(self, tmp_path):
        # 20 candidates from 1 family → FAIL
        rows = [
            {"candidate_id": f"S001_VAR_{i:03d}", "sequence": "AKRK", "seed_family": "SEED-001",
             "panel_role": "BALANCED_LEAD", "novelty_class": "HIGH_CONFIDENCE_NOVEL"}
            for i in range(20)
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_1_family_diversity(p)
        assert result.status == "FAIL"

    def test_gate_id_is_w051(self, tmp_path):
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, _make_panel())
        result = check_w05_1_family_diversity(p)
        assert result.gate == "W0.5-1"


# ---------------------------------------------------------------------------
# Gate W0.5-2: Family Redundancy
# ---------------------------------------------------------------------------
class TestGateW052FamilyRedundancy:
    def test_pass_with_two_leads_per_family(self, tmp_path):
        rows = _make_panel(n_families=8, leads_per_family=2)
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_2_family_redundancy(p)
        assert result.status == "PASS"

    def test_fail_with_three_leads_from_one_family(self, tmp_path):
        rows = _make_panel(n_families=8, leads_per_family=2)
        # Add a third BALANCED_LEAD from the same family
        rows.append({
            "candidate_id": "SEED-010_VAR_099",
            "sequence": "AKRKFGYKKKK",
            "seed_family": "SEED-010",
            "panel_role": "BALANCED_LEAD",
            "novelty_class": "HIGH_CONFIDENCE_NOVEL",
        })
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_2_family_redundancy(p)
        assert result.status == "FAIL"

    def test_controls_not_counted_as_leads(self, tmp_path):
        # A POSITIVE_CONTROL from a family should not trigger family cap
        rows = [
            {"candidate_id": "CTRL-001", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "POSITIVE_CONTROL", "novelty_class": "KNOWN_VARIANT"},
            {"candidate_id": "CTRL-002", "sequence": "KWKLFKK2", "seed_family": "SEED-001",
             "panel_role": "SAR_CONTROL", "novelty_class": "KNOWN_VARIANT"},
            {"candidate_id": "CTRL-003", "sequence": "KWKLFKK3", "seed_family": "SEED-001",
             "panel_role": "SAR_CONTROL", "novelty_class": "KNOWN_VARIANT"},
        ]
        # Add enough families for W0.5-1 but this test only checks W0.5-2
        for i in range(8):
            rows.append({"candidate_id": f"S{i:03d}_001", "sequence": "AKRK", "seed_family": f"SEED-{20+i:03d}",
                         "panel_role": "BALANCED_LEAD", "novelty_class": "HIGH_CONFIDENCE_NOVEL"})
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_2_family_redundancy(p)
        assert result.status == "PASS"


# ---------------------------------------------------------------------------
# Gate W0.5-3: Activity Consensus
# ---------------------------------------------------------------------------
class TestGateW053ActivityConsensus:
    def test_pending_when_all_rows_pending(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "PENDING",
             "hemofinder_risk": "PENDING", "anticp2_class": "PENDING"}
            for i in range(10)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_3_activity_consensus(p)
        assert result.status == "PENDING"

    def test_pass_when_majority_strong(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "STRONG_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "NOT_ACP"}
            for i in range(8)
        ] + [
            {"candidate_id": f"W{i}", "activity_consensus": "WEAK_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "NOT_ACP"}
            for i in range(2)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_3_activity_consensus(p)
        assert result.status == "PASS"

    def test_fail_when_minority_strong(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "STRONG_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "NOT_ACP"}
            for i in range(5)
        ] + [
            {"candidate_id": f"W{i}", "activity_consensus": "WEAK_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "NOT_ACP"}
            for i in range(5)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_3_activity_consensus(p)
        assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# Gate W0.5-4: Safety Annotation
# ---------------------------------------------------------------------------
class TestGateW054SafetyAnnotation:
    def test_pending_when_all_hemofinder_pending(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "STRONG_ACTIVITY",
             "hemofinder_risk": "PENDING", "anticp2_class": "PENDING"}
            for i in range(5)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_4_safety_annotation(p)
        assert result.status == "PENDING"

    def test_pass_when_all_annotated(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "STRONG_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "NOT_ACP"}
            for i in range(5)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_4_safety_annotation(p)
        assert result.status == "PASS"

    def test_pending_when_only_anticp_missing(self, tmp_path):
        rows = [
            {"candidate_id": f"S{i}", "activity_consensus": "STRONG_ACTIVITY",
             "hemofinder_risk": "LOW", "anticp2_class": "PENDING"}
            for i in range(5)
        ]
        p = tmp_path / "consensus.csv"
        _write_csv(p, CONSENSUS_FIELDNAMES, rows)
        result = check_w05_4_safety_annotation(p)
        assert result.status == "PENDING"


# ---------------------------------------------------------------------------
# Gate W0.5-5: Novelty Qualification
# ---------------------------------------------------------------------------
class TestGateW055NoveltyQualification:
    def test_pass_with_enough_novel_leads(self, tmp_path):
        panel_rows = [
            {"candidate_id": f"S{i}", "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "panel_role": "BALANCED_LEAD", "novelty_class": "HIGH_CONFIDENCE_NOVEL"}
            for i in range(10)
        ]
        novelty_rows = [
            {"candidate_id": f"S{i}", "novelty_class": "HIGH_CONFIDENCE_NOVEL",
             "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "best_database": "N/A", "best_hit_id": "NONE", "best_hit_sequence": "N/A",
             "best_identity": "0.1", "best_similarity": "0.1",
             "patent_risk": "LOW", "action": "LEAD_CANDIDATE", "shortlist_role": "PASS"}
            for i in range(10)
        ]
        fp = tmp_path / "panel.csv"
        np = tmp_path / "novelty.csv"
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)
        _write_csv(np, NOVELTY_FIELDNAMES, novelty_rows)
        result = check_w05_5_novelty_qualification(np, fp)
        assert result.status == "PASS"

    def test_fail_when_all_known_variants(self, tmp_path):
        panel_rows = [
            {"candidate_id": f"S{i}", "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "panel_role": "BALANCED_LEAD", "novelty_class": "KNOWN_VARIANT"}
            for i in range(5)
        ]
        novelty_rows = [
            {"candidate_id": f"S{i}", "novelty_class": "KNOWN_VARIANT",
             "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "best_database": "N/A", "best_hit_id": "REF-001", "best_hit_sequence": "AKRK",
             "best_identity": "0.9", "best_similarity": "0.9",
             "patent_risk": "REVIEW_REQUIRED", "action": "CONTROL/SAR_ONLY", "shortlist_role": "PASS"}
            for i in range(5)
        ]
        fp = tmp_path / "panel.csv"
        np = tmp_path / "novelty.csv"
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)
        _write_csv(np, NOVELTY_FIELDNAMES, novelty_rows)
        result = check_w05_5_novelty_qualification(np, fp)
        assert result.status == "FAIL"

    def test_pass_when_close_relative_qualifies(self, tmp_path):
        # CLOSE_RELATIVE is now included in NOVEL_CLASSES after v2 audit
        panel_rows = [
            {"candidate_id": f"S{i}", "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "panel_role": "BALANCED_LEAD", "novelty_class": "CLOSE_RELATIVE"}
            for i in range(8)
        ]
        novelty_rows = [
            {"candidate_id": f"S{i}", "novelty_class": "CLOSE_RELATIVE",
             "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "best_database": "public", "best_hit_id": "REF-001", "best_hit_sequence": "AKRKXXX",
             "best_identity": "0.70", "best_similarity": "0.70",
             "patent_risk": "CLEAR", "action": "KEEP_WITH_DISCLOSURE", "shortlist_role": "PASS"}
            for i in range(8)
        ]
        fp = tmp_path / "panel.csv"
        np = tmp_path / "novelty.csv"
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)
        _write_csv(np, NOVELTY_FIELDNAMES, novelty_rows)
        result = check_w05_5_novelty_qualification(np, fp)
        assert result.status == "PASS"

    def test_controls_excluded_from_novel_count(self, tmp_path):
        # Controls labeled POSITIVE_CONTROL with HIGH_CONFIDENCE_NOVEL should not count
        panel_rows = [
            {"candidate_id": "CTRL", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "POSITIVE_CONTROL", "novelty_class": "KNOWN_VARIANT"},
        ] + [
            {"candidate_id": f"S{i}", "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "panel_role": "BALANCED_LEAD", "novelty_class": "HIGH_CONFIDENCE_NOVEL"}
            for i in range(9)   # only 9 actual leads → FAIL
        ]
        novelty_rows = [
            {"candidate_id": f"S{i}", "novelty_class": "HIGH_CONFIDENCE_NOVEL",
             "sequence": "AKRK", "seed_family": f"SEED-{10+i:03d}",
             "best_database": "N/A", "best_hit_id": "NONE", "best_hit_sequence": "N/A",
             "best_identity": "0.1", "best_similarity": "0.1",
             "patent_risk": "LOW", "action": "LEAD_CANDIDATE", "shortlist_role": "PASS"}
            for i in range(9)
        ]
        fp = tmp_path / "panel.csv"
        np = tmp_path / "novelty.csv"
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)
        _write_csv(np, NOVELTY_FIELDNAMES, novelty_rows)
        result = check_w05_5_novelty_qualification(np, fp)
        assert result.status == "PASS"  # 9 >= 8


# ---------------------------------------------------------------------------
# Gate W0.5-6: Control Integrity
# ---------------------------------------------------------------------------
class TestGateW056ControlIntegrity:
    def test_pass_when_known_variants_are_controls(self, tmp_path):
        rows = [
            {"candidate_id": "C1", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "POSITIVE_CONTROL", "novelty_class": "KNOWN_VARIANT"},
            {"candidate_id": "C2", "sequence": "AKRKFGYK", "seed_family": "SEED-010",
             "panel_role": "BALANCED_LEAD", "novelty_class": "HIGH_CONFIDENCE_NOVEL"},
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_6_control_integrity(p)
        assert result.status == "PASS"

    def test_fail_when_known_variant_labeled_as_lead(self, tmp_path):
        rows = [
            {"candidate_id": "BAD", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "BALANCED_LEAD", "novelty_class": "KNOWN_VARIANT"},
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_6_control_integrity(p)
        assert result.status == "FAIL"
        assert "BAD" in result.detail

    def test_fail_when_exact_match_labeled_as_lead(self, tmp_path):
        rows = [
            {"candidate_id": "EXACT", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "BALANCED_LEAD", "novelty_class": "EXACT_MATCH"},
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_6_control_integrity(p)
        assert result.status == "FAIL"

    def test_fail_when_exact_match_or_fragment_labeled_as_lead(self, tmp_path):
        # v2 novelty audit uses "EXACT_MATCH_OR_FRAGMENT" instead of "EXACT_MATCH"
        rows = [
            {"candidate_id": "EMF", "sequence": "GWGSFFKKAAHVGK", "seed_family": "SEED-013",
             "panel_role": "BALANCED_LEAD", "novelty_class": "EXACT_MATCH_OR_FRAGMENT"},
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_6_control_integrity(p)
        assert result.status == "FAIL"
        assert "EMF" in result.detail

    def test_high_upside_risky_of_known_variant_is_violation(self, tmp_path):
        rows = [
            {"candidate_id": "BAD2", "sequence": "KWKLFKK", "seed_family": "SEED-001",
             "panel_role": "HIGH_UPSIDE_RISKY", "novelty_class": "KNOWN_VARIANT"},
        ]
        p = tmp_path / "panel.csv"
        _write_csv(p, PANEL_FIELDNAMES, rows)
        result = check_w05_6_control_integrity(p)
        assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# Gate W0.5-7: Claim Safety
# ---------------------------------------------------------------------------
class TestGateW057ClaimSafety:
    def test_pass_with_clean_doc(self, tmp_path):
        doc = tmp_path / "safe.md"
        doc.write_text(
            "# Wave 0.5\n\n"
            "> Disclaimer: All scores are computational predictions. No wet-lab evidence.\n\n"
            "Candidates are scored by physicochemical heuristics.\n"
        )
        result = check_w05_7_claim_safety([doc])
        assert result.status == "PASS"

    def test_fail_on_unsupported_antibiotic_claim(self, tmp_path):
        doc = tmp_path / "bad.md"
        doc.write_text(
            "# Results\n\nThese peptides are antibiotics with proven activity.\n"
        )
        result = check_w05_7_claim_safety([doc])
        assert result.status == "FAIL"

    def test_no_violation_in_disclaimer_context(self, tmp_path):
        doc = tmp_path / "ok.md"
        doc.write_text(
            "# Wave 0.5\n\n"
            "Disclaimer: Do not claim antibiotic or drug activity. All computational.\n\n"
            "This pipeline does not claim clinical utility.\n"
        )
        result = check_w05_7_claim_safety([doc])
        # Disclaimer context should prevent false positive
        assert result.status == "PASS"

    def test_nonexistent_doc_skipped(self, tmp_path):
        result = check_w05_7_claim_safety([tmp_path / "does_not_exist.md"])
        assert result.status == "PASS"


# ---------------------------------------------------------------------------
# Integration: run_all_gates with real outputs
# ---------------------------------------------------------------------------
class TestRunAllGates:
    def test_gates_return_seven_results(self, tmp_path):
        # Create minimal valid files
        fp = tmp_path / "panel.csv"
        cp = tmp_path / "consensus.csv"
        np_ = tmp_path / "novelty.csv"

        panel_rows = _make_panel(n_families=8)
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)

        consensus_rows = [{"candidate_id": f"S{i}", "activity_consensus": "PENDING",
                           "hemofinder_risk": "PENDING", "anticp2_class": "PENDING"}
                          for i in range(5)]
        _write_csv(cp, CONSENSUS_FIELDNAMES, consensus_rows)

        novelty_rows = [
            {"candidate_id": row["candidate_id"], "novelty_class": row["novelty_class"],
             "sequence": row["sequence"], "seed_family": row["seed_family"],
             "best_database": "N/A", "best_hit_id": "NONE", "best_hit_sequence": "N/A",
             "best_identity": "0.1", "best_similarity": "0.1",
             "patent_risk": "LOW", "action": "LEAD_CANDIDATE", "shortlist_role": "PASS"}
            for row in panel_rows
        ]
        _write_csv(np_, NOVELTY_FIELDNAMES, novelty_rows)

        results = run_all_gates(
            final_panel_path=fp,
            consensus_path=cp,
            novelty_path=np_,
            doc_paths=[],
        )
        assert len(results) == 7
        assert all(isinstance(r, W05GateResult) for r in results)

    def test_gate_ids_are_correct(self, tmp_path):
        fp = tmp_path / "panel.csv"
        cp = tmp_path / "consensus.csv"
        np_ = tmp_path / "novelty.csv"

        panel_rows = _make_panel(n_families=8)
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)
        _write_csv(cp, CONSENSUS_FIELDNAMES, [])
        novelty_rows = [
            {"candidate_id": row["candidate_id"], "novelty_class": row["novelty_class"],
             "sequence": row["sequence"], "seed_family": row["seed_family"],
             "best_database": "N/A", "best_hit_id": "NONE", "best_hit_sequence": "N/A",
             "best_identity": "0.1", "best_similarity": "0.1",
             "patent_risk": "LOW", "action": "LEAD_CANDIDATE", "shortlist_role": "PASS"}
            for row in panel_rows
        ]
        _write_csv(np_, NOVELTY_FIELDNAMES, novelty_rows)

        results = run_all_gates(
            final_panel_path=fp,
            consensus_path=cp,
            novelty_path=np_,
            doc_paths=[],
        )
        expected_ids = ["W0.5-1", "W0.5-2", "W0.5-3", "W0.5-4", "W0.5-5", "W0.5-6", "W0.5-7"]
        assert [r.gate for r in results] == expected_ids

    def test_deterministic_fixture_passes_available_gates(self, tmp_path):
        """Hermetic equivalent of the old "real outputs" integration test.

        The previous version of this test read
        `outputs/wave1_final_panel.csv`, `outputs/wave0_5_external_consensus.csv`,
        and `outputs/wave0_5_novelty_audit.csv` directly from the repo's
        gitignored `outputs/` directory (see `.gitignore:80`, `outputs/*`).
        Those files are not checked into git, are not regenerated by `make
        demo` or CI, and are routinely overwritten by whichever pipeline run
        last touched the local `outputs/` directory. On a clean checkout the
        test skipped silently; on a machine with stale or concurrently-written
        `outputs/` files (e.g. multiple agents sharing a checkout) it could
        assert PASS/FAIL against arbitrary, non-reproducible local state and
        fail without any code or data regression in the repo itself.

        This test replaces that ambient-filesystem dependency with a
        deterministic, self-contained fixture built the same way the unit
        tests above build theirs. It proves `run_all_gates()` returns PASS
        for every N/A-safe gate on a well-formed Wave 0.5 panel, with zero
        dependency on machine-local state.
        """
        fp = tmp_path / "panel.csv"
        cp = tmp_path / "consensus.csv"
        np_ = tmp_path / "novelty.csv"

        panel_rows = _make_panel(n_families=MIN_FAMILIES)
        _write_csv(fp, PANEL_FIELDNAMES, panel_rows)

        consensus_rows = [
            {
                "candidate_id": row["candidate_id"],
                "activity_consensus": "STRONG_ACTIVITY",
                "hemofinder_risk": "LOW",
                "anticp2_class": "Non-AntiCP",
            }
            for row in panel_rows
        ]
        _write_csv(cp, CONSENSUS_FIELDNAMES, consensus_rows)

        novelty_rows = [
            {
                "candidate_id": row["candidate_id"],
                "sequence": row["sequence"],
                "seed_family": row["seed_family"],
                "best_database": "curated_27k",
                "best_hit_id": "NONE",
                "best_hit_sequence": "N/A",
                "best_identity": "0.2",
                "best_similarity": "0.2",
                "novelty_class": row["novelty_class"],
                "patent_risk": "LOW",
                "action": "LEAD_CANDIDATE",
                "shortlist_role": "PASS",
            }
            for row in panel_rows
        ]
        _write_csv(np_, NOVELTY_FIELDNAMES, novelty_rows)

        results = run_all_gates(
            final_panel_path=fp, consensus_path=cp, novelty_path=np_, doc_paths=[]
        )
        results_by_id = {r.gate: r for r in results}

        assert results_by_id["W0.5-1"].status == "PASS"
        assert results_by_id["W0.5-2"].status == "PASS"
        # W0.5-3 and W0.5-4 may be PENDING (external predictors)
        assert results_by_id["W0.5-3"].status in ("PASS", "PENDING")
        assert results_by_id["W0.5-4"].status in ("PASS", "PENDING")
        assert results_by_id["W0.5-5"].status == "PASS"
        assert results_by_id["W0.5-6"].status == "PASS"
        assert results_by_id["W0.5-7"].status == "PASS"

    def test_local_outputs_smoke_check_never_fails_suite(self, capsys):
        """Best-effort visibility into local `outputs/` artifacts, non-blocking.

        `outputs/` is gitignored and machine-local (see docstring above). If a
        contributor has generated real Wave 0.5 outputs locally, print their
        gate status for visibility, but never assert on them — asserting on
        ambient filesystem state outside git's control is exactly the
        reproducibility failure this test class exists to avoid repeating.
        """
        root = Path(__file__).resolve().parent.parent
        fp = root / "outputs" / "wave1_final_panel.csv"
        cp = root / "outputs" / "wave0_5_external_consensus.csv"
        np_ = root / "outputs" / "wave0_5_novelty_audit.csv"

        if not fp.exists() or not cp.exists() or not np_.exists():
            pytest.skip("Wave 0.5 outputs not present locally (expected on a clean checkout)")

        results = run_all_gates(final_panel_path=fp, consensus_path=cp, novelty_path=np_)
        for r in results:
            print(f"[local outputs, informational only] {r.gate}: {r.status} ({r.value})")
        assert len(results) == 7
