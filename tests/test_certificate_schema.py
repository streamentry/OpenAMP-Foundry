from pathlib import Path

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate

_SCHEMA = Path(__file__).parents[1] / "schemas" / "candidate.schema.json"


def test_certificate_validates():
    candidate = PeptideCandidate("AMPF-TEST", "KWKLFKKIGAVLKVL", "test")
    scored = ScoredCandidate(
        candidate=candidate,
        features=compute_features(candidate.sequence),
        scores={"activity": 0.8, "safety": 0.9, "synthesis": 0.9, "novelty": 0.5, "ensemble": 0.8},
        selection_reason=["test"],
        known_failure_modes=["No wet-lab assay has been run."],
    )
    cert = build_certificate(scored, {"weights": {}}, [])
    validate_json_schema(cert, _SCHEMA)
