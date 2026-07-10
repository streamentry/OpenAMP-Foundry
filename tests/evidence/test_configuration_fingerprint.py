"""Tests for CFP- configuration fingerprint schema."""

import pytest
from openamp_foundry.evidence.configuration_fingerprint import (
    ConfigurationFingerprint,
    ConfigFileRecord,
    VALID_CFP_HASH_ALGORITHMS,
    VALID_CFP_VERDICTS,
    RECOMMENDED_HASH_ALGORITHM,
    build_configuration_fingerprint,
    format_configuration_fingerprint,
    validate_configuration_fingerprint,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIMITATIONS = ["Dry-lab only, not biological validation."]

ALL_HASHED_CONFIGS = [
    dict(file_path="configs/scoring.yaml", file_hash="abc123",
         hash_algorithm="sha256", role="scoring_config"),
    dict(file_path="configs/filter.yaml", file_hash="def456",
         hash_algorithm="sha512", role="filter_config"),
]

ONE_UNHASHED_CONFIGS = [
    dict(file_path="configs/scoring.yaml", file_hash="abc123",
         hash_algorithm="sha256", role="scoring_config"),
    dict(file_path="configs/filter.yaml", file_hash="",
         hash_algorithm="", role="filter_config"),
]


def _build(**kwargs):
    defaults = dict(
        cfp_id="CFP-001",
        pipeline_version="v1.0",
        run_id="run-20260710-001",
        config_files=[dict(c) for c in ALL_HASHED_CONFIGS],
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_configuration_fingerprint(**defaults)


def _make_cfp(**kwargs):
    defaults = dict(
        cfp_id="CFP-001",
        pipeline_version="v1.0",
        run_id="run-001",
        config_file_records=[
            ConfigFileRecord(
                file_path="configs/scoring.yaml",
                file_hash="abc123",
                hash_algorithm="sha256",
                is_hashed=True,
                role="scoring_config",
            ),
            ConfigFileRecord(
                file_path="configs/filter.yaml",
                file_hash="def456",
                hash_algorithm="sha256",
                is_hashed=True,
                role="filter_config",
            ),
        ],
        n_configs=2,
        n_hashed=2,
        n_unhashed=0,
        unhashed_paths=[],
        verdict="all_configs_hashed",
        hash_algorithm_used="sha256",
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return ConfigurationFingerprint(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (10 tests)
# ---------------------------------------------------------------------------


def test_valid_cfp_hash_algorithms_is_frozenset():
    assert isinstance(VALID_CFP_HASH_ALGORITHMS, frozenset)


def test_valid_cfp_hash_algorithms_has_four():
    assert len(VALID_CFP_HASH_ALGORITHMS) == 4


def test_valid_cfp_hash_algorithms_contains_sha256():
    assert "sha256" in VALID_CFP_HASH_ALGORITHMS


def test_valid_cfp_hash_algorithms_contains_sha512():
    assert "sha512" in VALID_CFP_HASH_ALGORITHMS


def test_valid_cfp_hash_algorithms_contains_md5():
    assert "md5" in VALID_CFP_HASH_ALGORITHMS


def test_valid_cfp_hash_algorithms_contains_blake2b():
    assert "blake2b" in VALID_CFP_HASH_ALGORITHMS


def test_valid_cfp_verdicts_is_frozenset():
    assert isinstance(VALID_CFP_VERDICTS, frozenset)


def test_valid_cfp_verdicts_has_three():
    assert len(VALID_CFP_VERDICTS) == 3


def test_valid_cfp_verdicts_contains_all_configs_hashed():
    assert "all_configs_hashed" in VALID_CFP_VERDICTS


def test_recommended_hash_algorithm_is_sha256():
    assert RECOMMENDED_HASH_ALGORITHM == "sha256"


# ---------------------------------------------------------------------------
# 2. build – happy paths (20 tests)
# ---------------------------------------------------------------------------


def test_build_returns_configuration_fingerprint():
    assert isinstance(_build(), ConfigurationFingerprint)


def test_build_all_hashed_verdict_all_configs_hashed():
    assert _build().verdict == "all_configs_hashed"


def test_build_one_unhashed_verdict_some_configs_unhashed():
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    assert r.verdict == "some_configs_unhashed"


def test_build_empty_records_verdict_no_configs_recorded():
    r = _build(config_files=[])
    assert r.verdict == "no_configs_recorded"


def test_build_n_configs_count():
    assert _build().n_configs == 2


def test_build_n_hashed_count():
    assert _build().n_hashed == 2
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    assert r.n_hashed == 1


def test_build_n_unhashed_count():
    assert _build().n_unhashed == 0
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    assert r.n_unhashed == 1


def test_build_unhashed_paths_list():
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    assert r.unhashed_paths == ["configs/filter.yaml"]


def test_build_hash_algorithm_used_auto_select():
    assert _build().hash_algorithm_used == "sha256"


def test_build_hash_algorithm_used_empty_when_none_hashed():
    no_hash_configs = [
        dict(file_path="configs/scoring.yaml", file_hash="",
             hash_algorithm="", role="scoring_config"),
    ]
    r = _build(config_files=no_hash_configs)
    assert r.hash_algorithm_used == ""


def test_build_hash_algorithm_used_most_common():
    mixed_configs = [
        dict(file_path="c1.yaml", file_hash="a", hash_algorithm="sha256",
             role="scoring_config"),
        dict(file_path="c2.yaml", file_hash="b", hash_algorithm="sha256",
             role="filter_config"),
        dict(file_path="c3.yaml", file_hash="c", hash_algorithm="sha512",
             role="seed_config"),
    ]
    r = _build(config_files=mixed_configs)
    assert r.hash_algorithm_used == "sha256"


def test_build_cfp_id_stored():
    assert _build(cfp_id="CFP-099").cfp_id == "CFP-099"


def test_build_pipeline_version_stored():
    assert _build(pipeline_version="v2.0").pipeline_version == "v2.0"


def test_build_run_id_stored():
    assert _build(run_id="run-099").run_id == "run-099"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_limitations_stored():
    r = _build(limitations=["lim1", "lim2"])
    assert r.limitations == ["lim1", "lim2"]


def test_build_created_at_stored():
    assert _build(created_at="2026-07-11").created_at == "2026-07-11"


def test_build_is_hashed_true():
    assert _build().config_file_records[0].is_hashed is True


def test_build_is_hashed_false():
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    assert r.config_file_records[1].is_hashed is False


def test_build_role_stored():
    r = _build(config_files=[dict(file_path="c.yaml", file_hash="a",
                                  hash_algorithm="sha256", role="seed_config")])
    assert r.config_file_records[0].role == "seed_config"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_cfp_id_prefix():
    with pytest.raises(ValueError, match="CFP-"):
        _build(cfp_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_run_id():
    with pytest.raises(ValueError):
        _build(run_id="")


def test_validate_rejects_empty_file_path():
    cfp = _make_cfp()
    cfp.config_file_records[0].file_path = ""
    with pytest.raises(ValueError, match="file_path"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_empty_role():
    cfp = _make_cfp()
    cfp.config_file_records[0].role = ""
    with pytest.raises(ValueError, match="role"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_is_hashed_true_empty_file_hash():
    cfp = _make_cfp()
    cfp.config_file_records[0].is_hashed = True
    cfp.config_file_records[0].file_hash = ""
    cfp.config_file_records[0].hash_algorithm = "sha256"
    with pytest.raises(ValueError, match="file_hash"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_is_hashed_true_bad_hash_algorithm():
    cfp = _make_cfp()
    cfp.config_file_records[0].is_hashed = True
    cfp.config_file_records[0].file_hash = "abc"
    cfp.config_file_records[0].hash_algorithm = "md4"
    with pytest.raises(ValueError, match="hash_algorithm"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_is_hashed_false_file_hash_non_empty():
    cfp = _make_cfp()
    cfp.config_file_records[0].is_hashed = False
    cfp.config_file_records[0].file_hash = "abc"
    cfp.config_file_records[0].hash_algorithm = ""
    with pytest.raises(ValueError, match="file_hash must be empty"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_is_hashed_false_hash_algorithm_non_empty():
    cfp = _make_cfp()
    cfp.config_file_records[0].is_hashed = False
    cfp.config_file_records[0].file_hash = ""
    cfp.config_file_records[0].hash_algorithm = "sha256"
    with pytest.raises(ValueError, match="hash_algorithm must be empty"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_n_configs_mismatch():
    cfp = _build()
    cfp.n_configs = 99
    with pytest.raises(ValueError, match="n_configs"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_n_hashed_mismatch():
    cfp = _build()
    cfp.n_hashed = 99
    with pytest.raises(ValueError, match="n_hashed"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_n_unhashed_mismatch():
    cfp = _build()
    cfp.n_unhashed = 99
    with pytest.raises(ValueError, match="n_unhashed"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_unhashed_paths_mismatch():
    cfp = _build()
    cfp.unhashed_paths = ["some/config.yaml"]
    with pytest.raises(ValueError, match="unhashed_paths"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_verdict_mismatch():
    cfp = _build()
    cfp.verdict = "some_configs_unhashed"
    with pytest.raises(ValueError, match="verdict"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_hash_algorithm_used_mismatch():
    cfp = _build()
    cfp.hash_algorithm_used = "md5"
    with pytest.raises(ValueError, match="hash_algorithm_used"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_dry_lab_only_false():
    cfp = _build()
    cfp.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_configuration_fingerprint(cfp)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_cfp_id():
    assert "CFP-001" in format_configuration_fingerprint(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_configuration_fingerprint(_build())


def test_format_contains_run_id():
    assert "run-20260710-001" in format_configuration_fingerprint(_build())


def test_format_contains_verdict():
    assert "all_configs_hashed" in format_configuration_fingerprint(_build())


def test_format_contains_n_configs_and_n_hashed():
    output = format_configuration_fingerprint(_build())
    assert "2" in output


def test_format_contains_hash_algorithm():
    output = format_configuration_fingerprint(_build())
    assert "sha256" in output


def test_format_contains_unhashed_paths_when_present():
    r = _build(config_files=ONE_UNHASHED_CONFIGS)
    output = format_configuration_fingerprint(r)
    assert "Unhashed:" in output
    assert "configs/filter.yaml" in output


def test_format_is_string():
    assert isinstance(format_configuration_fingerprint(_build()), str)
