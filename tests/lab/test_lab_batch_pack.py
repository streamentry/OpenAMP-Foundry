"""Tests for the fail-closed lab batch pack builder."""

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lab" / "build_lab_batch_pack.py"
_spec = importlib.util.spec_from_file_location(
    "_scripts_lab_batch_pack",
    _SCRIPT_PATH,
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
build_batch_pack = _mod.build_batch_pack
verify_batch_pack = _mod.verify_batch_pack


def _make_evidence(tmp: Path, *candidate_ids: str) -> Path:
    """Create minimal evidence certificates for candidate IDs."""
    d = tmp / "evidence"
    d.mkdir(exist_ok=True)
    for candidate_id in candidate_ids:
        (d / f"{candidate_id}.json").write_text(
            json.dumps({"candidate_id": candidate_id, "scores": {"ensemble": 0.8}})
        )
    return d


def _make_panel_csv(tmp: Path, rows: list[tuple[str, str]] | None = None) -> Path:
    """Create a minimal panel CSV."""
    rows = rows or [
        ("C1", "KKLFKKILKYL"),
        ("C2", "ACDEFGHIKLMNPQRSTVWY"),
    ]
    p = tmp / "panel.csv"
    body = "\n".join(f"{candidate_id},{sequence}" for candidate_id, sequence in rows)
    p.write_text(f"candidate_id,sequence\n{body}\n")
    return p


def _build_pack(panel: Path, ev_dir: Path, out: Path) -> dict:
    return build_batch_pack(
        panel_csv=str(panel),
        evidence_dir=str(ev_dir),
        out_zip=str(out),
    )


def _run_pack_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/lab/build_lab_batch_pack.py", *args],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def test_build_pack_success(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    result = _build_pack(panel, ev_dir, out)

    assert "error" not in result
    assert out.exists()
    assert result["evidence_count"] == 2
    assert result["strict_identity_checks"]["evidence_must_match_panel_exactly"]


def test_build_pack_contains_evidence(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)

    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "evidence/C1.json" in names
        assert "evidence/C2.json" in names


def test_build_pack_contains_readme(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)

    with zipfile.ZipFile(out) as z:
        assert "README.md" in z.namelist()
        readme = z.read("README.md").decode("utf-8")
        assert "Fail-Closed Checks Applied" in readme
        assert "not wet-lab procedures" in readme


def test_build_pack_contains_controls_manifest(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)

    with zipfile.ZipFile(out) as z:
        assert "controls_manifest.json" in z.namelist()


def test_build_pack_contains_data_return_template(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)

    with zipfile.ZipFile(out) as z:
        assert "data_return_template.json" in z.namelist()


def test_build_pack_contains_chain_of_custody(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    manifest = _build_pack(panel, ev_dir, out)

    with zipfile.ZipFile(out) as z:
        custody = json.loads(z.read("chain_of_custody.json"))
        assert "MANIFEST.json" in z.namelist()
        assert custody["panel_csv_sha256"] == manifest["panel_csv_sha256"]
        assert custody["synthesis_order_sha256"] == manifest["synthesis_order_sha256"]
        assert custody["pack_standard"] == "fail_closed_lab_handoff_v1"
        assert len(custody["candidate_identities"]) == 2
        assert custody["candidate_identities"][0]["candidate_id"] == "C1"
        assert "sequence_sha256" in custody["candidate_identities"][0]
        assert "biological activity" in custody["not_evidence_of"]


def test_verify_batch_pack_success(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)
    result = verify_batch_pack(out)

    assert result["status"] == "ok"
    assert result["panel_hash_ok"] is True
    assert result["candidate_identity_hashes_ok"] is True
    assert result["synthesis_order_hash_ok"] is True
    assert result["evidence_hashes_ok"] is True


def test_verify_batch_pack_detects_tampered_panel(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)

    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(out) as src:
        with zipfile.ZipFile(tampered, "w", zipfile.ZIP_DEFLATED) as dst:
            for name in src.namelist():
                data = src.read(name)
                if name == "panel.csv":
                    data = data.replace(b"C1,KKLFKKILKYL", b"C1,KKLFKKILKKK")
                dst.writestr(name, data)

    result = verify_batch_pack(tampered)

    assert result["status"] == "failed"
    assert result["panel_hash_ok"] is False
    assert result["candidate_identity_hashes_ok"] is False
    assert result["synthesis_order_hash_ok"] is False


def test_build_pack_contains_real_review_reference_docs(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    out = tmp_path / "pack.zip"

    result = _build_pack(panel, ev_dir, out)

    assert "error" not in result
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "protocols/README.md" in names
        assert "protocols/LAB_PARTNER_ONBOARDING.md" in names
        assert "protocols/PRE_REGISTERED_PILOT_TEMPLATE.md" in names
        assert "protocols/EXTERNAL_REVIEW_PACKET.md" in names


def test_build_pack_fails_for_missing_required_panel_column(tmp_path):
    panel = tmp_path / "panel.csv"
    panel.write_text("id,seq\nC1,KKLFKKILKYL\n")
    ev_dir = _make_evidence(tmp_path, "C1")

    result = build_batch_pack(
        panel_csv=str(panel),
        evidence_dir=str(ev_dir),
        out_zip=str(tmp_path / "pack.zip"),
    )

    assert "error" in result
    assert "missing required column" in result["error"]


def test_build_pack_fails_for_missing_evidence_certificate(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1")

    result = build_batch_pack(
        panel_csv=str(panel),
        evidence_dir=str(ev_dir),
        out_zip=str(tmp_path / "pack.zip"),
    )

    assert "error" in result
    assert result["missing_evidence"] == ["C2"]


def test_build_pack_fails_for_extra_evidence_certificate(tmp_path):
    panel = _make_panel_csv(tmp_path, rows=[("C1", "KKLFKKILKYL")])
    ev_dir = _make_evidence(tmp_path, "C1", "C2")

    result = build_batch_pack(
        panel_csv=str(panel),
        evidence_dir=str(ev_dir),
        out_zip=str(tmp_path / "pack.zip"),
    )

    assert "error" in result
    assert result["extra_evidence"] == ["C2"]


def test_build_pack_fails_for_missing_protocol_doc(tmp_path):
    panel = _make_panel_csv(tmp_path)
    ev_dir = _make_evidence(tmp_path, "C1", "C2")

    result = build_batch_pack(
        panel_csv=str(panel),
        evidence_dir=str(ev_dir),
        out_zip=str(tmp_path / "pack.zip"),
        protocol_docs=[str(tmp_path / "missing.md")],
    )

    assert "error" in result
    assert "Missing protocol/reference document" in result["error"]


def test_build_pack_error_missing_panel(tmp_path):
    result = build_batch_pack(
        panel_csv="/nonexistent.csv",
        evidence_dir=str(tmp_path),
        out_zip=str(tmp_path / "pack.zip"),
    )
    assert "error" in result


def test_build_pack_error_missing_evidence(tmp_path):
    result = build_batch_pack(
        panel_csv=str(_make_panel_csv(tmp_path)),
        evidence_dir="/nonexistent",
        out_zip=str(tmp_path / "pack.zip"),
    )
    assert "error" in result


def test_cli_runs(tmp_path):
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    panel = _make_panel_csv(tmp_path)
    out = tmp_path / "pack.zip"

    result = _run_pack_cli(
        "--panel-csv",
        str(panel),
        "--evidence-dir",
        str(ev_dir),
        "--out",
        str(out),
    )

    assert result.returncode == 0
    assert out.exists()


def test_cli_manifest_output(tmp_path):
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    panel = _make_panel_csv(tmp_path)
    out = tmp_path / "pack.zip"
    manifest = tmp_path / "manifest.json"

    result = _run_pack_cli(
        "--panel-csv",
        str(panel),
        "--evidence-dir",
        str(ev_dir),
        "--out",
        str(out),
        "--manifest-out",
        str(manifest),
    )

    assert result.returncode == 0
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert "evidence_count" in data
    assert "panel_csv_sha256" in data
    assert "synthesis_order_sha256" in data
    assert data["pack_standard"] == "fail_closed_lab_handoff_v1"


def test_cli_returns_2_for_missing_evidence(tmp_path):
    ev_dir = _make_evidence(tmp_path, "C1")
    panel = _make_panel_csv(tmp_path)
    out = tmp_path / "pack.zip"

    result = _run_pack_cli(
        "--panel-csv",
        str(panel),
        "--evidence-dir",
        str(ev_dir),
        "--out",
        str(out),
    )

    assert result.returncode == 2
    assert "Missing evidence certificate" in result.stderr


def test_cli_verify_pack(tmp_path):
    ev_dir = _make_evidence(tmp_path, "C1", "C2")
    panel = _make_panel_csv(tmp_path)
    out = tmp_path / "pack.zip"

    _build_pack(panel, ev_dir, out)
    result = _run_pack_cli("--verify-pack", str(out))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
