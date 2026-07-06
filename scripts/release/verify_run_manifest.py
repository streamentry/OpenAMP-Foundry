#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openamp_foundry.reproducibility import verify_run_manifest


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify a run manifest")
    parser.add_argument("manifest")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    report = verify_run_manifest(args.manifest, root=args.root)
    output = json.dumps(report, indent=2)
    print(output)

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
