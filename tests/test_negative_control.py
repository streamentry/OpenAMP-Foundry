"""Negative control test: trivial non-AMP sequences should score low."""
import json
import tempfile
from pathlib import Path

from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.pipeline import score_candidates


def _make_control_csv(sequences: list[tuple[str, str]], tmp_path: Path) -> Path:
    path = tmp_path / "controls.csv"
    with open(path, "w") as f:
        f.write("id,sequence,source\n")
        for i, (seq, src) in enumerate(sequences):
            f.write(f"CTRL-{i:03d},{seq},{src}\n")
    return path


def test_poly_glycine_scores_low():
    """Poly-glycine (neutral, no charge) should score near zero for activity."""
    with tempfile.TemporaryDirectory() as tmp:
        csv = _make_control_csv([
            ("GGGGGGGGGG", "control"),
            ("GGGGGGGGGGGGGGGGGGGG", "control"),
        ], Path(tmp))
        scored, _ = score_candidates(str(csv))
        for item in scored:
            assert item.scores["activity"] < 0.3, f"Poly-G activity {item.scores['activity']} should be low"


def test_poly_alanine_scores_low():
    """Poly-alanine (hydrophobic, no charge) should score low for activity."""
    with tempfile.TemporaryDirectory() as tmp:
        csv = _make_control_csv([
            ("AAAAAAAAAA", "control"),
        ], Path(tmp))
        scored, _ = score_candidates(str(csv))
        for item in scored:
            assert item.scores["activity"] < 0.4, f"Poly-A activity {item.scores['activity']} should be low"


def test_known_amp_positive_control_scores_high():
    """A known AMP (magainin-2) should score higher than poly-glycine."""
    with tempfile.TemporaryDirectory() as tmp:
        csv = _make_control_csv([
            ("GGGGGGGGGG", "negative"),
            ("GIGKFLHSAKKFGKAFVGEIMNS", "positive"),
        ], Path(tmp))
        scored, _ = score_candidates(str(csv))
        scores = {item.candidate.candidate_id: item.scores["activity"] for item in scored}
        pos_id = "CTRL-001"
        neg_id = "CTRL-000"
        assert scores[pos_id] > scores[neg_id], (
            f"Known AMP ({scores[pos_id]}) should score higher than poly-G ({scores[neg_id]})"
        )
