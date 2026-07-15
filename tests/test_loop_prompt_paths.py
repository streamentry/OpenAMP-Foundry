"""Keep the recurring loop prompt aligned with the documentation tree."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
LOOP_PROMPT = (ROOT / "LOOP.md").read_text()


def test_loop_prompt_points_to_canonical_source_of_truth_docs():
    canonical_paths = (
        "docs/README.md",
        "docs/engineering/ARCHITECTURE.md",
        "docs/research/PLAN.md",
        "docs/research/ROADMAP.md",
        "docs/evidence/METRICS_CURRENT.md",
        "docs/trust/SAFE_SCOPE.md",
    )

    for path in canonical_paths:
        assert path in LOOP_PROMPT
        assert (ROOT / path).is_file(), path


def test_loop_prompt_does_not_reintroduce_retired_flat_doc_paths():
    retired_paths = (
        "docs/ARCHITECTURE.md",
        "docs/PLAN.md",
        "docs/ROADMAP.md",
        "docs/METRICS_CURRENT.md",
        "docs/SAFE_SCOPE.md",
    )

    for path in retired_paths:
        assert f"`{path}`" not in LOOP_PROMPT.split("These files replace")[0]
