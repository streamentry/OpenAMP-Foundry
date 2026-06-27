from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openamp_foundry import __version__
from openamp_foundry.config import load_config
from openamp_foundry.data.loaders import is_valid_sequence, load_candidates_csv
from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.ensemble import ensemble_score, known_failure_modes, selection_reasons
from openamp_foundry.scoring.novelty import novelty_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
from openamp_foundry.selection.diversity import greedy_diverse_select
from openamp_foundry.selection.pareto import rank_candidates
from openamp_foundry.types import ScoredCandidate
from openamp_foundry.utils.hashing import file_sha256, stable_json_hash
from openamp_foundry.utils.io import write_json, write_jsonl


def _passes_length_filter(sequence: str, min_length: int, max_length: int) -> bool:
    return min_length <= len(sequence) <= max_length


def score_candidates(
    candidate_path: str | Path,
    reference_path: str | Path | None = None,
    config_path: str | Path = "configs/pipeline.yaml",
) -> tuple[list[ScoredCandidate], dict[str, Any]]:
    config = load_config(config_path)
    filters = config.get("filters", {})
    allowed = set(filters.get("allowed_amino_acids", "ACDEFGHIKLMNPQRSTVWY"))
    min_length = int(filters.get("min_length", 8))
    max_length = int(filters.get("max_length", 35))

    candidates = load_candidates_csv(candidate_path)
    references = load_candidates_csv(reference_path) if reference_path else []
    weights = config["weights"]

    scored: list[ScoredCandidate] = []
    for candidate in candidates:
        valid_aa = is_valid_sequence(candidate.sequence, allowed=allowed)
        valid_len = _passes_length_filter(candidate.sequence, min_length, max_length)
        valid = valid_aa and valid_len
        features = compute_features(candidate.sequence)
        act = activity_likeness_score(features) if valid else 0.0
        safe = safety_score(features) if valid else 0.0
        synth = synthesis_feasibility_score(features, valid_sequence=valid)
        nov, nearest = novelty_score(candidate.sequence, references)
        raw_scores = {
            "activity": act,
            "safety": safe,
            "synthesis": synth,
            "novelty": nov,
        }
        raw_scores["ensemble"] = ensemble_score(raw_scores, weights)
        item = ScoredCandidate(
            candidate=candidate,
            features=features,
            scores=raw_scores,
            references_checked=[str(reference_path)] if reference_path else [],
            nearest_reference=nearest,
        )
        item.valid = valid
        item.selection_reason = selection_reasons(raw_scores)
        item.known_failure_modes = known_failure_modes(raw_scores)
        if not valid_aa:
            item.known_failure_modes.append("Sequence contains non-canonical amino acids.")
        if not valid_len:
            item.known_failure_modes.append(
                f"Sequence length {len(candidate.sequence)} outside filter range "
                f"[{min_length}, {max_length}]."
            )
        scored.append(item)
    return scored, config


def build_run_manifest(
    run_id: str,
    config: dict[str, Any],
    input_paths: list[Path],
    output_paths: list[str],
    generated_at: str,
) -> dict[str, Any]:
    inputs = []
    for p in input_paths:
        if p.exists():
            inputs.append({"path": str(p), "sha256": file_sha256(p)})
        else:
            inputs.append({"path": str(p)})
    return {
        "run_id": run_id,
        "pipeline_version": __version__,
        "config_hash": stable_json_hash(config),
        "generated_at": generated_at,
        "inputs": [x["path"] for x in inputs],
        "input_hashes": {x["path"]: x.get("sha256", "N/A") for x in inputs},
        "outputs": output_paths,
    }


def run_ranking_pipeline(
    candidate_path: str | Path,
    reference_path: str | Path | None,
    out_path: str | Path,
    report_path: str | Path | None = None,
    cert_dir: str | Path | None = None,
    config_path: str | Path = "configs/pipeline.yaml",
    manifest_path: str | Path | None = None,
) -> list[ScoredCandidate]:
    run_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    scored, config = score_candidates(candidate_path, reference_path, config_path)
    selection_cfg = config.get("selection", {})
    min_novelty = float(selection_cfg.get("min_novelty", 0.0))
    max_safety_risk = float(selection_cfg.get("max_safety_risk", 1.0))

    ranked = rank_candidates(scored)
    top_n = int(selection_cfg.get("top_n", len(ranked)))

    eligible = [
        item for item in ranked
        if getattr(item, "valid", True)
        and item.scores["novelty"] >= min_novelty
        and item.scores["safety"] >= (1.0 - max_safety_risk)
    ]
    selected = greedy_diverse_select(eligible, top_n=top_n)

    rows = []
    selected_ids = {item.candidate.candidate_id for item in selected}
    for item in ranked:
        rows.append(
            {
                "candidate_id": item.candidate.candidate_id,
                "sequence": item.candidate.sequence,
                "source": item.candidate.source,
                "valid": getattr(item, "valid", True),
                "selected": item.candidate.candidate_id in selected_ids,
                "scores": item.scores,
                "features": item.features,
                "nearest_reference": item.nearest_reference,
                "selection_reason": item.selection_reason,
                "known_failure_modes": item.known_failure_modes,
            }
        )
    write_jsonl(out_path, rows)

    if cert_dir:
        cert_root = Path(cert_dir)
        for item in selected:
            cert = build_certificate(item, config, [str(reference_path)] if reference_path else [])
            write_json(cert_root / f"{item.candidate.candidate_id}.json", cert)

    if report_path:
        write_report(report_path, ranked, selected)
        batch_report = build_batch_report(ranked, selected, generated_at)
        report_json = Path(report_path).with_suffix(".json")
        write_json(report_json, batch_report)

    output_paths = [str(out_path)]
    if report_path:
        output_paths.append(str(report_path))
    if cert_dir:
        output_paths.append(str(cert_dir))

    manifest = build_run_manifest(
        run_id=run_id,
        config=config,
        input_paths=[Path(candidate_path)]
        + ([Path(reference_path)] if reference_path else [])
        + [Path(config_path)],
        output_paths=output_paths,
        generated_at=generated_at,
    )

    if manifest_path:
        write_json(manifest_path, manifest)
    else:
        manifest_out = Path(out_path).with_name("run_manifest.json")
        write_json(manifest_out, manifest)

    return ranked


def build_batch_report(
    ranked: list[ScoredCandidate],
    selected: list[ScoredCandidate],
    generated_at: str,
) -> dict[str, Any]:
    """Build a machine-readable batch report validatable against batch_report.schema.json."""
    selected_ids = {item.candidate.candidate_id for item in selected}
    return {
        "pipeline_version": __version__,
        "candidate_count": len(ranked),
        "selected_count": len(selected),
        "generated_at": generated_at,
        "disclaimer": (
            "All scores are transparent baseline heuristics. "
            "They are not validated biological predictors. "
            "No antimicrobial activity has been demonstrated."
        ),
        "score_averages": {
            "activity": round(
                sum(s.scores["activity"] for s in ranked) / len(ranked), 4
            ) if ranked else 0.0,
            "safety": round(
                sum(s.scores["safety"] for s in ranked) / len(ranked), 4
            ) if ranked else 0.0,
            "novelty": round(
                sum(s.scores["novelty"] for s in ranked) / len(ranked), 4
            ) if ranked else 0.0,
            "ensemble": round(
                sum(s.scores["ensemble"] for s in ranked) / len(ranked), 4
            ) if ranked else 0.0,
        },
        "selected_ids": sorted(selected_ids),
    }


def write_report(
    path: str | Path, ranked: list[ScoredCandidate], selected: list[ScoredCandidate]
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    selected_ids = {item.candidate.candidate_id for item in selected}
    lines = [
        "# OpenAMP Foundry Candidate Report",
        "",
        "> **Disclaimer:** All scores are transparent baseline heuristics computed from "
        "physicochemical properties. They are NOT validated biological predictors. "
        "No antimicrobial activity has been demonstrated in vitro or in vivo. "
        "These candidates are nominated for possible future expert review and assay only.",
        "",
        f"Total candidates scored: {len(ranked)}",
        f"Candidates selected (passed all filters, diverse): {len(selected)}",
        "",
        "| Rank | ID | Seq | Ensemble | Activity | Safety | Synthesis | Novelty | Selected |",
        "|---:|---|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for idx, item in enumerate(ranked, start=1):
        s = item.scores
        sel_mark = "Y" if item.candidate.candidate_id in selected_ids else ""
        lines.append(
            f"| {idx} | {item.candidate.candidate_id} | `{item.candidate.sequence}` | "
            f"{s['ensemble']:.4f} | {s['activity']:.4f} | {s['safety']:.4f} | "
            f"{s['synthesis']:.4f} | {s['novelty']:.4f} | {sel_mark} |"
        )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
