#!/usr/bin/env python3
"""Bump `configs/recalibration_policy.yaml` version, guarded by decision-log recency.

The bump workflow enforces the pre-registered policy version contract:
1. A decision-log entry dated within 30 days must exist in the given directory.
2. The version is auto-incremented by one.
3. ``locked_at`` and ``human_reviewer`` are updated.
4. All existing ``locked_changes`` are preserved.

Dry-run mode previews changes without writing.

Usage::

    python scripts/bump_recalibration_policy.py --human-reviewer "Name"

    python scripts/bump_recalibration_policy.py \\
        --human-reviewer "Name" \\
        --policy configs/recalibration_policy.yaml \\
        --decision-log-dir decision_logs/ \\
        --dry-run

Exit codes:
    0 – Version bumped (or dry-run simulated bump).
    2 – Missing policy file or decision-log directory.
    3 – Validation failed (no recent decision log, etc.).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


def _find_latest_decision_log(
    decision_log_dir: str | Path,
) -> tuple[date | None, str | None]:
    """Return (date, filename) of the most recent decision-log file."""
    d = Path(decision_log_dir)
    if not d.is_dir():
        return None, f"Not a directory: {decision_log_dir}"

    best_date: date | None = None
    best_name: str | None = None
    for f in d.iterdir():
        if not f.is_file():
            continue
        name = f.name
        if name.startswith("DECISION_LOG_") and name.endswith(".md"):
            date_str = name[len("DECISION_LOG_") : -len(".md")]
            try:
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if best_date is None or log_date > best_date:
                best_date = log_date
                best_name = name
    return best_date, best_name


def bump_recalibration_policy(
    *,
    policy_path: str | Path,
    human_reviewer: str,
    decision_log_dir: str | Path = "decision_logs",
    today: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Execute the policy version bump workflow.

    Returns a dict with keys:
        - status: "bumped", "dry_run", or "failed"
        - old_version, new_version
        - locked_at
        - human_reviewer
        - decision_log: str or None
        - decision_log_age_days: int or None
        - reasons: list[str]  (failure reasons when status=failed)
    """
    from openamp_foundry.calibration.policy import load_recalibration_policy
    from openamp_foundry.calibration.policy_version import (
        auto_increment_version,
    )

    p = Path(policy_path)
    if not p.exists():
        return {
            "status": "failed",
            "reasons": [f"Policy file not found: {p}"],
        }

    policy = load_recalibration_policy(str(p))

    ref_date: date
    if today is not None:
        ref_date = datetime.strptime(today, "%Y-%m-%d").date()
    else:
        ref_date = date.today()

    # Check decision-log recency
    log_date, log_name = _find_latest_decision_log(decision_log_dir)
    reasons: list[str] = []
    if log_date is None:
        reasons.append(
            f"No decision-log file (DECISION_LOG_<date>.md) found in {decision_log_dir}"
        )
    else:
        age_days = (ref_date - log_date).days
        if age_days > 30:
            reasons.append(
                f"Latest decision log ({log_name}) dated {log_date} "
                f"is {age_days} days before reference date {ref_date}, "
                f"exceeds 30-day limit"
            )
        if log_date > ref_date:
            reasons.append(
                f"Latest decision log ({log_name}) dated {log_date} "
                f"is in the future relative to reference date {ref_date}"
            )

    if reasons:
        return {
            "status": "failed",
            "old_version": policy.policy_version,
            "decision_log": log_name,
            "decision_log_date": str(log_date) if log_date else None,
            "reasons": reasons,
        }

    new_locked_at = ref_date.isoformat()
    new_raw = auto_increment_version(
        policy,
        new_locked_at=new_locked_at,
        new_reviewer=human_reviewer,
        policy_dir=str(p.parent) if p.parent else None,
    )

    result = {
        "status": "dry_run" if dry_run else "bumped",
        "old_version": policy.policy_version,
        "new_version": new_raw["policy_version"],
        "locked_at": new_locked_at,
        "human_reviewer": human_reviewer,
        "decision_log": log_name,
        "decision_log_date": str(log_date) if log_date else None,
    }

    if not dry_run:
        import yaml

        with open(p, "w") as f:
            yaml.dump(new_raw, f, default_flow_style=False, sort_keys=False)
        result["written_to"] = str(p)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump recalibration policy version with decision-log guard",
    )
    parser.add_argument(
        "--policy",
        default="configs/recalibration_policy.yaml",
        help="Path to the recalibration policy YAML (default: configs/recalibration_policy.yaml)",
    )
    parser.add_argument(
        "--human-reviewer",
        required=True,
        help="Name of the human reviewer authorising this bump",
    )
    parser.add_argument(
        "--decision-log-dir",
        default="decision_logs",
        help="Directory containing DECISION_LOG_<date>.md files (default: decision_logs/)",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="ISO date string (YYYY-MM-DD) for 'today' (default: today's date)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )

    args = parser.parse_args()
    result = bump_recalibration_policy(
        policy_path=args.policy,
        human_reviewer=args.human_reviewer,
        decision_log_dir=args.decision_log_dir,
        today=args.today,
        dry_run=args.dry_run,
    )

    print(json.dumps(result, indent=2, default=str))

    if result.get("status") == "failed":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
