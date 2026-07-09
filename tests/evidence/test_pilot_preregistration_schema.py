"""Tests for pilot_preregistration.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"

PILOT_PREREG_SCHEMA = _SCHEMA_DIR / "pilot_preregistration.schema.json"


def _valid_preregistration() -> dict:
    return {
        "preregistration_id": "PPR-2026-07-09-001",
        "packet_id": "ERP-2026-07-09-001",
        "registered_at": "2026-07-09T12:00:00Z",
        "registered_by": "Dr. Jane Smith, Safety Lead",
        "assay_types": ["MIC", "hemolysis_RBC"],
        "pass_criteria": [
            {
                "metric": "MIC_50",
                "threshold": 16,
                "direction": "below",
            },
            {
                "metric": "HC50",
                "threshold": 100,
                "direction": "above",
            },
        ],
        "control_conditions": [
            "Melittin positive control (hemolytic)",
            "Vehicle-only negative control",
        ],
        "sample_size": 3,
        "blinding": True,
        "primary_endpoint": "MIC <= 16 ug/mL against MRSA USA300",
        "secondary_endpoints": [
            "Selectivity index (HC50/MIC) > 10",
            "Serum stability t1/2 > 4 hours",
        ],
        "statistical_analysis_plan": "MIC values will be log2-transformed and compared using one-way ANOVA with Dunnett's post-hoc test against the positive control. HC50 will be estimated by nonlinear regression.",
        "amendment_policy": "Any changes to pass_criteria require a documented amendment signed by the study lead and safety reviewer. Amendments must reference the original preregistration_id and include rationale.",
        "pipeline_version_locked": "v0.5.72",
    }


class TestPilotPreregistrationSchema:
    def test_schema_file_exists(self):
        assert PILOT_PREREG_SCHEMA.exists()

    def test_valid_preregistration_passes(self):
        validate_json_schema(_valid_preregistration(), PILOT_PREREG_SCHEMA)

    def test_missing_required_field_fails(self):
        p = {"preregistration_id": "PPR-001"}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_empty_assay_types_fails(self):
        p = _valid_preregistration()
        p["assay_types"] = []
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_empty_pass_criteria_fails(self):
        p = _valid_preregistration()
        p["pass_criteria"] = []
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_pass_criteria_missing_direction_fails(self):
        p = _valid_preregistration()
        p["pass_criteria"] = [{"metric": "MIC_50", "threshold": 16}]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_pass_criteria_invalid_direction_fails(self):
        p = _valid_preregistration()
        p["pass_criteria"] = [{"metric": "MIC_50", "threshold": 16, "direction": "greater"}]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_pass_criteria_equals_direction_passes(self):
        p = _valid_preregistration()
        p["pass_criteria"] = [{"metric": "replicates", "threshold": 3, "direction": "equals"}]
        validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_negative_sample_size_fails(self):
        p = _valid_preregistration()
        p["sample_size"] = 0
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_negative_sample_size_negative_fails(self):
        p = _valid_preregistration()
        p["sample_size"] = -1
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_empty_control_conditions_fails(self):
        p = _valid_preregistration()
        p["control_conditions"] = []
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_too_short_statistical_plan_fails(self):
        p = _valid_preregistration()
        p["statistical_analysis_plan"] = "Short plan."
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_blinding_non_bool_fails(self):
        p = _valid_preregistration()
        p["blinding"] = "yes"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(p, PILOT_PREREG_SCHEMA)

    def test_maximal_preregistration_passes(self):
        p = {
            "preregistration_id": "PPR-2026-07-09-002",
            "packet_id": "ERP-2026-07-09-002",
            "registered_at": "2026-07-09T14:00:00Z",
            "registered_by": "Dr. Alan Turing, External Review Board",
            "assay_types": ["MIC", "hemolysis_RBC", "serum_stability", "cytotoxicity_mammalian"],
            "pass_criteria": [
                {"metric": "MIC_50", "threshold": 32, "direction": "below", "notes": "Standard susceptibility breakpoint for MRSA"},
                {"metric": "HC50", "threshold": 200, "direction": "above", "notes": "Safety margin requirement"},
                {"metric": "serum_t1_2", "threshold": 4, "direction": "above"},
            ],
            "control_conditions": [
                "Melittin positive control (hemolytic)",
                "Vehicle-only negative control",
                "Vancomycin assay control",
            ],
            "sample_size": 6,
            "blinding": True,
            "primary_endpoint": "MIC <= 32 ug/mL against MRSA USA300 with HC50 > 200 ug/mL",
            "secondary_endpoints": [
                "Selectivity index (HC50/MIC) > 6.25",
                "Serum stability t1/2 > 4 hours",
                "Activity retention in RPMI-1640 medium",
            ],
            "statistical_analysis_plan": "Primary analysis: proportion of candidates meeting both MIC and HC50 criteria with 95% CI. Secondary: log2 MIC compared by ANOVA with Dunnett's test. Exploratory: ROC analysis of pipeline scores vs assay outcomes.",
            "amendment_policy": "Amendments require written approval from study lead and independent reviewer. Changes to primary endpoint require new preregistration. All amendments archived with original.",
            "pipeline_version_locked": "v0.5.72",
        }
        validate_json_schema(p, PILOT_PREREG_SCHEMA)
