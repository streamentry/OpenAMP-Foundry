"""CFP- Configuration fingerprint schema.

Structured record of all config file paths and their hashes for a pipeline run.
Complements the RMC- config_hash field with a full per-file audit trail.
Verdict: all_configs_hashed / some_configs_unhashed / no_configs_recorded.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

VALID_CFP_HASH_ALGORITHMS: frozenset[str] = frozenset({
    "sha256", "sha512", "md5", "blake2b",
})

VALID_CFP_VERDICTS: frozenset[str] = frozenset({
    "all_configs_hashed",
    "some_configs_unhashed",
    "no_configs_recorded",
})

RECOMMENDED_HASH_ALGORITHM: str = "sha256"


@dataclass
class ConfigFileRecord:
    file_path: str
    file_hash: str
    hash_algorithm: str
    is_hashed: bool
    role: str


@dataclass
class ConfigurationFingerprint:
    cfp_id: str
    pipeline_version: str
    run_id: str
    config_file_records: list[ConfigFileRecord]
    n_configs: int
    n_hashed: int
    n_unhashed: int
    unhashed_paths: list[str]
    verdict: str
    hash_algorithm_used: str
    limitations: list[str]
    created_at: str
    dry_lab_only: bool = True


def _compute_is_hashed(file_hash: str, hash_algorithm: str) -> bool:
    return file_hash != "" and hash_algorithm != ""


def _compute_verdict(n_configs: int, n_unhashed: int) -> str:
    if n_configs == 0:
        return "no_configs_recorded"
    if n_unhashed > 0:
        return "some_configs_unhashed"
    return "all_configs_hashed"


def _compute_hash_algorithm_used(
    records: list[ConfigFileRecord],
) -> str:
    hashed = [r for r in records if r.is_hashed]
    if not hashed:
        return ""
    counts: Counter = Counter(r.hash_algorithm for r in hashed)
    return counts.most_common(1)[0][0]


def build_configuration_fingerprint(
    *,
    cfp_id: str,
    pipeline_version: str,
    run_id: str,
    config_files: list[dict],
    limitations: list[str],
    created_at: str,
) -> ConfigurationFingerprint:
    config_file_records: list[ConfigFileRecord] = []
    for cf in config_files:
        file_hash = cf.get("file_hash", "")
        hash_algorithm = cf.get("hash_algorithm", "")
        is_hashed = _compute_is_hashed(file_hash, hash_algorithm)
        config_file_records.append(ConfigFileRecord(
            file_path=cf["file_path"],
            file_hash=file_hash,
            hash_algorithm=hash_algorithm,
            is_hashed=is_hashed,
            role=cf["role"],
        ))
    n_configs = len(config_file_records)
    n_hashed = sum(1 for r in config_file_records if r.is_hashed)
    n_unhashed = n_configs - n_hashed
    unhashed_paths = [r.file_path for r in config_file_records if not r.is_hashed]
    verdict = _compute_verdict(n_configs, n_unhashed)
    hash_algorithm_used = _compute_hash_algorithm_used(config_file_records)
    cfp = ConfigurationFingerprint(
        cfp_id=cfp_id,
        pipeline_version=pipeline_version,
        run_id=run_id,
        config_file_records=config_file_records,
        n_configs=n_configs,
        n_hashed=n_hashed,
        n_unhashed=n_unhashed,
        unhashed_paths=unhashed_paths,
        verdict=verdict,
        hash_algorithm_used=hash_algorithm_used,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_configuration_fingerprint(cfp)
    return cfp


def validate_configuration_fingerprint(
    cfp: ConfigurationFingerprint,
) -> None:
    if not cfp.cfp_id.startswith("CFP-"):
        raise ValueError(f"cfp_id must start with 'CFP-': {cfp.cfp_id!r}")
    if not cfp.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not cfp.run_id:
        raise ValueError("run_id must be non-empty")
    for i, rec in enumerate(cfp.config_file_records):
        if not rec.file_path:
            raise ValueError(
                f"config_file_records[{i}].file_path must be non-empty"
            )
        if not rec.role:
            raise ValueError(
                f"config_file_records[{i}].role must be non-empty"
            )
        if rec.is_hashed:
            if not rec.file_hash:
                raise ValueError(
                    f"config_file_records[{i}].file_hash must be non-empty "
                    f"when is_hashed=True"
                )
            if rec.hash_algorithm not in VALID_CFP_HASH_ALGORITHMS:
                raise ValueError(
                    f"config_file_records[{i}].hash_algorithm "
                    f"{rec.hash_algorithm!r} not in VALID_CFP_HASH_ALGORITHMS"
                )
        else:
            if rec.file_hash != "":
                raise ValueError(
                    f"config_file_records[{i}].file_hash must be empty "
                    f"when is_hashed=False"
                )
            if rec.hash_algorithm != "":
                raise ValueError(
                    f"config_file_records[{i}].hash_algorithm must be empty "
                    f"when is_hashed=False"
                )
    expected_n_configs = len(cfp.config_file_records)
    if cfp.n_configs != expected_n_configs:
        raise ValueError(
            f"n_configs {cfp.n_configs} != {expected_n_configs} "
            f"(len(config_file_records))"
        )
    expected_n_hashed = sum(1 for r in cfp.config_file_records if r.is_hashed)
    if cfp.n_hashed != expected_n_hashed:
        raise ValueError(
            f"n_hashed {cfp.n_hashed} != {expected_n_hashed}"
        )
    expected_n_unhashed = (
        len(cfp.config_file_records) - expected_n_hashed
    )
    if cfp.n_unhashed != expected_n_unhashed:
        raise ValueError(
            f"n_unhashed {cfp.n_unhashed} != {expected_n_unhashed}"
        )
    expected_unhashed_paths = [
        r.file_path for r in cfp.config_file_records if not r.is_hashed
    ]
    if cfp.unhashed_paths != expected_unhashed_paths:
        raise ValueError(
            f"unhashed_paths {cfp.unhashed_paths} != "
            f"{expected_unhashed_paths}"
        )
    if cfp.verdict not in VALID_CFP_VERDICTS:
        raise ValueError(
            f"verdict {cfp.verdict!r} not in VALID_CFP_VERDICTS"
        )
    expected_verdict = _compute_verdict(cfp.n_configs, cfp.n_unhashed)
    if cfp.verdict != expected_verdict:
        raise ValueError(
            f"verdict {cfp.verdict!r} inconsistent with "
            f"n_configs={cfp.n_configs}, n_unhashed={cfp.n_unhashed}"
        )
    expected_hash_algorithm_used = _compute_hash_algorithm_used(
        cfp.config_file_records
    )
    if cfp.hash_algorithm_used != expected_hash_algorithm_used:
        raise ValueError(
            f"hash_algorithm_used {cfp.hash_algorithm_used!r} != "
            f"{expected_hash_algorithm_used!r}"
        )
    if not cfp.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not cfp.limitations:
        raise ValueError("limitations must be non-empty")
    if not cfp.created_at:
        raise ValueError("created_at must be non-empty")


def format_configuration_fingerprint(
    cfp: ConfigurationFingerprint,
) -> str:
    lines = [
        f"Configuration Fingerprint — {cfp.cfp_id}",
        f"Pipeline: {cfp.pipeline_version}",
        f"Run ID: {cfp.run_id}",
        f"Verdict: {cfp.verdict}",
        f"Config files: {cfp.n_hashed}/{cfp.n_configs} hashed",
    ]
    if cfp.hash_algorithm_used:
        lines.append(f"Hash algorithm: {cfp.hash_algorithm_used}")
    if cfp.unhashed_paths:
        lines.append(f"Unhashed: {', '.join(cfp.unhashed_paths)}")
    lines.append("Config files:")
    for rec in cfp.config_file_records:
        status = "HASHED" if rec.is_hashed else "UNHASHED"
        algo = f" ({rec.hash_algorithm})" if rec.hash_algorithm else ""
        lines.append(f"  [{status}] {rec.role}: {rec.file_path}{algo}")
    if cfp.limitations:
        lines.append(f"Limitations: {'; '.join(cfp.limitations)}")
    lines.append(f"Created: {cfp.created_at}")
    lines.append(f"dry_lab_only: {cfp.dry_lab_only}")
    return "\n".join(lines)
