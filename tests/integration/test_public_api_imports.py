"""Public API import surface — verifies that every name listed in each
subpackage's `__all__` is actually importable from the package root.

This guards against accidental removal of re-exports when modules are
refactored, and makes the public surface discoverable for new agents
and contributors without reading source.
"""

from __future__ import annotations

import importlib


# Subpackages that should expose a curated public API via __all__.
# cli and calibration already had this; the rest were completed in
# the Phase 0 Loop 7 self-improvement slice.
PACKAGES_WITH_ALL = [
    "openamp_foundry.benchmark",
    "openamp_foundry.scoring",
    "openamp_foundry.selection",
    "openamp_foundry.features",
    "openamp_foundry.evidence",
    "openamp_foundry.data",
    "openamp_foundry.qc",
    "openamp_foundry.reports",
    "openamp_foundry.generators",
    "openamp_foundry.analysis",
    "openamp_foundry.utils",
    "openamp_foundry.gates",
    "openamp_foundry.simulation",
    "openamp_foundry.calibration",
    "openamp_foundry.cli",
]


def test_every_subpackage_declares_all():
    """Every public subpackage must publish `__all__`."""
    for pkg_name in PACKAGES_WITH_ALL:
        pkg = importlib.import_module(pkg_name)
        assert hasattr(pkg, "__all__"), f"{pkg_name} missing __all__"
        assert isinstance(pkg.__all__, list), f"{pkg_name}.__all__ must be a list"
        assert len(pkg.__all__) > 0, f"{pkg_name}.__all__ must be non-empty"


def test_every_all_entry_is_importable():
    """Each name in `__all__` must be reachable from the package root."""
    failed: list[str] = []
    for pkg_name in PACKAGES_WITH_ALL:
        pkg = importlib.import_module(pkg_name)
        for name in pkg.__all__:
            if not hasattr(pkg, name):
                failed.append(f"{pkg_name}.{name}")
    assert not failed, (
        "Names listed in __all__ but not importable from package root:\n  "
        + "\n  ".join(failed)
    )


def test_no_accidentally_exported_underscore_names():
    """Private names (prefixed with `_`) must not leak into __all__."""
    for pkg_name in PACKAGES_WITH_ALL:
        pkg = importlib.import_module(pkg_name)
        leaked = [n for n in pkg.__all__ if n.startswith("_")]
        assert not leaked, (
            f"{pkg_name}.__all__ leaks private names: {leaked}"
        )


def test_top_level_version_is_set():
    """The root package should expose a version string."""
    import openamp_foundry

    assert hasattr(openamp_foundry, "__version__")
    assert isinstance(openamp_foundry.__version__, str)
    assert openamp_foundry.__version__  # non-empty


def test_calibration_gateverdict_still_importable():
    """Regression guard for the Phase 0 exit-criterion import path."""
    from openamp_foundry.calibration import GateVerdict

    assert GateVerdict is not None


def test_benchmark_top_level_imports_work():
    """Phase 0 exit criterion: `from openamp_foundry.benchmark import ...` works."""
    from openamp_foundry.benchmark import (
        cluster_split,
        find_near_duplicates,
        run_cluster_split_benchmark,
        run_triage_benchmark,
    )

    assert cluster_split is not None
    assert find_near_duplicates is not None
    assert run_cluster_split_benchmark is not None
    assert run_triage_benchmark is not None


def test_scoring_top_level_imports_work():
    """Phase 0 exit criterion: `from openamp_foundry.scoring import ...` works."""
    from openamp_foundry.scoring import (
        EXPERT_WEIGHTS,
        activity_likeness_score,
        ensemble_score,
        safety_score,
    )

    assert callable(activity_likeness_score)
    assert callable(ensemble_score)
    assert callable(safety_score)
    assert isinstance(EXPERT_WEIGHTS, dict)
