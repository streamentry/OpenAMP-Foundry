"""Test that optional imports fail gracefully when dependencies are missing."""

def test_import_core():
    """Core package should import without optional dependencies."""
    import openamp_foundry  # noqa: F401


def test_import_cli():
    from openamp_foundry.cli import main  # noqa: F401


def test_import_pipeline():
    from openamp_foundry.pipeline import score_candidates  # noqa: F401


def test_import_simulation():
    from openamp_foundry.simulation import MembraneProxy  # noqa: F401
    from openamp_foundry.simulation import StructureProxy  # noqa: F401
