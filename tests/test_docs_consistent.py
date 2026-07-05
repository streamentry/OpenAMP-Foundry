"""Verify doc consistency: no stale benchmark numbers, no conflicting claims."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# Current authoritative benchmark values — single source of truth
CURRENT_AUROC = "0.7832"
CURRENT_PHASE3_AUROC = "0.7448"
CURRENT_N_POSITIVES = 95
CURRENT_N_NEGATIVES = 96
CURRENT_N_TOTAL = 191
EXPANDED_PR_REF = "PR #110"
ORIGINAL_DEMO_AUROC = "0.8420"
SNAPSHOT_PATH = REPO_ROOT / "outputs" / "metrics_snapshot.json"
WAVE05_GENERATED_OUTPUTS = [
    REPO_ROOT / "outputs" / "wave0_5_external_predict_results.csv",
    REPO_ROOT / "outputs" / "wave0_5_external_consensus.csv",
    REPO_ROOT / "outputs" / "wave0_5_safety_consensus.csv",
]

# Patterns that indicate stale "current" usage (not historical context)
_STALE_CURRENT_PATTERNS: list[str] = [
    # "AUROC = 0.8420" used as current without "original demo" qualifier
    r"(?<!original demo set )(?<!historical baseline: )AUROC = 0\.8420",
    # "AUROC 0.8420" as current benchmark claim (not historical progression)
    r"(?<!demo set )AUROC 0\.8420(?!.*demo)(?!.*historical)(?!.*original)(?!.*baseline)",
    # "n=87" as current benchmark size — match only when preceded by start of line or whitespace (not parenthetical)
    r"(?<!\()n=87(?!\s*\)|\s*was|\s*actually)",
    # "43 AMPs + 44 background" as current benchmark
    r"(?<!original )(?<!demo )(?<!historical baseline: )43 AMPs.*44 background",
]


def _ignored_path(path: Path) -> bool:
    """Paths where stale patterns are acceptable (CHANGELOG, generated outputs)."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    return any(
        ignore in rel
        for ignore in [
            ".venv/",
            "node_modules/",
            "outputs/gold_standard_calibration.md",
            "CHANGELOG.md",
        ]
    )


def _collect_md_files() -> list[Path]:
    md_files = list(DOCS_DIR.rglob("*.md"))
    # Also check README.md at root
    root_readme = REPO_ROOT / "README.md"
    if root_readme.exists():
        md_files.append(root_readme)
    return [f for f in md_files if not _ignored_path(f)]


class TestDocsConsistent:
    """All test methods prefixed test_doc_ so they're easy to filter."""

    def test_doc_current_auroc_consistent_across_all_docs(self):
        """Every doc that mentions a current AUROC must reference the expanded benchmark."""
        errors = []
        for md_file in _collect_md_files():
            text = md_file.read_text(encoding="utf-8")
            # If the file mentions any AUROC value, check it's not stale
            for i, pattern in enumerate(_STALE_CURRENT_PATTERNS):
                matches = re.findall(pattern, text)
                if matches:
                    # Only flag if the file uses AUROC as current-state (not historical timeline)
                    # Check if "current" or present-tense references exist without qualifiers
                    if not re.search(
                        r"(historical|original demo|baseline|PR.*#\d+|progression)",
                        text[: min(500, len(text))],
                    ):
                        errors.append(
                            f"{md_file.relative_to(REPO_ROOT)}: "
                            f"possible stale benchmark text matching pattern {i}: "
                            f"{matches[0][:80]}"
                        )
        assert not errors, "\n".join(errors[:5])

    def test_doc_metrics_current_md_is_authoritative(self):
        """METRICS_CURRENT.md must exist and contain current AUROC."""
        metrics = DOCS_DIR / "METRICS_CURRENT.md"
        assert metrics.exists(), "docs/METRICS_CURRENT.md not found"
        text = metrics.read_text(encoding="utf-8")
        assert CURRENT_AUROC in text, (
            f"METRICS_CURRENT.md missing current AUROC {CURRENT_AUROC}"
        )
        assert str(CURRENT_N_TOTAL) in text, (
            f"METRICS_CURRENT.md missing n={CURRENT_N_TOTAL}"
        )

    def test_doc_metrics_snapshot_matches_authoritative_values(self):
        """Machine-readable metrics snapshot must agree with docs' current truth."""
        assert SNAPSHOT_PATH.exists(), "outputs/metrics_snapshot.json not found"
        payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert payload["standard"]["auroc"] == float(CURRENT_AUROC)
        assert payload["phase3"]["auroc"] == float(CURRENT_PHASE3_AUROC)
        assert payload["standard"]["n_positives"] == CURRENT_N_POSITIVES
        assert payload["standard"]["n_negatives"] == CURRENT_N_NEGATIVES
        assert payload["standard"]["n_total"] == CURRENT_N_TOTAL

    def test_doc_metrics_snapshot_includes_ranking_policy(self):
        """Snapshot must encode the current ranking recommendation contract."""
        payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert payload["ranking_policy"]["default"]["mode"] == "ensemble"
        assert payload["ranking_policy"]["alternative"]["mode"] == "expert"
        assert payload["ranking_policy"]["default"]["evidence_basis"]
        assert payload["ranking_policy"]["alternative"]["evidence_basis"]

    def test_doc_no_breaking_news_terminology(self):
        """'breaking news' must be replaced with 'high-impact scenario' in all docs."""
        breaking = re.compile(r"breaking[-\s]news", re.IGNORECASE)
        errors = []
        for md_file in _collect_md_files():
            text = md_file.read_text(encoding="utf-8")
            if breaking.search(text):
                # Allow in CHANGELOG (historical entries) and METRICS (if any)
                rel = md_file.relative_to(REPO_ROOT).as_posix()
                if "CHANGELOG" not in rel and "METRICS_CURRENT" not in rel:
                    errors.append(f"{rel}: contains 'breaking news'")
        assert not errors, "\n".join(errors[:5])

    def test_doc_no_overconfident_probability_claims(self):
        """No doc should claim '92-97%' as the primary probability without honesty correction."""
        overconfident = re.compile(r"9[0-9]%[^)]*active hit|92.*97%", re.IGNORECASE)
        errors = []
        for md_file in _collect_md_files():
            if _ignored_path(md_file):
                continue
            text = md_file.read_text(encoding="utf-8")
            # Only flag if not followed by an honest correction within the same section
            matches = overconfident.findall(text)
            for m in matches:
                # Check if the surrounding context has a correction
                idx = text.find(m)
                chunk = text[idx : idx + 500]
                if "honest" not in chunk.lower() and "upper bound" not in chunk.lower() and "unvalidated" not in chunk.lower():
                    rel = md_file.relative_to(REPO_ROOT).as_posix()
                    errors.append(f"{rel}: overconfident probability claim '{m[:60]}'")
                    break
        assert not errors, "\n".join(errors[:5])

    def test_doc_wet_lab_probability_has_honest_correction(self):
        """WET_LAB_PROBABILITY.md must contain an honest lower-bound estimate."""
        path = DOCS_DIR / "WET_LAB_PROBABILITY.md"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "55–80%" in text or "55-80" in text or "honest" in text.lower(), (
            "WET_LAB_PROBABILITY.md missing honest correction range"
        )

    def test_doc_wave05_generated_outputs_claimed_only_if_present(self):
        """Docs must not present missing Wave 0.5 generated CSVs as committed facts."""
        files_present = all(path.exists() for path in WAVE05_GENERATED_OUTPUTS)

        metrics_text = (DOCS_DIR / "METRICS_CURRENT.md").read_text(encoding="utf-8")
        summary_text = (DOCS_DIR / "WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md").read_text(
            encoding="utf-8"
        )

        if not files_present:
            assert "Machine-readable: `outputs/wave0_5_external_predict_results.csv`" not in metrics_text
            assert "PENDING (60 rows, all PENDING)" not in summary_text
            assert "Generated only after running `make wave0-5-fill-external`" in summary_text

    def test_doc_wave05_historical_docs_do_not_pose_as_live_pending_state(self):
        """Historical Wave 0.5 docs must label superseded pending steps as historical."""
        baseline_text = (DOCS_DIR / "WAVE_0_5_BASELINE.md").read_text(encoding="utf-8")
        scaffold_text = (DOCS_DIR / "WAVE_0_5_SCAFFOLD_DIVERSIFICATION_PLAN.md").read_text(
            encoding="utf-8"
        )
        prereg_text = (DOCS_DIR / "ASSAY_PREREGISTRATION.md").read_text(encoding="utf-8")
        checklist_text = (DOCS_DIR / "PRE_WET_LAB_CHECKLIST.md").read_text(encoding="utf-8")
        wave1_text = (DOCS_DIR / "WAVE_1_PANEL_RECOMMENDATION.md").read_text(encoding="utf-8")

        assert "Historical note: this baseline freeze predates the completed Wave 0.5 external screen." in baseline_text
        assert "Historical baseline state only" in baseline_text
        assert "External predictor screen (all 60 shortlist) | COMPLETE" in scaffold_text
        assert "Wave 0.5 Gate W0.5-3 (activity consensus) | COMPLETE" in scaffold_text
        assert "Historical placeholder; external predictor review later completed" in prereg_text
        assert "The external predictor portion has since been completed" in checklist_text
        assert "External predictor review for Wave 0.5 was completed after this panel recommendation was first drafted." in wave1_text

    def test_doc_external_predictor_gate_distinguishes_generic_from_wave05(self):
        """Live docs must not imply the completed Wave 0.5 screen is still wholly pending."""
        consensus_text = (DOCS_DIR / "EXTERNAL_PREDICTOR_CONSENSUS.md").read_text(
            encoding="utf-8"
        )
        decision_text = (DOCS_DIR / "DECISION_RULES.md").read_text(encoding="utf-8")
        reviewer_text = (DOCS_DIR / "REVIEWER_SUMMARY.md").read_text(encoding="utf-8")
        roadmap_text = (DOCS_DIR / "ROADMAP.md").read_text(encoding="utf-8")
        expert_text = (DOCS_DIR / "EXPERT_REVIEW_PACK.md").read_text(encoding="utf-8")

        assert "generic pilot-panel consensus workflow" in consensus_text
        assert "Wave 0.5 activity consensus" in consensus_text
        assert "three activity predictors" in consensus_text
        assert "generic 5-tool" in consensus_text
        assert "Wave 0.5 remains wholly pending" in consensus_text
        assert "PENDING (see `outputs/external_predict_checklist.md`)" not in decision_text
        assert "generic Gate 6" in decision_text
        assert "completed Wave 0.5 external" in decision_text
        assert "No external predictor ensemble yet" not in reviewer_text
        assert "Wave 0.5 external screen is complete" in reviewer_text
        assert "web submissions pending" not in roadmap_text
        assert "Wave 0.5 complete; generic future-panel Gate 6 remains panel-specific" in roadmap_text
        assert "CAMPR4 was excluded" in expert_text


class TestFeatureDecompositionDocsConsistent:
    """Guard against drift between feature decomposition docs and reality."""

    def test_metrics_current_has_feature_decomposition_section(self):
        text = (DOCS_DIR / "METRICS_CURRENT.md").read_text(encoding="utf-8")
        assert "Feature Decomposition" in text
        assert "hydrophobic_fraction" in text
        assert "0.6745" in text

    def test_roadmap_has_v0515_entry(self):
        text = (DOCS_DIR / "ROADMAP.md").read_text(encoding="utf-8")
        assert "v0.5.15" in text
        assert "Feature Decomposition Benchmark" in text
        assert "feature_decomp.py" in text

    def test_metrics_current_last_updated_is_2026_07_03(self):
        text = (DOCS_DIR / "METRICS_CURRENT.md").read_text(encoding="utf-8")
        assert "2026-07-03" in text
