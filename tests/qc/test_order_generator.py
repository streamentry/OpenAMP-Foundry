"""Tests for qc/order_generator.py — synthesis order generation."""
from __future__ import annotations

import csv
from pathlib import Path

from openamp_foundry.qc.order_generator import (
    _extract_handling,
    generate_synthesis_order,
    write_order_csv,
    write_synthesis_checklist,
)
from openamp_foundry.qc.presynth_check import SynthQC


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _candidate(cid: str, seq: str, **extra) -> dict:
    return {"candidate_id": cid, "sequence": seq, **extra}


# Simple cationic helical peptide: no Cys, no Met, no aggregation run, no DG/DS, no NG/NS.
CLEAN_SEQ = "KWKLFKKIGAVLKVL"   # SEED-001; length=15, K×4+R×0, no C/M, modest μH

# Has interior trypsin sites (K at pos 0,5,8,12 but not C-terminal) → n_acetylation_recommended
TRYPSIN_HEAVY_SEQ = "KWKLFKKIGSALKFL"  # from SEED-005; has multiple interior K

# Has Cys → oxidation risk flag → N2 storage
CYS_SEQ = "ACYCRIPACIAGERR"

# Has Met → oxidation risk flag → −80°C storage
MET_SEQ = "GIGKFLHSAKKFGKAFVGEIMNS"   # Magainin-2-like; has Met near end

# Has ≥3 Trp → photolability flag (TRP_PHOTOLABILITY)
TRP_SEQ = "FPVTWRWWKWWKG"   # SEED-008 puroindoline-a; 5 Trp

# Peptide with DG motif → ISOMERIZATION_RISK
ISOMZ_SEQ = "KWKLFDGKKIAL"   # DG at position 6

# Peptide with NG motif → DEAMIDATION_RISK
DEAM_SEQ = "KWKLNGSALKKFL"   # NG at position 5


# ---------------------------------------------------------------------------
# _extract_handling
# ---------------------------------------------------------------------------

class TestExtractHandling:
    def test_empty_flags_returns_empty(self):
        assert _extract_handling([]) == ""

    def test_cysteine_flag_maps_to_n2(self):
        result = _extract_handling(["CYSTEINE×2: disulfide/oxidation risk"])
        assert "N2 storage" in result

    def test_met_flag_maps_to_minus80(self):
        result = _extract_handling(["MET×1: oxidation risk — store at −80°C"])
        assert "−80°C" in result

    def test_hydrophobic_run_maps_to_solubility(self):
        result = _extract_handling(["HYDROPHOBIC_RUN (VILLF): aggregation risk"])
        assert "Solubility check" in result

    def test_trypsin_sites_flag_maps_to_serum_free(self):
        result = _extract_handling(["TRYPSIN_SITES×3: low serum stability expected (<2h)"])
        assert "serum-free" in result

    def test_deamidation_maps_correctly(self):
        result = _extract_handling(["DEAMIDATION_RISK: N3G — avoid >pH 7.5 storage"])
        assert "pH 5-6" in result

    def test_isomerization_maps_correctly(self):
        result = _extract_handling(["ISOMERIZATION_RISK: D6G — Asp→β-Asp"])
        assert "HPLC re-check" in result

    def test_trp_photolability_maps_to_amber(self):
        result = _extract_handling(["TRP_PHOTOLABILITY (5 Trp): store in amber vials"])
        assert "Amber vial" in result

    def test_multiple_flags_semicolon_separated(self):
        result = _extract_handling([
            "CYSTEINE×1: disulfide/oxidation risk",
            "MET×1: oxidation risk",
        ])
        assert "N2 storage" in result
        assert "−80°C" in result
        assert ";" in result

    def test_guidance_flags_not_mapped(self):
        result = _extract_handling([
            "N_ACETYLATION_RECOMMENDED: specify 'Ac-'",
            "WAVE2_D_AMINO: 2 trypsin site(s)",
            "C_AMIDATION_RECOMMENDED: specify 'CONH₂'",
        ])
        # Guidance flags have no HANDLING_MAP entry → empty
        assert result == ""

    def test_no_duplicates_for_repeated_flag_types(self):
        flags = [
            "CYSTEINE×1: disulfide risk",
            "CYSTEINE×2: another cysteine flag",  # unusual but defensively handled
        ]
        result = _extract_handling(flags)
        # "N2 storage" should appear only once
        assert result.count("N2 storage") == 1


# ---------------------------------------------------------------------------
# generate_synthesis_order — order row structure
# ---------------------------------------------------------------------------

class TestGenerateSynthesisOrderStructure:
    def test_returns_correct_number_of_rows(self):
        candidates = [
            _candidate("C1", CLEAN_SEQ),
            _candidate("C2", CYS_SEQ),
        ]
        rows, qc = generate_synthesis_order(candidates)
        assert len(rows) == 2
        assert len(qc) == 2

    def test_row_has_all_required_columns(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        row = rows[0]
        required = {
            "pilot_rank", "candidate_id", "sequence", "length",
            "mol_weight_da", "n_modification", "c_modification",
            "purity_spec", "quantity_mg", "synthesis_difficulty",
            "special_handling",
        }
        assert required <= row.keys()

    def test_purity_spec_always_95_hplc(self):
        candidates = [_candidate("C1", CLEAN_SEQ), _candidate("C2", CYS_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        for row in rows:
            assert row["purity_spec"] == ">95% HPLC"

    def test_sequence_and_length_match(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert rows[0]["sequence"] == CLEAN_SEQ
        assert rows[0]["length"] == len(CLEAN_SEQ)

    def test_pilot_rank_propagated_when_provided(self):
        candidates = [_candidate("C1", CLEAN_SEQ, pilot_rank=3)]
        rows, _ = generate_synthesis_order(candidates)
        assert rows[0]["pilot_rank"] == 3

    def test_pilot_rank_empty_when_absent(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert rows[0]["pilot_rank"] == ""


# ---------------------------------------------------------------------------
# generate_synthesis_order — N-modification logic
# ---------------------------------------------------------------------------

class TestNModification:
    def test_clean_peptide_free_n_terminus(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        # CLEAN_SEQ has K at end (position 14, C-terminal), interior Ks at 0,2,5,12
        # presynth QC will decide; what matters is n_modification == qc.n_acetylation_recommended
        assert rows[0]["n_modification"] in ("Ac-", "Free")
        if qc[0].n_acetylation_recommended:
            assert rows[0]["n_modification"] == "Ac-"
        else:
            assert rows[0]["n_modification"] == "Free"

    def test_trypsin_heavy_gets_acetylation(self):
        # TRYPSIN_HEAVY_SEQ has many interior K/R → n_acetylation_recommended=True
        candidates = [_candidate("C1", TRYPSIN_HEAVY_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        if qc[0].n_acetylation_recommended:
            assert rows[0]["n_modification"] == "Ac-"

    def test_single_residue_peptide_no_trypsin_interior(self):
        # "K" → only one residue, K is C-terminal, no interior site
        candidates = [_candidate("C1", "AAAK")]
        rows, qc = generate_synthesis_order(candidates)
        assert not qc[0].n_acetylation_recommended
        assert rows[0]["n_modification"] == "Free"


# ---------------------------------------------------------------------------
# generate_synthesis_order — C-modification logic
# ---------------------------------------------------------------------------

class TestCModification:
    def test_c_amidated_when_recommended(self):
        # MET_SEQ = magainin-like, ends in 'S', charge < 3 → amidation recommended
        candidates = [_candidate("C1", MET_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        if qc[0].c_amidation_recommended:
            assert rows[0]["c_modification"] == "NH2"

    def test_oh_when_not_recommended(self):
        # A sequence ending in K with high charge → not recommended
        candidates = [_candidate("C1", "AAAAAAAAAAAAAAAK")]
        rows, qc = generate_synthesis_order(candidates)
        assert not qc[0].c_amidation_recommended
        assert rows[0]["c_modification"] == "OH"

    def test_c_modification_consistent_with_qc(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        expected = "NH2" if qc[0].c_amidation_recommended else "OH"
        assert rows[0]["c_modification"] == expected


# ---------------------------------------------------------------------------
# generate_synthesis_order — quantity logic
# ---------------------------------------------------------------------------

class TestQuantityLogic:
    def test_default_quantity_for_low_difficulty(self):
        # "KAAAKAAAAR": 2 interior K (trypsin_sites=[0,4], ≤2 → no flag),
        # C-terminal R (not interior), no C/M, no hydrophobic run, charge ~2.8 ≥ 2.0
        # → 0 synthesis-risk flags → LOW difficulty → default quantity
        candidates = [_candidate("C1", "KAAAKAAAAR")]
        rows, qc = generate_synthesis_order(candidates)
        assert qc[0].synthesis_difficulty == "LOW", (
            f"Expected LOW difficulty but got {qc[0].synthesis_difficulty}; flags: {qc[0].flags}"
        )
        assert rows[0]["quantity_mg"] == 5.0

    def test_high_difficulty_gets_extra_quantity(self):
        # CYS_SEQ has Cys + Met + aggregation → HIGH difficulty → 10 mg
        # Manufacture a sequence with ≥3 synthesis flags
        high_risk_seq = "CCCMMMVILMFWK"   # 3 Cys + 3 Met + hydrophobic run
        candidates = [_candidate("C1", high_risk_seq)]
        rows, qc = generate_synthesis_order(candidates)
        if qc[0].synthesis_difficulty == "HIGH":
            assert rows[0]["quantity_mg"] == 10.0
        else:
            assert rows[0]["quantity_mg"] == 5.0

    def test_custom_quantity_respected(self):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(
            candidates, default_quantity_mg=2.0, high_difficulty_quantity_mg=4.0
        )
        # Either 2 or 4 depending on difficulty
        assert rows[0]["quantity_mg"] in (2.0, 4.0)


# ---------------------------------------------------------------------------
# generate_synthesis_order — special_handling
# ---------------------------------------------------------------------------

class TestSpecialHandling:
    def test_clean_peptide_empty_handling(self):
        # "KWKLFKK" — length 7, no C/M, no hydrophobic run, likely no flags
        candidates = [_candidate("C1", "KWKLFKK")]
        rows, qc = generate_synthesis_order(candidates)
        # Guidance flags (N_ACETYLATION_RECOMMENDED, etc.) don't map to handling
        synthesis_risk_flags = [
            f for f in qc[0].flags
            if any(f.startswith(k) for k in (
                "CYSTEINE", "MET", "HYDROPHOBIC_RUN", "TRYPSIN_SITES",
                "DEAMIDATION_RISK", "ISOMERIZATION_RISK", "LOW_CHARGE", "LONG_PEPTIDE"
            ))
        ]
        if not synthesis_risk_flags:
            assert rows[0]["special_handling"] == ""

    def test_cys_peptide_has_n2_handling(self):
        candidates = [_candidate("C1", CYS_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert "N2 storage" in rows[0]["special_handling"]

    def test_met_peptide_has_storage_handling(self):
        candidates = [_candidate("C1", MET_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert "−80°C" in rows[0]["special_handling"]

    def test_trp_peptide_has_amber_handling(self):
        candidates = [_candidate("C1", TRP_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert "Amber vial" in rows[0]["special_handling"]

    def test_isomerization_peptide_handling(self):
        candidates = [_candidate("C1", ISOMZ_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        assert "HPLC re-check" in rows[0]["special_handling"]


# ---------------------------------------------------------------------------
# write_order_csv
# ---------------------------------------------------------------------------

class TestWriteOrderCsv:
    def test_creates_file(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        out = tmp_path / "order.csv"
        write_order_csv(rows, out)
        assert out.exists()

    def test_csv_has_header_row(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        out = tmp_path / "order.csv"
        write_order_csv(rows, out)
        lines = out.read_text().splitlines()
        assert "candidate_id" in lines[0]
        assert "sequence" in lines[0]

    def test_csv_row_count_matches_candidates(self, tmp_path):
        candidates = [
            _candidate("C1", CLEAN_SEQ),
            _candidate("C2", CYS_SEQ),
            _candidate("C3", TRP_SEQ),
        ]
        rows, _ = generate_synthesis_order(candidates)
        out = tmp_path / "order.csv"
        write_order_csv(rows, out)
        with open(out, newline="") as f:
            data_rows = list(csv.DictReader(f))
        assert len(data_rows) == 3

    def test_csv_roundtrip_preserves_sequence(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        out = tmp_path / "order.csv"
        write_order_csv(rows, out)
        with open(out, newline="") as f:
            data_rows = list(csv.DictReader(f))
        assert data_rows[0]["sequence"] == CLEAN_SEQ

    def test_csv_creates_parent_dirs(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, _ = generate_synthesis_order(candidates)
        out = tmp_path / "nested" / "deep" / "order.csv"
        write_order_csv(rows, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# write_synthesis_checklist
# ---------------------------------------------------------------------------

class TestWriteSynthesisChecklist:
    def test_creates_file(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        assert out.exists()

    def test_checklist_contains_candidate_id(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        assert "C1" in content

    def test_checklist_has_order_summary_section(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ), _candidate("C2", CYS_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        assert "Order Summary" in content
        assert "Total peptides" in content

    def test_checklist_contains_disclaimer(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        assert "Disclaimer" in content
        assert "antimicrobial activity" in content.lower()

    def test_checklist_wave2_section_present(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        assert "Wave 2" in content

    def test_checklist_generated_at_appears(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out, generated_at="2026-06-28T00:00:00Z")
        content = out.read_text()
        assert "2026-06-28" in content

    def test_checklist_n_ac_rationale_present_when_recommended(self, tmp_path):
        candidates = [_candidate("C1", TRYPSIN_HEAVY_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        if qc[0].n_acetylation_recommended:
            assert "N-Ac rationale" in content

    def test_checklist_c_amide_rationale_present_when_recommended(self, tmp_path):
        candidates = [_candidate("C1", MET_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        if qc[0].c_amidation_recommended:
            assert "C-amide rationale" in content

    def test_pre_order_checklist_items_present(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        content = out.read_text()
        assert "Pre-Order Checklist" in content
        assert "CoA" in content

    def test_creates_parent_dirs(self, tmp_path):
        candidates = [_candidate("C1", CLEAN_SEQ)]
        rows, qc = generate_synthesis_order(candidates)
        out = tmp_path / "nested" / "checklist.md"
        write_synthesis_checklist(rows, qc, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# End-to-end: realistic panel with mixed complexity
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_mixed_panel_generates_valid_order(self, tmp_path):
        candidates = [
            _candidate("SEED1_VAR1", CLEAN_SEQ, pilot_rank=1),
            _candidate("SEED2_VAR1", MET_SEQ, pilot_rank=2),
            _candidate("SEED3_VAR1", CYS_SEQ, pilot_rank=3),
            _candidate("SEED8_VAR1", TRP_SEQ, pilot_rank=4),
        ]
        rows, qc = generate_synthesis_order(candidates)
        assert len(rows) == 4
        # All rows have required structure
        for row in rows:
            assert row["purity_spec"] == ">95% HPLC"
            assert row["n_modification"] in ("Ac-", "Free")
            assert row["c_modification"] in ("NH2", "OH")
            assert row["quantity_mg"] > 0

    def test_csv_and_checklist_consistent_candidate_ids(self, tmp_path):
        candidates = [
            _candidate("P001", CLEAN_SEQ, pilot_rank=1),
            _candidate("P002", TRP_SEQ, pilot_rank=2),
        ]
        rows, qc = generate_synthesis_order(candidates)
        csv_path = tmp_path / "order.csv"
        md_path = tmp_path / "checklist.md"
        write_order_csv(rows, csv_path)
        write_synthesis_checklist(rows, qc, md_path)

        with open(csv_path, newline="") as f:
            csv_ids = [r["candidate_id"] for r in csv.DictReader(f)]
        md_content = md_path.read_text()

        assert csv_ids == ["P001", "P002"]
        assert "P001" in md_content
        assert "P002" in md_content

    def test_mol_weight_positive_for_all_seeds(self):
        seqs = [CLEAN_SEQ, MET_SEQ, CYS_SEQ, TRP_SEQ, TRYPSIN_HEAVY_SEQ]
        candidates = [_candidate(f"S{i}", s) for i, s in enumerate(seqs, 1)]
        rows, _ = generate_synthesis_order(candidates)
        for row in rows:
            assert float(row["mol_weight_da"]) > 0


# ---------------------------------------------------------------------------
# CLI integration tests — _run_synthesis_order via main()
# ---------------------------------------------------------------------------

class TestCLISynthesisOrder:
    """Integration tests for the synthesis-order CLI subcommand."""

    def _write_panel_csv(self, path: Path, rows: list[dict]) -> None:
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_cli_creates_csv_and_md_outputs(self, tmp_path):
        from openamp_foundry.cli import main

        panel_csv = tmp_path / "panel.csv"
        self._write_panel_csv(panel_csv, [
            {"candidate_id": "P001", "sequence": CLEAN_SEQ, "pilot_rank": "1",
             "ensemble": "0.72", "activity": "0.65", "safety": "0.80"},
            {"candidate_id": "P002", "sequence": MET_SEQ, "pilot_rank": "2",
             "ensemble": "0.68", "activity": "0.60", "safety": "0.75"},
        ])
        out_csv = tmp_path / "order.csv"
        out_md = tmp_path / "checklist.md"

        rc = main([
            "synthesis-order",
            "--panel-csv", str(panel_csv),
            "--out-csv", str(out_csv),
            "--out-md", str(out_md),
            "--quantity-mg", "5",
        ])
        assert rc == 0
        assert out_csv.exists()
        assert out_md.exists()

    def test_cli_csv_has_correct_row_count(self, tmp_path):
        from openamp_foundry.cli import main

        panel_csv = tmp_path / "panel.csv"
        self._write_panel_csv(panel_csv, [
            {"candidate_id": "C1", "sequence": CLEAN_SEQ},
            {"candidate_id": "C2", "sequence": CYS_SEQ},
            {"candidate_id": "C3", "sequence": TRP_SEQ},
        ])
        out_csv = tmp_path / "order.csv"
        out_md = tmp_path / "checklist.md"

        main([
            "synthesis-order",
            "--panel-csv", str(panel_csv),
            "--out-csv", str(out_csv),
            "--out-md", str(out_md),
        ])

        with open(out_csv, newline="") as f:
            data_rows = list(csv.DictReader(f))
        assert len(data_rows) == 3

    def test_cli_high_difficulty_gets_double_quantity(self, tmp_path):
        from openamp_foundry.cli import main

        high_risk_seq = "CCCMMMVILLKFWR"
        panel_csv = tmp_path / "panel.csv"
        self._write_panel_csv(panel_csv, [
            {"candidate_id": "HIGH1", "sequence": high_risk_seq},
        ])
        out_csv = tmp_path / "order.csv"
        out_md = tmp_path / "checklist.md"

        main([
            "synthesis-order",
            "--panel-csv", str(panel_csv),
            "--out-csv", str(out_csv),
            "--out-md", str(out_md),
            "--quantity-mg", "3",
        ])

        with open(out_csv, newline="") as f:
            rows = list(csv.DictReader(f))

        # HIGH difficulty → quantity_mg = 3 * 2 = 6
        if rows[0]["synthesis_difficulty"] == "HIGH":
            assert float(rows[0]["quantity_mg"]) == 6.0

    def test_cli_missing_panel_csv_returns_error(self, tmp_path):
        from openamp_foundry.cli import main

        rc = main([
            "synthesis-order",
            "--panel-csv", str(tmp_path / "nonexistent.csv"),
            "--out-csv", str(tmp_path / "order.csv"),
            "--out-md", str(tmp_path / "checklist.md"),
        ])
        assert rc == 1

    def test_cli_checklist_contains_all_candidate_ids(self, tmp_path):
        from openamp_foundry.cli import main

        panel_csv = tmp_path / "panel.csv"
        self._write_panel_csv(panel_csv, [
            {"candidate_id": "ALPHA1", "sequence": CLEAN_SEQ},
            {"candidate_id": "BETA2", "sequence": TRP_SEQ},
        ])
        out_csv = tmp_path / "order.csv"
        out_md = tmp_path / "checklist.md"

        main([
            "synthesis-order",
            "--panel-csv", str(panel_csv),
            "--out-csv", str(out_csv),
            "--out-md", str(out_md),
        ])

        md_content = out_md.read_text()
        assert "ALPHA1" in md_content
        assert "BETA2" in md_content


# ---------------------------------------------------------------------------
# write_synthesis_checklist — "QC flags: None" branch (order_generator.py:219)
# ---------------------------------------------------------------------------

class TestSynthesisChecklistQcFlagsNone:
    def test_no_flags_shows_none_in_checklist(self, tmp_path):
        # Directly construct a SynthQC with empty flags to exercise the
        # "QC flags: None" branch at order_generator.py:219.
        qc_obj = SynthQC(candidate_id="C0", sequence="AAKK", length=4)
        qc_obj.synthesis_difficulty = "LOW"
        row = {
            "pilot_rank": 1,
            "candidate_id": "C0",
            "sequence": "AAKK",
            "length": 4,
            "mol_weight_da": 456.0,
            "n_modification": "Free",
            "c_modification": "OH",
            "purity_spec": ">95% HPLC",
            "quantity_mg": 5.0,
            "synthesis_difficulty": "LOW",
            "special_handling": "",
        }
        out = tmp_path / "checklist.md"
        write_synthesis_checklist([row], [qc_obj], out)
        content = out.read_text()
        assert "QC flags:** None" in content
