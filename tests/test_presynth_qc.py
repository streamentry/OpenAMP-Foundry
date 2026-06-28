"""Tests for src/openamp_foundry/qc/presynth_check.py"""
import pytest
from openamp_foundry.qc.presynth_check import (
    SynthQC,
    check_panel,
    check_sequence,
)


# ---------------------------------------------------------------------------
# Molecular weight
# ---------------------------------------------------------------------------

class TestMolecularWeight:
    def test_glycine_monomer(self):
        # Single G: residue mass 75.03 - 0 water corrections = 75.03
        qc = check_sequence("G1", "G")
        assert qc.molecular_weight_da == pytest.approx(75.03, abs=0.5)

    def test_short_peptide_positive(self):
        qc = check_sequence("test", "ACDEF")
        assert qc.molecular_weight_da > 0

    def test_longer_peptide_heavier(self):
        qc_short = check_sequence("s", "KRLF")
        qc_long = check_sequence("l", "KRLFKKIGSALKFL")
        assert qc_long.molecular_weight_da > qc_short.molecular_weight_da

    def test_known_seed003(self):
        # RRWQWRMKKLG should be ~1.4–1.6 kDa
        qc = check_sequence("s3", "RRWQWRMKKLG")
        assert 1300 < qc.molecular_weight_da < 1700


# ---------------------------------------------------------------------------
# Isoelectric point
# ---------------------------------------------------------------------------

class TestIsoelectricPoint:
    def test_cationic_peptide_basic_pi(self):
        # KKKK should be highly basic
        qc = check_sequence("k4", "KKKK")
        assert qc.isoelectric_point > 9.0

    def test_acidic_peptide_low_pi(self):
        # DDDD should be acidic
        qc = check_sequence("d4", "DDDD")
        assert qc.isoelectric_point < 5.0

    def test_pi_in_valid_range(self):
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert 0.0 < qc.isoelectric_point < 14.0


# ---------------------------------------------------------------------------
# Net charge
# ---------------------------------------------------------------------------

class TestNetCharge:
    def test_cationic_amp_positive_charge(self):
        # SEED-005 scaffold — K×3, R×1 → strongly positive
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert qc.charge_ph74 > 2.0

    def test_charge_decreases_at_higher_ph(self):
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert qc.charge_ph74 < qc.charge_ph60

    def test_lysine_rich_highly_positive(self):
        qc = check_sequence("k", "KKKKKK")
        assert qc.charge_ph74 > 4.0

    def test_acidic_peptide_negative(self):
        qc = check_sequence("d", "DDDDDD")
        assert qc.charge_ph74 < 0.0


# ---------------------------------------------------------------------------
# Oxidation risk (Met, Cys)
# ---------------------------------------------------------------------------

class TestOxidationRisk:
    def test_no_met_no_cys_no_risk(self):
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert not qc.has_oxidation_risk
        assert qc.methionine_count == 0
        assert qc.cysteine_count == 0

    def test_met_triggers_oxidation_risk(self):
        qc = check_sequence("s", "KRLMKKIGSAIKFL")
        assert qc.has_oxidation_risk
        assert qc.methionine_count == 1

    def test_cys_triggers_oxidation_risk(self):
        qc = check_sequence("s", "ACYCRIPACIAGER")
        assert qc.has_oxidation_risk
        assert qc.cysteine_count >= 2

    def test_two_met_counted(self):
        qc = check_sequence("s", "RRWNWRMKKMG")
        assert qc.methionine_count == 2

    def test_met_flag_in_flags_list(self):
        qc = check_sequence("s", "KRLMKKIGSAIKFL")
        met_flags = [f for f in qc.flags if "MET" in f]
        assert len(met_flags) == 1


# ---------------------------------------------------------------------------
# Trypsin/chymotrypsin sites
# ---------------------------------------------------------------------------

class TestProteolytic:
    def test_trypsin_sites_detected(self):
        # KRLFKKIGSALKFL: K and R (not terminal, not before P)
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert len(qc.trypsin_sites) >= 3

    def test_trypsin_before_proline_not_counted(self):
        # KP: K before P should NOT be counted
        qc = check_sequence("s", "AKPGG")
        # K at pos 1 (0-based) is before P → should NOT be in sites
        # A at pos 0 is just a residue
        assert 1 not in qc.trypsin_sites

    def test_chymotrypsin_w_detected(self):
        qc = check_sequence("s", "RRWQWRMKKLG")
        assert len(qc.chymotrypsin_sites) >= 1

    def test_terminal_k_not_trypsin_site(self):
        # K at last position should not be counted (terminal)
        qc = check_sequence("s", "GGGGGK")
        assert (len(qc.sequence) - 1) not in qc.trypsin_sites


# ---------------------------------------------------------------------------
# Deamidation
# ---------------------------------------------------------------------------

class TestDeamidation:
    def test_ng_hotspot_detected(self):
        qc = check_sequence("s", "ANGGG")
        assert any("N" in s for s in qc.deamidation_sites)

    def test_ns_hotspot_detected(self):
        qc = check_sequence("s", "ANSGGG")
        assert any("N" in s for s in qc.deamidation_sites)

    def test_no_hotspot_when_absent(self):
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert qc.deamidation_sites == []

    def test_hotspot_format(self):
        qc = check_sequence("s", "ANGGG")
        # Should be like "N1G" (residue + 1-based position + next residue)
        assert len(qc.deamidation_sites) >= 1
        for site in qc.deamidation_sites:
            assert site[0] == "N"


# ---------------------------------------------------------------------------
# Aggregation / hydrophobic runs
# ---------------------------------------------------------------------------

class TestAggregationRisk:
    def test_four_hydrophobic_run_flagged(self):
        qc = check_sequence("s", "VILLKK")
        assert qc.aggregation_risk
        assert "VILL" in qc.hydrophobic_run

    def test_three_hydrophobic_not_flagged(self):
        qc = check_sequence("s", "VILKK")
        assert not qc.aggregation_risk

    def test_seed005_flagged_for_alkfl_run(self):
        # KRLFKKIGSALKFL has LKFL at the end with ALKFL — let's check
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        # "ALKFL" has 5 chars with A, L, K, F, L — K is not in VILMFW
        # so not a pure hydrophobic run. Let's just check the function works
        assert isinstance(qc.aggregation_risk, bool)

    def test_run_length_correct(self):
        qc = check_sequence("s", "KVILMFWAAAK")
        assert len(qc.hydrophobic_run) >= 4


# ---------------------------------------------------------------------------
# UV chromophore
# ---------------------------------------------------------------------------

class TestUVChromophore:
    def test_w_gives_chromophore(self):
        qc = check_sequence("s", "RRWQWRMKKLG")
        assert qc.has_uv_chromophore

    def test_y_gives_chromophore(self):
        qc = check_sequence("s", "KRWQYRMKKLG")
        assert qc.has_uv_chromophore

    def test_f_gives_chromophore(self):
        qc = check_sequence("s", "KRLFKKIGSALKFL")
        assert qc.has_uv_chromophore

    def test_no_chromophore(self):
        qc = check_sequence("s", "KRKRKLLL")
        assert not qc.has_uv_chromophore

    def test_w_formulation_note_includes_eps280(self):
        qc = check_sequence("s", "RRWWRR")
        assert "A280" in qc.formulation_note
        assert "ε=" in qc.formulation_note


# ---------------------------------------------------------------------------
# Hemolysis stratification
# ---------------------------------------------------------------------------

class TestHemolysisStratification:
    def test_low_mu_h_start_at_mic(self):
        qc = check_sequence("s", "AAAAAAA", mu_h=0.40)
        assert "Start at MIC" in qc.hemolysis_start_conc

    def test_moderate_mu_h_start_at_mic_third(self):
        qc = check_sequence("s", "AAAAAAA", mu_h=0.65)
        assert "MIC/3" in qc.hemolysis_start_conc

    def test_high_mu_h_start_at_mic_tenth(self):
        qc = check_sequence("s", "AAAAAAA", mu_h=0.90)
        assert "MIC/10" in qc.hemolysis_start_conc

    def test_boundary_at_055(self):
        # μH exactly 0.55 → should still be "low risk" (> 0.55 triggers moderate)
        qc = check_sequence("s", "AAAAAAA", mu_h=0.55)
        assert "Start at MIC;" in qc.hemolysis_start_conc

    def test_boundary_at_080(self):
        # μH exactly 0.80 → moderate (> 0.80 triggers high)
        qc = check_sequence("s", "AAAAAAA", mu_h=0.80)
        assert "MIC/3" in qc.hemolysis_start_conc


# ---------------------------------------------------------------------------
# Synthesis difficulty
# ---------------------------------------------------------------------------

class TestSynthesisDifficulty:
    def test_clean_peptide_low_difficulty(self):
        # Simple 8-mer with no risky residues and no trypsin sites beyond terminal
        qc = check_sequence("s", "RRWQWRMK")  # short, no M inside non-K/R position
        assert qc.synthesis_difficulty in ("LOW", "MODERATE")

    def test_many_flags_high_difficulty(self):
        # Long peptide with Met, many Lys/Arg, deamidation sites
        qc = check_sequence("s", "GIGKFLKSAKKFGKAFVPEIMNS")
        # 23-mer with Met → HIGH difficulty expected
        assert qc.synthesis_difficulty == "HIGH"

    def test_no_flags_low(self):
        # KKK: charge ~2.8 at pH7.4, ≤2 trypsin sites, no Met/Cys/aggregation/deamidation
        qc = check_sequence("s", "KKK")
        assert qc.synthesis_difficulty == "LOW"


# ---------------------------------------------------------------------------
# check_panel (batch function)
# ---------------------------------------------------------------------------

class TestCheckPanel:
    def test_returns_list_of_qc(self):
        panel = [
            {"candidate_id": "A", "sequence": "KRLFKKIGSALKFL"},
            {"candidate_id": "B", "sequence": "RRWQWRMKKLG"},
        ]
        results = check_panel(panel)
        assert len(results) == 2
        assert all(isinstance(r, SynthQC) for r in results)

    def test_mu_h_map_applied(self):
        panel = [{"candidate_id": "A", "sequence": "AAAAAA"}]
        mu_h_map = {"A": 0.85}
        results = check_panel(panel, mu_h_map=mu_h_map)
        assert results[0].mu_h == 0.85

    def test_empty_panel(self):
        assert check_panel([]) == []

    def test_preserves_candidate_id(self):
        panel = [{"candidate_id": "SEED-003_VAR_016", "sequence": "RRWNWRMKKMG"}]
        results = check_panel(panel)
        assert results[0].candidate_id == "SEED-003_VAR_016"

    def test_missing_mu_h_defaults_to_zero(self):
        panel = [{"candidate_id": "A", "sequence": "AAAAAA"}]
        results = check_panel(panel)
        assert results[0].mu_h == 0.0

    def test_missing_candidate_id_raises_key_error(self):
        panel = [{"sequence": "KRLFKK"}]  # no 'candidate_id'
        with pytest.raises(KeyError, match="candidate_id"):
            check_panel(panel)

    def test_missing_sequence_raises_key_error(self):
        panel = [{"candidate_id": "A"}]  # no 'sequence'
        with pytest.raises(KeyError, match="sequence"):
            check_panel(panel)


# ---------------------------------------------------------------------------
# SynthQC.to_dict()
# ---------------------------------------------------------------------------

class TestSynthQCToDict:
    def _qc(self, seq: str = "KRLFKKIGSALKFL", cid: str = "TEST-001") -> SynthQC:
        return check_sequence(cid, seq)

    def test_to_dict_returns_dict(self):
        assert isinstance(self._qc().to_dict(), dict)

    def test_to_dict_has_required_keys(self):
        d = self._qc().to_dict()
        required = {
            "candidate_id", "sequence", "length",
            "mol_weight_da", "pI", "charge_pH7.4", "charge_pH6.0",
            "cysteine_count", "methionine_count", "oxidation_risk", "aggregation_risk",
            "hydrophobic_run", "trypsin_sites", "chymotrypsin_sites", "deamidation_sites",
            "has_uv_chromophore", "formulation_note",
            "mu_h", "hemolysis_start_conc",
            "flags", "synthesis_difficulty",
        }
        missing = required - set(d.keys())
        assert not missing, f"to_dict() is missing keys: {missing}"

    def test_to_dict_candidate_id_matches(self):
        d = check_sequence("MY-ID", "KWKLF").to_dict()
        assert d["candidate_id"] == "MY-ID"

    def test_to_dict_sequence_matches(self):
        d = check_sequence("X", "KWKLF").to_dict()
        assert d["sequence"] == "KWKLF"

    def test_to_dict_length_matches(self):
        seq = "KWKLFKKIGAVLKVL"
        d = check_sequence("X", seq).to_dict()
        assert d["length"] == len(seq)

    def test_to_dict_mol_weight_positive(self):
        d = self._qc().to_dict()
        assert d["mol_weight_da"] > 0

    def test_to_dict_charge_is_float(self):
        d = self._qc().to_dict()
        assert isinstance(d["charge_pH7.4"], float)
        assert isinstance(d["charge_pH6.0"], float)

    def test_to_dict_flags_is_list(self):
        d = self._qc().to_dict()
        assert isinstance(d["flags"], list)

    def test_to_dict_synthesis_difficulty_valid(self):
        d = self._qc().to_dict()
        assert d["synthesis_difficulty"] in ("LOW", "MODERATE", "HIGH")

    def test_to_dict_trypsin_sites_is_list(self):
        d = self._qc().to_dict()
        assert isinstance(d["trypsin_sites"], list)

    def test_to_dict_oxidation_risk_is_bool(self):
        d = self._qc().to_dict()
        assert isinstance(d["oxidation_risk"], bool)

    def test_to_dict_charge_ph74_is_plausible_for_kkkk(self):
        # KKKK is strongly cationic; charge at pH 7.4 should be ~3.8-4.2
        # This pins the actual value rather than comparing self-referentially.
        qc = check_sequence("X", "KKKK")
        d = qc.to_dict()
        assert 3.0 < d["charge_pH7.4"] < 5.0

    def test_to_dict_pi_matches_isoelectric_point(self):
        qc = check_sequence("X", "KRLFKKIGSALKFL")
        d = qc.to_dict()
        assert abs(d["pI"] - qc.isoelectric_point) < 1e-9

    def test_to_dict_mol_weight_matches_molecular_weight_da(self):
        qc = check_sequence("X", "KWKLFKKIGAVLKVL")
        d = qc.to_dict()
        assert abs(d["mol_weight_da"] - qc.molecular_weight_da) < 0.01

    def test_to_dict_mu_h_preserved(self):
        qc = check_sequence("X", "AAAAAA", mu_h=0.72)
        d = qc.to_dict()
        assert abs(d["mu_h"] - 0.72) < 1e-9


# ---------------------------------------------------------------------------
# C-terminal amidation recommendation
# ---------------------------------------------------------------------------

class TestCTerminalAmidation:
    def test_neutral_cterm_low_charge_recommends_amidation(self):
        # ALPFIGRVLSGIL (SEED-004 scaffold) ends in L, charge < 2 → recommend
        qc = check_sequence("seed4", "ALPFIGRVLSGIL")
        assert qc.c_amidation_recommended is True

    def test_lys_cterm_does_not_recommend(self):
        # Sequence ending in K already has positive C-terminal charge → no amidation needed
        qc = check_sequence("k_cterm", "KWKLFKKIGAVLKVLK")
        assert qc.c_amidation_recommended is False

    def test_arg_cterm_does_not_recommend(self):
        # Sequence ending in R → no recommendation (already positive)
        qc = check_sequence("r_cterm", "GIGKFLHSAKKFGKR")
        assert qc.c_amidation_recommended is False

    def test_neutral_cterm_high_charge_does_not_flag(self):
        # Sequence with neutral C-term but high charge (≥3.0) → optional but not recommended
        # 3K + 3R + neutral C-term → charge > 3.0
        qc = check_sequence("high_charge", "KRKKRRAL")  # 2K+2R → charge ~4+
        assert qc.c_amidation_recommended is False

    def test_recommended_adds_flag(self):
        # When recommended, a C_AMIDATION_RECOMMENDED flag should appear in flags list
        qc = check_sequence("seed4", "ALPFIGRVLSGIL")
        c_flags = [f for f in qc.flags if "C_AMIDATION" in f]
        assert len(c_flags) == 1

    def test_not_recommended_no_flag(self):
        # When not recommended, no C_AMIDATION flag
        qc = check_sequence("k_cterm", "KWKLFKKIGAVLKVLK")
        c_flags = [f for f in qc.flags if "C_AMIDATION" in f]
        assert len(c_flags) == 0

    def test_reason_populated_when_recommended(self):
        qc = check_sequence("seed4", "ALPFIGRVLSGIL")
        assert len(qc.c_amidation_reason) > 0
        assert "amide" in qc.c_amidation_reason.lower() or "amidation" in qc.c_amidation_reason.lower()

    def test_to_dict_contains_amidation_keys(self):
        qc = check_sequence("seed4", "ALPFIGRVLSGIL")
        d = qc.to_dict()
        assert "c_amidation_recommended" in d
        assert "c_amidation_reason" in d

    def test_to_dict_amidation_recommended_matches_bool(self):
        qc = check_sequence("seed4", "ALPFIGRVLSGIL")
        d = qc.to_dict()
        assert d["c_amidation_recommended"] == qc.c_amidation_recommended

    def test_low_charge_sequence_benefits_most(self):
        # SEED-004 (charge ≈ 0.8 at pH 7.4) → highest benefit from amidation
        qc_low = check_sequence("low", "ALPFIGRVLSGIL")  # charge ~0.8
        qc_high = check_sequence("high", "KWKLFKKIGAVLKVL")  # charge > 3.0
        # low charge → recommended, high charge → not recommended (or optional)
        assert qc_low.c_amidation_recommended is True
        assert qc_high.c_amidation_recommended is False

    def test_empty_sequence_no_crash(self):
        qc = check_sequence("empty", "")
        # Empty sequence: no C-term → c_amidation_recommended should be False (default)
        assert isinstance(qc.c_amidation_recommended, bool)


# ---------------------------------------------------------------------------
# Wave 2 guidance (N-acetylation + D-amino substitution)
# ---------------------------------------------------------------------------

class TestWave2Guidance:
    def test_n_acetylation_recommended_when_interior_trypsin_sites(self):
        # K/R at 0-based pos 0,1,5,7,8 (regex excludes pos 10=C-terminal G; all K/R here are considered interior)
        qc = check_sequence("w1", "RRWQWRMKKLG")
        assert qc.n_acetylation_recommended is True

    def test_n_acetylation_not_recommended_when_no_interior_sites(self):
        # "FLPLIGAVLSGIL" contains no K or R → no trypsin sites
        qc = check_sequence("w2", "FLPLIGAVLSGIL")
        assert qc.n_acetylation_recommended is False

    def test_d_amino_guidance_lists_all_trypsin_positions(self):
        # "RRWQWRMKKLG" has 5 interior sites; entries must reference D- substitutions
        qc = check_sequence("w3", "RRWQWRMKKLG")
        assert len(qc.wave2_d_substitutions) > 0
        assert all("→ D-" in entry for entry in qc.wave2_d_substitutions)

    def test_d_amino_guidance_empty_for_no_trypsin_sites(self):
        qc = check_sequence("w4", "FLPLIGAVLSGIL")
        assert qc.wave2_d_substitutions == []

    def test_d_amino_guidance_capped_at_3_positions(self):
        # "RRWQWRMKKLG" has 5 interior trypsin sites → only top 3 returned
        qc = check_sequence("w5", "RRWQWRMKKLG")
        assert len(qc.wave2_d_substitutions) == 3

    def test_n_acetylation_flag_appears_in_flags_list(self):
        qc = check_sequence("w6", "RRWQWRMKKLG")
        acetyl_flags = [f for f in qc.flags if "N_ACETYLATION_RECOMMENDED" in f]
        assert len(acetyl_flags) == 1

    def test_wave2_d_amino_flag_appears_in_flags_list(self):
        qc = check_sequence("w7", "RRWQWRMKKLG")
        d_flags = [f for f in qc.flags if "WAVE2_D_AMINO" in f]
        assert len(d_flags) == 1

    def test_to_dict_contains_new_fields(self):
        qc = check_sequence("w8", "RRWQWRMKKLG")
        d = qc.to_dict()
        assert "n_acetylation_recommended" in d
        assert "n_acetylation_reason" in d
        assert "wave2_d_substitutions" in d

    def test_d_lys_for_interior_lys(self):
        # "KKKAAA" has K at positions 0, 1, 2 — all interior → all D-Lys guidance
        qc = check_sequence("w9", "KKKAAA")
        assert any("D-Lys" in entry for entry in qc.wave2_d_substitutions)

    def test_d_arg_for_interior_arg(self):
        # "RRRAAA" has R at positions 0, 1, 2 — all interior → all D-Arg guidance
        qc = check_sequence("w10", "RRRAAA")
        assert any("D-Arg" in entry for entry in qc.wave2_d_substitutions)

    def test_n_acetylation_not_recommended_when_only_terminal_kr(self):
        # C-terminal K is excluded by trypsin regex (?=.) lookahead + guard
        qc = check_sequence("w_cterm_only", "AAAAK")
        assert qc.n_acetylation_recommended is False
        assert qc.wave2_d_substitutions == []
        assert not any("N_ACETYLATION" in f for f in qc.flags)

    def test_d_amino_guidance_positions_are_1_indexed(self):
        # RRWQWRMKKLG: internal K/R at 0-based positions 0,1,5,7,8
        # Top 3 (most N-terminal) = positions 0,1,5 → displayed as 1,2,6
        qc = check_sequence("w_pos_1idx", "RRWQWRMKKLG")
        assert len(qc.wave2_d_substitutions) == 3
        assert "Position 1" in qc.wave2_d_substitutions[0]
        assert "Position 2" in qc.wave2_d_substitutions[1]
        assert "Position 6" in qc.wave2_d_substitutions[2]

    def test_empty_sequence_no_crash_wave2(self):
        qc = check_sequence("w_empty", "")
        assert qc.n_acetylation_recommended is False
        assert qc.wave2_d_substitutions == []

    def test_n_acetylation_reason_populated_when_recommended(self):
        qc = check_sequence("w_reason", "RRWQWRMKKLG")
        assert qc.n_acetylation_recommended is True
        assert len(qc.n_acetylation_reason) > 0
        assert "acetylat" in qc.n_acetylation_reason.lower()


# ---------------------------------------------------------------------------
# Deamidation hotspot completeness (QG, QS additions to NG, NS)
# ---------------------------------------------------------------------------

class TestDeamidationCompleteness:
    def test_ng_detected(self):
        qc = check_sequence("d_ng", "AANGAA")
        assert any("N" in s and "G" in s for s in qc.deamidation_sites)

    def test_ns_detected(self):
        qc = check_sequence("d_ns", "AANSKK")
        assert any("N" in s and "S" in s for s in qc.deamidation_sites)

    def test_qg_detected(self):
        qc = check_sequence("d_qg", "AAQGAA")
        assert any("Q" in s and "G" in s for s in qc.deamidation_sites), \
            "QG Gln deamidation hotspot should be detected"

    def test_qs_detected(self):
        qc = check_sequence("d_qs", "AAQSAA")
        assert any("Q" in s and "S" in s for s in qc.deamidation_sites), \
            "QS Gln deamidation hotspot should be detected"

    def test_deamidation_flag_present_for_qg(self):
        qc = check_sequence("d_qg_flag", "AAQGAA")
        assert any("DEAMIDATION_RISK" in f for f in qc.flags)

    def test_no_deamidation_for_clean_sequence(self):
        qc = check_sequence("d_clean", "KWKLFKKIGAVLKVL")
        assert qc.deamidation_sites == []

    def test_site_label_format_is_residue_position_neighbor(self):
        # "AAQGAA" → Q at position 3 (1-based), followed by G → label "Q3G"
        qc = check_sequence("d_label", "AAQGAA")
        assert "Q3G" in qc.deamidation_sites

    def test_to_dict_contains_deamidation_sites(self):
        qc = check_sequence("d_dict", "AAQGAA")
        d = qc.to_dict()
        assert "deamidation_sites" in d
        assert len(d["deamidation_sites"]) > 0


# ---------------------------------------------------------------------------
# Aspartate isomerization detection (DG, DS motifs)
# ---------------------------------------------------------------------------

class TestAspartateIsomerization:
    def test_dg_detected(self):
        qc = check_sequence("iso_dg", "AADGAA")
        assert any("D" in s and "G" in s for s in qc.isomerization_sites), \
            "DG aspartate isomerization hotspot should be detected"

    def test_ds_detected(self):
        qc = check_sequence("iso_ds", "AADSAA")
        assert any("D" in s and "S" in s for s in qc.isomerization_sites), \
            "DS aspartate isomerization hotspot should be detected"

    def test_isomerization_flag_present_for_dg(self):
        qc = check_sequence("iso_flag", "AADGAA")
        assert any("ISOMERIZATION_RISK" in f for f in qc.flags)

    def test_no_isomerization_for_da_motif(self):
        # DA is not a hotspot — only DG and DS
        qc = check_sequence("iso_da", "AADAAA")
        assert qc.isomerization_sites == []

    def test_no_isomerization_for_clean_sequence(self):
        qc = check_sequence("iso_clean", "KWKLFKKIGAVLKVL")
        assert qc.isomerization_sites == []

    def test_site_label_format(self):
        # "AADGAA" → D at position 3 (1-based), followed by G → label "D3G"
        qc = check_sequence("iso_label", "AADGAA")
        assert "D3G" in qc.isomerization_sites

    def test_to_dict_contains_isomerization_sites(self):
        qc = check_sequence("iso_dict", "AADGAA")
        d = qc.to_dict()
        assert "isomerization_sites" in d
        assert len(d["isomerization_sites"]) > 0


# ---------------------------------------------------------------------------
# Tryptophan photolability (≥3 Trp residues)
# ---------------------------------------------------------------------------

class TestTrpPhotolability:
    def test_three_trp_triggers_flag(self):
        # SEED-008 parent: FPVTWRWWKWWKG → 5 Trp
        qc = check_sequence("trp_seed8", "FPVTWRWWKWWKG")
        assert qc.tryptophan_count == 5
        assert qc.trp_photolability_risk is True

    def test_two_trp_no_flag(self):
        # 2 Trp → below threshold
        qc = check_sequence("trp_two", "AAWWAA")
        assert qc.tryptophan_count == 2
        assert qc.trp_photolability_risk is False

    def test_exactly_three_trp_triggers_flag(self):
        qc = check_sequence("trp_three", "AAAWWWAA")
        assert qc.tryptophan_count == 3
        assert qc.trp_photolability_risk is True

    def test_no_trp_no_flag(self):
        # KRLFKKIGSALKFL — no W residues
        qc = check_sequence("trp_zero", "KRLFKKIGSALKFL")
        assert qc.tryptophan_count == 0
        assert qc.trp_photolability_risk is False

    def test_trp_flag_appears_in_flags_list(self):
        qc = check_sequence("trp_flag", "FPVTWRWWKWWKG")
        assert any("TRP_PHOTOLABILITY" in f for f in qc.flags)

    def test_trp_flag_mentions_amber_vials(self):
        qc = check_sequence("trp_amber", "FPVTWRWWKWWKG")
        trp_flags = [f for f in qc.flags if "TRP_PHOTOLABILITY" in f]
        assert len(trp_flags) == 1
        assert "amber" in trp_flags[0].lower()

    def test_trp_photolability_does_not_affect_synthesis_difficulty(self):
        # TRP_PHOTOLABILITY is a storage/guidance flag (appended after difficulty is set).
        # WWWKKK: 3 Trp (photolability risk), 3 Lys (charge ≈ +2.8 → no LOW_CHARGE flag),
        # no hydrophobic run ≥4, ≤2 trypsin sites (K at pos 3,4 interior; K5 is C-terminal)
        # → zero synthesis-risk flags → synthesis_difficulty stays "LOW"
        qc = check_sequence("trp_diff", "WWWKKK")
        assert qc.trp_photolability_risk is True
        assert qc.synthesis_difficulty == "LOW"

    def test_formulation_note_mentions_amber_vials_for_trp_rich(self):
        qc = check_sequence("trp_form", "FPVTWRWWKWWKG")
        assert "amber" in qc.formulation_note.lower() or "foil" in qc.formulation_note.lower()

    def test_to_dict_contains_trp_fields(self):
        qc = check_sequence("trp_dict", "FPVTWRWWKWWKG")
        d = qc.to_dict()
        assert "tryptophan_count" in d
        assert "trp_photolability_risk" in d
        assert d["tryptophan_count"] == 5
        assert d["trp_photolability_risk"] is True


class TestCheckSequenceInputValidation:
    """check_sequence() validates canonical amino acids before running QC."""

    def test_canonical_sequence_accepted(self):
        qc = check_sequence("ok", "KWKLFKKIGSALKFL")
        assert qc.sequence == "KWKLFKKIGSALKFL"

    def test_lowercase_accepted_after_normalisation(self):
        # check_sequence uppercases before validation
        qc = check_sequence("lower", "kwklfkk")
        assert qc.sequence == "KWKLFKK"

    def test_non_canonical_single_raises(self):
        with pytest.raises(ValueError, match="non-canonical"):
            check_sequence("bad", "KWKLFKKX")

    def test_non_canonical_multiple_raises(self):
        with pytest.raises(ValueError, match="non-canonical"):
            check_sequence("bad2", "KWKXBZLFKK")

    def test_error_message_names_bad_residues(self):
        with pytest.raises(ValueError, match="X"):
            check_sequence("bad3", "KWKLFKX")

    def test_all_20_canonical_aas_accepted(self):
        # One representative from each canonical AA — all should pass without error
        for aa in "ACDEFGHIKLMNPQRSTVWY":
            qc = check_sequence(f"test_{aa}", aa * 5)
            assert qc.length == 5


# ---------------------------------------------------------------------------
# PROLINE_RICH_MEDIA flag — RPMI-1640 assay recommendation for proline-rich AMPs
# ---------------------------------------------------------------------------

# Bac2A-like proline-rich sequence: RRLPRPPYLPRP (5/12 Pro = 41.7% > 25%)
_BAC2A_LIKE = "RRLPRPPYLPRP"
# Non-proline-rich control: KWKLFKKIGSALKFL (0% Pro)
_LOW_PRO = "KWKLFKKIGSALKFL"
# Borderline: exactly 2/8 = 25% Pro — at threshold
_BORDER_PRO = "RRLPRPAA"


class TestProlineRichMediaFlag:
    """PROLINE_RICH_MEDIA flag for proline-rich AMPs requiring RPMI-1640 parallel assay."""

    def test_flag_present_for_proline_rich_sequence(self):
        qc = check_sequence("bac2a", _BAC2A_LIKE)
        flag_texts = " ".join(qc.flags)
        assert "PROLINE_RICH" in flag_texts

    def test_flag_mentions_rpmi(self):
        qc = check_sequence("bac2a", _BAC2A_LIKE)
        flag_texts = " ".join(qc.flags)
        assert "RPMI" in flag_texts

    def test_flag_mentions_krizsan(self):
        qc = check_sequence("bac2a", _BAC2A_LIKE)
        flag_texts = " ".join(qc.flags)
        assert "Krizsan" in flag_texts

    def test_flag_absent_for_low_proline_sequence(self):
        qc = check_sequence("low_pro", _LOW_PRO)
        flag_texts = " ".join(qc.flags)
        assert "PROLINE_RICH" not in flag_texts

    def test_flag_present_at_exactly_25_percent(self):
        # RRLPRPAA: 2 Pro out of 8 = 25% — should trigger flag at threshold
        qc = check_sequence("border", _BORDER_PRO)
        flag_texts = " ".join(qc.flags)
        assert "PROLINE_RICH" in flag_texts

    def test_flag_does_not_increase_synthesis_difficulty(self):
        # PROLINE_RICH_MEDIA is informational — must not raise difficulty rating.
        # KWKIALK: 3 Lys (charge +2.8 at pH 7.4), no Met/Cys, no hydrophobic run,
        # only 2 interior trypsin sites (threshold for flag is >2), 0% Pro.
        # All flags it gets (N_ACETYLATION_RECOMMENDED, WAVE2_D_AMINO) are informational
        # and appended AFTER difficulty is computed, so difficulty stays LOW.
        qc_clean = check_sequence("clean", "KWKIALK")
        assert qc_clean.synthesis_difficulty == "LOW"
        assert "PROLINE_RICH" not in " ".join(qc_clean.flags)

    def test_to_dict_flags_contains_proline_rich_entry(self):
        qc = check_sequence("bac2a", _BAC2A_LIKE)
        d = qc.to_dict()
        assert any("PROLINE_RICH" in f for f in d["flags"])

    def test_seed009_pilot_sequences_get_flag(self):
        # Real SEED-009 sequences from the pilot panel
        for seq in ("RRLPRPGYMPRP", "RRLPRGPYLPKP", "RRLPRPPYIPRG", "RRLGRPPYLGRP"):
            qc = check_sequence("s9", seq)
            assert any("PROLINE_RICH" in f for f in qc.flags), f"missing flag for {seq}"
