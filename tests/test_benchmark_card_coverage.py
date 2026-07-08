"""Verify benchmark card YAMLs exist for key benchmarks."""
from pathlib import Path

CARDS_DIR = Path("configs/benchmark_cards")
REQUIRED_CARDS = {
    "bench-500",
    "bench-calibration",
    "bench-charge-distribution",
    "bench-cheap-enemies",
    "bench-simulation-ablation",
    "bench-simulation-calibration",
}


def _get_card_targets() -> set[str]:
    cards = set()
    for f in CARDS_DIR.glob("*.yaml"):
        text = f.read_text()
        for line in text.split("\n"):
            if line.strip().startswith("target:"):
                cards.add(line.split(":")[1].strip())
    return cards


def test_required_benchmarks_have_cards():
    card_targets = _get_card_targets()
    missing = REQUIRED_CARDS - card_targets
    assert not missing, f"Missing required benchmark cards: {sorted(missing)}"


def test_cards_directory_has_yaml_files():
    files = list(CARDS_DIR.glob("*.yaml"))
    assert len(files) >= 3, f"Expected at least 3 card YAMLs, got {len(files)}"
