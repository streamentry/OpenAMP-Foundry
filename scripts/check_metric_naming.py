"""Check metric names against the canonical registry."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load_registry(path: str = "configs/metric_polarity_registry.json") -> dict:
    return json.loads(Path(path).read_text())


def get_all_canonical(registry: dict) -> set[str]:
    names = set()
    for key in ["pipeline_metrics", "simulation_metrics", "safety_metrics"]:
        names.update(registry.get(key, {}).keys())
    names.update(registry.get("canonical_names", {}).keys())
    return names


def get_aliases(registry: dict) -> dict[str, str]:
    return registry.get("aliases", {})


def check_metric_name(name: str, registry: dict) -> dict:
    canonicals = get_all_canonical(registry)
    aliases = get_aliases(registry)

    if name in canonicals:
        return {"name": name, "status": "canonical", "canonical_name": name}
    if name in aliases:
        return {"name": name, "status": "alias", "canonical_name": aliases[name]}
    return {"name": name, "status": "unknown", "canonical_name": None}


def scan_reports(docs_dir: str = "docs") -> list[dict]:
    registry = load_registry()
    canonicals = get_all_canonical(registry)
    aliases = get_aliases(registry)
    all_known = canonicals | set(aliases.keys())
    findings = []

    pattern = re.compile(r"\b[a-z_]+(?:_at_\d+)?\b")
    for md in Path(docs_dir).rglob("*.md"):
        for match in pattern.finditer(md.read_text()):
            word = match.group()
            if word in all_known:
                continue
            # Skip common non-metric words
            if word in {"docs", "make", "path", "file", "true", "false", "null", "none", "src",
                         "tests", "scripts", "configs", "outputs", "examples", "data", "models",
                         "schemas", "github", "html", "json", "yaml", "csv", "txt", "png"}:
                continue
            # Check if it looks like a metric name (snake_case with known endings)
            if word.endswith(("_score", "_rate", "_count", "_auroc", "_auc", "_at", "_bias",
                              "_risk", "_weight", "_ratio", "_flag", "_binding", "_index")):
                findings.append({
                    "file": str(md),
                    "word": word,
                    "suggestion": aliases.get(word, "unknown — check spelling or add to registry"),
                })

    return findings


def check_names_in_file(file_path: str) -> dict:
    registry = load_registry()
    text = Path(file_path).read_text()
    words = set(re.findall(r"\b[a-z_]+(?:_at_\d+)?\b", text))
    results = []
    for word in sorted(words):
        result = check_metric_name(word, registry)
        if result["status"] != "canonical":
            results.append(result)
    return {"file": file_path, "metrics_found": len(words), "non_canonical": results}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check metric naming consistency")
    parser.add_argument("--file", help="Check a specific file")
    parser.add_argument("--scan-docs", action="store_true", help="Scan docs for unknown metric names")
    args = parser.parse_args()

    if args.file:
        result = check_names_in_file(args.file)
        print(json.dumps(result, indent=2))
        return 3 if result["non_canonical"] else 0

    if args.scan_docs:
        findings = scan_reports()
        print(f"Found {len(findings)} potentially unknown metric names in docs:")
        for f in findings[:20]:
            print(f"  ❌ {f['file']}: '{f['word']}' → {f['suggestion']}")
        return 3 if findings else 0

    print("Specify --file or --scan-docs")
    return 2


if __name__ == "__main__":
    sys.exit(main())
