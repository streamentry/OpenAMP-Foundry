"""Tests for A8 toy pipeline output examples (tests/test_toy_examples.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


_TOY_DIR = Path(__file__).parent.parent / "examples" / "toy_pipeline_output"
_RANKED_FILE = _TOY_DIR / "toy_ranked_example.jsonl"
_CERT_FILE = _TOY_DIR / "toy_certificate_example.json"
_README_FILE = _TOY_DIR / "README.md"


class TestToyDirectoryExists:
    def test_toy_dir_exists(self):
        assert _TOY_DIR.is_dir()

    def test_ranked_file_exists(self):
        assert _RANKED_FILE.exists()

    def test_cert_file_exists(self):
        assert _CERT_FILE.exists()

    def test_readme_exists(self):
        assert _README_FILE.exists()

    def test_toy_dir_has_files(self):
        files = list(_TOY_DIR.iterdir())
        assert len(files) >= 3


class TestToyReadme:
    def test_readme_nonempty(self):
        content = _README_FILE.read_text()
        assert len(content) > 0

    def test_readme_mentions_toy(self):
        content = _README_FILE.read_text().lower()
        assert "toy" in content

    def test_readme_mentions_not_real(self):
        content = _README_FILE.read_text()
        assert "NOT" in content or "not real" in content.lower()

    def test_readme_mentions_toy_ranked(self):
        content = _README_FILE.read_text()
        assert "toy_ranked_example" in content

    def test_readme_mentions_toy_certificate(self):
        content = _README_FILE.read_text()
        assert "toy_certificate_example" in content

    def test_readme_dry_lab_mentioned(self):
        content = _README_FILE.read_text().lower()
        assert "dry-lab" in content or "dry_lab" in content


class TestToyRankedFile:
    def _load_lines(self):
        lines = []
        with _RANKED_FILE.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(json.loads(line))
        return lines

    def test_file_is_valid_jsonl(self):
        lines = self._load_lines()
        assert len(lines) > 0

    def test_has_multiple_candidates(self):
        lines = self._load_lines()
        assert len(lines) >= 2

    def test_all_ids_have_toy_prefix(self):
        lines = self._load_lines()
        for obj in lines:
            assert obj["candidate_id"].startswith("TOY-"), \
                f"Expected TOY- prefix, got {obj['candidate_id']}"

    def test_all_have_sequence_field(self):
        lines = self._load_lines()
        for obj in lines:
            assert "sequence" in obj

    def test_sequences_are_uppercase(self):
        lines = self._load_lines()
        for obj in lines:
            assert obj["sequence"] == obj["sequence"].upper()

    def test_sequences_are_nonempty(self):
        lines = self._load_lines()
        for obj in lines:
            assert len(obj["sequence"]) > 0

    def test_all_have_scores_field(self):
        lines = self._load_lines()
        for obj in lines:
            assert "scores" in obj

    def test_all_have_valid_field(self):
        lines = self._load_lines()
        for obj in lines:
            assert "valid" in obj

    def test_all_have_selected_field(self):
        lines = self._load_lines()
        for obj in lines:
            assert "selected" in obj

    def test_all_have_dry_lab_only_true(self):
        lines = self._load_lines()
        for obj in lines:
            assert obj.get("dry_lab_only") is True

    def test_all_have_known_failure_modes(self):
        lines = self._load_lines()
        for obj in lines:
            assert "known_failure_modes" in obj
            assert len(obj["known_failure_modes"]) > 0

    def test_activity_score_in_range(self):
        lines = self._load_lines()
        for obj in lines:
            score = obj["scores"]["activity"]
            assert 0.0 <= score <= 1.0

    def test_safety_score_in_range(self):
        lines = self._load_lines()
        for obj in lines:
            score = obj["scores"]["safety"]
            assert 0.0 <= score <= 1.0

    def test_novelty_score_in_range(self):
        lines = self._load_lines()
        for obj in lines:
            score = obj["scores"]["novelty"]
            assert 0.0 <= score <= 1.0

    def test_hemolysis_risk_in_range(self):
        lines = self._load_lines()
        for obj in lines:
            score = obj["scores"]["hemolysis_risk"]
            assert 0.0 <= score <= 1.0

    def test_source_is_toy(self):
        lines = self._load_lines()
        for obj in lines:
            assert obj.get("source") == "toy"

    def test_no_real_ampf_ids(self):
        lines = self._load_lines()
        for obj in lines:
            assert not obj["candidate_id"].startswith("AMPF-")

    def test_selected_candidates_have_selection_reason(self):
        lines = self._load_lines()
        for obj in lines:
            if obj["selected"]:
                assert len(obj.get("selection_reason", [])) > 0

    def test_failure_modes_mention_no_wet_lab(self):
        lines = self._load_lines()
        for obj in lines:
            modes_text = " ".join(obj["known_failure_modes"]).lower()
            assert "wet-lab" in modes_text or "assay" in modes_text


class TestToyCertificate:
    def _load(self):
        with _CERT_FILE.open() as f:
            return json.load(f)

    def test_cert_is_valid_json(self):
        cert = self._load()
        assert isinstance(cert, dict)

    def test_cert_id_has_toy_prefix(self):
        cert = self._load()
        assert cert["cert_id"].startswith("TOY-")

    def test_candidate_id_has_toy_prefix(self):
        cert = self._load()
        assert cert["candidate_id"].startswith("TOY-")

    def test_dry_lab_only_is_true(self):
        cert = self._load()
        assert cert["dry_lab_only"] is True

    def test_has_unsupported_claims(self):
        cert = self._load()
        assert "unsupported_claims" in cert
        assert len(cert["unsupported_claims"]) > 0

    def test_in_vitro_in_unsupported(self):
        cert = self._load()
        assert "in_vitro_activity" in cert["unsupported_claims"]

    def test_in_vivo_in_unsupported(self):
        cert = self._load()
        assert "in_vivo_efficacy" in cert["unsupported_claims"]

    def test_proof_ladder_level_present(self):
        cert = self._load()
        assert "proof_ladder_level" in cert

    def test_proof_ladder_not_validated(self):
        cert = self._load()
        level = cert["proof_ladder_level"]
        assert "clinical" not in level
        assert "validated" not in level

    def test_has_baseline_caveat(self):
        cert = self._load()
        assert "baseline_caveat" in cert
        assert len(cert["baseline_caveat"]) > 0

    def test_has_known_failure_modes(self):
        cert = self._load()
        assert "known_failure_modes" in cert
        assert len(cert["known_failure_modes"]) > 0

    def test_has_scores(self):
        cert = self._load()
        assert "scores" in cert

    def test_has_sequence(self):
        cert = self._load()
        assert "sequence" in cert

    def test_sequence_uppercase(self):
        cert = self._load()
        assert cert["sequence"] == cert["sequence"].upper()

    def test_has_run_id(self):
        cert = self._load()
        assert "run_id" in cert

    def test_run_id_toy_prefix(self):
        cert = self._load()
        assert cert["run_id"].startswith("TOY-")

    def test_claim_class_present(self):
        cert = self._load()
        assert "claim_class" in cert

    def test_claim_class_not_biological_proof(self):
        cert = self._load()
        claim = cert["claim_class"]
        assert "biological_proof" not in claim
        assert "validated" not in claim

    def test_no_real_candidate_ids(self):
        cert = self._load()
        assert not cert["candidate_id"].startswith("AMPF-")
        assert not cert["cert_id"].startswith("AMPF-")
