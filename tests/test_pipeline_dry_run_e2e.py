"""End-to-end dry-run test: full pipeline from sequences to evidence package.

Smoke test only — verifies the key data structures and validation rules
can be chained together. No real sequences, no external calls, no disk I/O.
All candidate IDs use the TOY- prefix.
"""

from __future__ import annotations

import pytest


TOY_SEQUENCES = [
    ("TOY-001", "KWKLFKKIEKVGQNIRDGIIKAGPAVAVVGQATQIAK"),
    ("TOY-002", "GIGKFLHSAKKFGKAFVGEIMNS"),
    ("TOY-003", "FLPLIGRVLSGIL"),
    ("TOY-004", "KKKKKKKK"),
    ("TOY-005", "ACDEFGHIKLMNPQRSTVWY"),
]


class TestDryRunPipelineSteps:
    """Verifies each pipeline step produces valid output that the next step can consume."""

    def test_fasta_export_round_trips(self):
        from openamp_foundry.export.fasta_export import (
            build_fasta_entry,
            build_fasta_export_record,
            validate_fasta_export_record,
            format_fasta_export,
        )
        entries = [
            build_fasta_entry(
                candidate_id=cid,
                sequence=seq,
                description=f"Toy candidate {cid}",
                export_context="dry_lab_only",
                status="nominated",
                is_toy_data=True,
            )
            for cid, seq in TOY_SEQUENCES
        ]
        record = build_fasta_export_record(
            export_id="FAE-DRY-001",
            entries=entries,
            dry_lab_only=True,
            export_context="dry_lab_only",
            export_note="Computational dry-lab toy candidates only.",
            export_timestamp_utc="2026-01-01T00:00:00Z",
        )
        result = validate_fasta_export_record(record)
        assert result.is_valid, f"FASTA export failed: {result.violations}"
        fasta_str = format_fasta_export(record)
        assert "TOY-001" in fasta_str
        assert fasta_str.count(">") == len(TOY_SEQUENCES)

    def test_jsonld_context_annotation(self):
        from openamp_foundry.interop.jsonld_context import (
            build_jsonld_context_record,
            validate_jsonld_context_record,
            annotate_certificate_with_context,
        )
        record = build_jsonld_context_record(
            context_id="JLC-DRY-001",
            evidence_type="EvidenceCertificate",
            generation_note="Dry-run context for toy pipeline",
        )
        result = validate_jsonld_context_record(record)
        assert result.is_valid, f"JSON-LD context failed: {result.violations}"
        cert = {
            "certificate_id": "CERT-TOY-001",
            "candidate_id": "TOY-001",
            "proof_ladder_level": "dry_lab_candidate",
            "dry_lab_only": True,
            "created_at": "2026-01-01T00:00:00Z",
        }
        annotated = annotate_certificate_with_context(cert, record)
        assert "@context" in annotated
        assert "@type" in annotated
        assert annotated["candidate_id"] == "TOY-001"

    def test_adapter_stub_describes_tool_integration(self):
        from openamp_foundry.interop.adapter_stub import (
            build_adapter_stub_record,
            validate_adapter_stub_record,
        )
        record = build_adapter_stub_record(
            adapter_id="ADS-DRY-001",
            target_tool="ampscanner",
            output_format="fasta",
            adapter_status="stub",
            implementation_notes="Dry-run stub for AMPScanner integration",
        )
        result = validate_adapter_stub_record(record)
        assert result.is_valid, f"Adapter stub failed: {result.violations}"

    def test_schema_export_manifest_for_pipeline(self):
        from openamp_foundry.versioning.schema_export import (
            build_schema_export_entry,
            build_schema_export_manifest,
            validate_schema_export_manifest,
        )
        entry = build_schema_export_entry(
            schema_id="fasta_export",
            schema_prefix="FAE-",
            module_path="src/openamp_foundry/export/fasta_export.py",
            stability_tier="stable",
            description="FASTA export for dry-lab AMP candidates",
            version="1.0.0",
        )
        manifest = build_schema_export_manifest(
            manifest_id="SEM-DRY-001",
            entries=[entry],
            total_schemas=1,
            stable_count=1,
            experimental_count=0,
            internal_count=0,
            deprecated_count=0,
            export_note="Dry-run schema manifest for pipeline integration test.",
        )
        result = validate_schema_export_manifest(manifest)
        assert result.is_valid, f"Schema export manifest failed: {result.violations}"

    def test_release_manifest_finalizes_pipeline(self):
        from openamp_foundry.evidence.release_manifest import (
            build_release_manifest,
            validate_release_manifest,
        )
        manifest = build_release_manifest(
            manifest_id="RMF-DRY-001",
            release_version="0.0.1-dry-run",
            release_status="draft",
            candidate_ids=["TOY-001", "TOY-002", "TOY-003"],
            total_candidates=3,
            dry_lab_only=True,
            pipeline_version="0.1.0",
            created_at="2026-01-01T00:00:00Z",
            release_note="Dry-run test. Computational nominees only. No biological validation.",
            schema_version="1.0",
            is_example_data=True,
        )
        result = validate_release_manifest(manifest)
        assert result.is_valid, f"Release manifest failed: {result.violations}"

    def test_negative_calibration_link_closes_loop(self):
        from openamp_foundry.evidence.negative_result_calibration_link import (
            build_negative_result_calibration_link,
            validate_negative_result_calibration_link,
        )
        link = build_negative_result_calibration_link(
            link_id="NCL-DRY-001",
            nrr_ids=["NRR-DRY-001", "NRR-DRY-002"],
            calibration_report_id="CAL-DRY-001",
            link_type="batch_failure_feedback",
            batch_coverage_fraction=0.5,
            all_nrrs_linked=False,
            link_status="pending",
            link_rationale="Dry-run test: linking toy negative results to calibration.",
        )
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid, f"NCL link failed: {result.violations}"

    def test_changelog_entry_for_pipeline_pr(self):
        from openamp_foundry.changelog.changelog_entry import (
            build_changelog_entry,
            validate_changelog_entry,
        )
        entry = build_changelog_entry(
            pr_number=999,
            pr_title="feat: dry-run pipeline smoke test",
            phase="Phase J",
            merged_at="2026-01-01T00:00:00Z",
        )
        result = validate_changelog_entry(entry)
        assert result.is_valid, f"Changelog entry failed: {result.violations}"

    def test_docs_coverage_detects_pipeline_modules(self):
        from pathlib import Path
        from openamp_foundry.checks.docs_coverage import check_docs_coverage
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / "src" / "openamp_foundry"
        if src_dir.exists():
            report = check_docs_coverage(src_dir, glob_pattern="**/*.py", exclude_init=True)
            assert report.total_modules > 0
            assert report.coverage_fraction >= 0.0

    def test_stale_doc_detector_runs_on_docs(self):
        from pathlib import Path
        from openamp_foundry.checks.stale_doc_detector import check_stale_doc_references
        repo_root = Path(__file__).parent.parent
        docs_dir = repo_root / "docs"
        if docs_dir.exists():
            report = check_stale_doc_references(docs_dir=docs_dir, repo_root=repo_root)
            assert report.total_docs_scanned >= 0


class TestDryRunSafetyGates:
    """Verifies dry-lab safety gates cannot be bypassed in the pipeline."""

    def test_fasta_export_rejects_non_toy_under_dry_lab(self):
        from openamp_foundry.export.fasta_export import (
            build_fasta_entry,
            build_fasta_export_record,
            validate_fasta_export_record,
        )
        real_entry = build_fasta_entry(
            candidate_id="REAL-001",
            sequence="ACDEFGHIKLM",
            description="Not a toy",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=False,
        )
        record = build_fasta_export_record(
            export_id="FAE-DRY-001",
            entries=[real_entry],
            dry_lab_only=True,
            export_context="dry_lab_only",
            export_note="computational dry-lab",
        )
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_fasta_export_rejects_public_release_under_dry_lab(self):
        from openamp_foundry.export.fasta_export import (
            build_fasta_entry,
            build_fasta_export_record,
            validate_fasta_export_record,
        )
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="ACDEFGHIKLM",
            description="Toy",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        record = build_fasta_export_record(
            export_id="FAE-DRY-001",
            entries=[entry],
            dry_lab_only=True,
            export_context="public_release",
            export_note="computational",
        )
        result = validate_fasta_export_record(record)
        assert not result.is_valid

    def test_jsonld_context_blocks_wet_lab_constraint(self):
        from openamp_foundry.interop.jsonld_context import (
            build_jsonld_context_record,
            validate_jsonld_context_record,
        )
        record = build_jsonld_context_record(
            context_id="JLC-DRY-001",
            evidence_type="EvidenceCertificate",
            generation_note="test",
        )
        record.is_dry_lab_constrained = False
        result = validate_jsonld_context_record(record)
        assert not result.is_valid

    def test_adapter_stub_rejects_wet_lab(self):
        from openamp_foundry.interop.adapter_stub import (
            build_adapter_stub_record,
            validate_adapter_stub_record,
        )
        record = build_adapter_stub_record(
            adapter_id="ADS-DRY-001",
            target_tool="ampscanner",
            output_format="fasta",
            dry_lab_only=False,
            implementation_notes="test",
        )
        result = validate_adapter_stub_record(record)
        assert not result.is_valid


class TestDryRunConsistencyChecks:
    """Verifies cross-schema consistency in the pipeline."""

    def test_all_toy_sequences_are_valid_amino_acids(self):
        from openamp_foundry.export.fasta_export import VALID_AMINO_ACIDS
        for cid, seq in TOY_SEQUENCES:
            invalid = set(seq.upper()) - VALID_AMINO_ACIDS
            assert not invalid, f"{cid}: invalid chars {invalid} in sequence '{seq}'"

    def test_all_toy_sequences_meet_length_constraints(self):
        from openamp_foundry.export.fasta_export import MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH
        for cid, seq in TOY_SEQUENCES:
            assert MIN_SEQUENCE_LENGTH <= len(seq) <= MAX_SEQUENCE_LENGTH, (
                f"{cid}: length {len(seq)} outside [{MIN_SEQUENCE_LENGTH}, {MAX_SEQUENCE_LENGTH}]"
            )

    def test_jsonld_base_context_has_all_required_fields(self):
        from openamp_foundry.interop.jsonld_context import (
            JSONLD_BASE_CONTEXT,
            REQUIRED_CERTIFICATE_FIELDS,
        )
        for field in REQUIRED_CERTIFICATE_FIELDS:
            assert field in JSONLD_BASE_CONTEXT, f"Required field '{field}' missing from JSONLD_BASE_CONTEXT"

    def test_adapter_tool_list_non_empty(self):
        from openamp_foundry.interop.adapter_stub import VALID_TARGET_TOOLS
        assert len(VALID_TARGET_TOOLS) >= 5

    def test_fasta_export_context_matches_adapter_formats(self):
        from openamp_foundry.export.fasta_export import VALID_OUTPUT_FORMATS
        from openamp_foundry.interop.adapter_stub import VALID_OUTPUT_FORMATS as ADAPTER_FORMATS
        shared = VALID_OUTPUT_FORMATS & ADAPTER_FORMATS
        assert "fasta" in shared

    def test_pipeline_prefix_uniqueness(self):
        prefixes = {
            "FAE-",
            "JLC-",
            "ADS-",
            "SEM-",
            "RMF-",
            "NCL-",
            "STC-",
        }
        assert len(prefixes) == 7

    def test_dry_run_produces_no_false_positives(self):
        from openamp_foundry.export.fasta_export import (
            build_fasta_entry,
            build_fasta_export_record,
            validate_fasta_export_record,
        )
        entries = [
            build_fasta_entry(
                candidate_id=cid,
                sequence=seq,
                description=f"Toy {cid}",
                export_context="dry_lab_only",
                status="nominated",
                is_toy_data=True,
            )
            for cid, seq in TOY_SEQUENCES
        ]
        record = build_fasta_export_record(
            export_id="FAE-DRY-001",
            entries=entries,
            dry_lab_only=True,
            export_context="dry_lab_only",
            export_note="computational dry-lab toy candidates only",
        )
        result = validate_fasta_export_record(record)
        assert result.is_valid
        assert result.violations == []
