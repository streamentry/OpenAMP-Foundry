"""Test pipeline handles duplicate and near-duplicate inputs."""
import tempfile
from pathlib import Path

from openamp_foundry.pipeline import score_candidates


def test_duplicate_sequences_both_scored():
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "dupes.csv"
        csv.write_text("id,sequence,source\nA,KWKLFKKIGAVLKVL,test\nB,KWKLFKKIGAVLKVL,test\n")
        scored, _ = score_candidates(str(csv))
        assert len(scored) == 2, "Both duplicate sequences should be scored"
        ids = {s.candidate.candidate_id for s in scored}
        assert ids == {"A", "B"}
        scores = {s.candidate.candidate_id: s.scores["ensemble"] for s in scored}
        assert scores["A"] == scores["B"], "Same sequence should get same scores"


def test_single_amino_acid_change_produces_similar_scores():
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "mutants.csv"
        csv.write_text(
            "id,sequence,source\n"
            "WT,KWKLFKKIGAVLKVL,test\n"
            "MUT1,KWKLFKKIGAVLKVA,test\n"
            "MUT2,KWKLFKKIGAVLKVV,test\n"
        )
        scored, _ = score_candidates(str(csv))
        scores = {s.candidate.candidate_id: s.scores["ensemble"] for s in scored}
        wt = scores["WT"]
        for mut in ["MUT1", "MUT2"]:
            delta = abs(scores[mut] - wt)
            assert delta < 0.3, f"Single AA change should not drastically alter score: {mut} delta={delta:.4f}"
