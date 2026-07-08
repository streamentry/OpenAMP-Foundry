from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.quality import assess_certificate_quality
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate

_SCHEMA = str(Path(__file__).parents[2] / "schemas" / "candidate.schema.json")


def _make_good_cert() -> dict:
    candidate = PeptideCandidate("AMPF-QTEST", "KWKLFKKIGAVLKVL", "test")
    scored = ScoredCandidate(
        candidate=candidate,
        features=compute_features(candidate.sequence),
        scores={"activity": 0.8, "safety": 0.9, "synthesis": 0.9, "novelty": 0.5, "ensemble": 0.8},
        selection_reason=["Top-ranked ensemble score"],
        known_failure_modes=["No wet-lab assay has been run."],
    )
    return build_certificate(scored, {"weights": {}}, [])


class TestAssessCertificateQuality:
    def test_good_cert_passes(self):
        cert = _make_good_cert()
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "pass"
        assert result["error_count"] == 0

    def test_warn_on_empty_failure_modes(self):
        cert = _make_good_cert()
        cert["known_failure_modes"] = []
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "warn"
        assert any("empty" in w.lower() for w in result["warnings"])

    def test_warn_on_empty_selection_reason(self):
        cert = _make_good_cert()
        cert["selection_reason"] = []
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "warn"

    def test_warn_on_missing_disclaimer(self):
        cert = _make_good_cert()
        cert["recommended_next_steps"] = ["Some other step"]
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "warn"

    def test_warn_on_empty_features(self):
        cert = _make_good_cert()
        cert["features"] = {}
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "warn"

    def test_fail_on_missing_proof_ladder_level(self):
        cert = _make_good_cert()
        del cert["proof_ladder_level"]
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "fail"
        assert result["critical_errors"]

    def test_fail_on_invalid_proof_ladder_level(self):
        cert = _make_good_cert()
        cert["proof_ladder_level"] = "proven_drug"
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "fail"

    def test_fail_on_missing_required_scores(self):
        cert = _make_good_cert()
        del cert["scores"]["activity"]
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "fail"

    def test_fail_on_invalid_timestamp(self):
        cert = _make_good_cert()
        cert["generated_at"] = "not-a-timestamp"
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "fail"

    def test_fail_on_schema_violation(self):
        cert = _make_good_cert()
        del cert["candidate_id"]
        result = assess_certificate_quality(cert, _SCHEMA)
        assert result["tier"] == "fail"

    def test_cli_exit_0_for_good_cert(self, tmp_path):
        cert = _make_good_cert()
        p = tmp_path / "good.json"
        p.write_text(json.dumps(cert))
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "validate-cert-quality",
             "--certificate", str(p)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        output = json.loads(r.stdout)
        assert output["tier"] in ("pass", "warn")
        assert r.returncode == 0

    def test_cli_exit_3_for_fail(self, tmp_path):
        cert = _make_good_cert()
        del cert["proof_ladder_level"]
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(cert))
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "validate-cert-quality",
             "--certificate", str(p)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 3
