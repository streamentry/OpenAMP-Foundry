"""Test scorer registry coverage."""
from pathlib import Path


def test_scoring_modules_exist():
    scoring_dir = Path("src/openamp_foundry/scoring")
    assert scoring_dir.exists()
    modules = [f.stem for f in scoring_dir.glob("*.py") if f.stem != "__init__"]
    assert len(modules) >= 10, f"Only {len(modules)} scoring modules found"


def test_ensemble_scorer_importable():
    from openamp_foundry.scoring.ensemble import ensemble_score
    assert callable(ensemble_score)


def test_activity_scorer_importable():
    from openamp_foundry.scoring.activity import activity_likeness_score
    assert callable(activity_likeness_score)
