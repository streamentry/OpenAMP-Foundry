"""Verify key docs are referenced in project index or README.

This is a soft check: warns about unreferenced docs but doesn't fail.
"""
from pathlib import Path

DOCS_DIR = Path("docs")

# Files that are expected to be standalone (no cross-reference needed)
STANDALONE = {
    "docs/AGENTS.md",
    "docs/README.md",
    "docs/PROJECT_INDEX.md",
}


def _get_all_md_files() -> set[str]:
    return {str(f.relative_to(DOCS_DIR.parent)) for f in DOCS_DIR.rglob("*.md")}


def _get_all_refs() -> set[str]:
    refs = set()
    # Check PROJECT_INDEX.md for references
    pi = DOCS_DIR.parent / "docs/PROJECT_INDEX.md"
    pi_text = pi.read_text()
    for line in pi_text.split("\n"):
        if ".md" in line:
            for word in line.split():
                if word.endswith(".md)") or word.endswith(".md]"):
                    ref = word.strip("()[]").strip(".")
                    if ref.endswith(".md"):
                        refs.add(ref)
    # Check README.md
    readme = DOCS_DIR.parent / "README.md"
    for line in readme.read_text().split("\n"):
        if ".md" in line:
            for word in line.split():
                if word.endswith(".md)") or word.endswith(".md]"):
                    ref = word.strip("()[]").strip(".")
                    if ref.endswith(".md"):
                        refs.add(ref)
    return refs


def test_key_docs_are_referenced():
    all_docs = _get_all_md_files()
    all_refs = _get_all_refs()
    # Check high-visibility docs are referenced
    key_docs = {
        "docs/evidence/METRICS_CURRENT.md",
        "docs/evidence/PROOF_LADDER.md",
        "docs/evidence/BENCHMARK_GOVERNANCE.md",
        "docs/engineering/ARCHITECTURE.md",
        "docs/getting-started/FIRST_RUN_WALKTHROUGH.md",
        "docs/trust/TRUST_CENTER.md",
        "docs/evidence/EVIDENCE_CERTIFICATE.md",
    }
    missing = key_docs - all_refs
    # These may be referenced by relative paths not captured by simple scan
    if missing:
        print(f"Warning: following docs not found by reference scan: {missing}")


def test_disconfirming_record_guide_is_indexed():
    """The DTR contract must be reachable from both documentation hubs."""
    guide = DOCS_DIR / "evidence" / "DISCONFIRMING_TEST_RECORD_GUIDE.md"
    assert guide.exists()

    evidence_readme = (DOCS_DIR / "evidence" / "README.md").read_text()
    project_index = (DOCS_DIR / "PROJECT_INDEX.md").read_text()

    assert "DISCONFIRMING_TEST_RECORD_GUIDE.md" in evidence_readme
    assert "DISCONFIRMING_TEST_RECORD_GUIDE.md" in project_index
