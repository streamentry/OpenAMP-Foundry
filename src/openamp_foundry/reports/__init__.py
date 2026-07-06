"""Report generators for OpenAMP Foundry.

Writes pilot panels, batch packs, external-predictor submissions,
external-predictor consensus, and lab-result review reports.
"""

from openamp_foundry.reports.batch_pack import (
    diversity_clustering_report,
    novelty_report,
    scorer_consensus_report,
    synthesis_feasibility_report,
    toxicity_hemolysis_risk_report,
)
from openamp_foundry.reports.external_consensus import (
    ConsensusResult,
    compute_consensus,
    consensus_report_to_dict,
    write_consensus_report,
)
from openamp_foundry.reports.external_predict import (
    write_confident_panel,
    write_external_predict_checklist,
    write_pilot_fasta,
)
from openamp_foundry.reports.lab_result_report import (
    build_lab_result_report,
    write_lab_result_json,
    write_lab_result_markdown,
)
from openamp_foundry.reports.pilot_panel import (
    write_pilot_csv,
    write_pilot_markdown,
)
from openamp_foundry.reports.recalibration_report import (
    build_recalibration_report,
    validate_recalibration_report,
    write_recalibration_report_json,
    write_recalibration_report_markdown,
)

__all__ = [
    # batch_pack
    "diversity_clustering_report",
    "novelty_report",
    "scorer_consensus_report",
    "synthesis_feasibility_report",
    "toxicity_hemolysis_risk_report",
    # external_consensus
    "ConsensusResult",
    "compute_consensus",
    "consensus_report_to_dict",
    "write_consensus_report",
    # external_predict
    "write_confident_panel",
    "write_external_predict_checklist",
    "write_pilot_fasta",
    # lab_result_report
    "build_lab_result_report",
    "write_lab_result_json",
    "write_lab_result_markdown",
    # pilot_panel
    "write_pilot_csv",
    "write_pilot_markdown",
    # recalibration_report
    "build_recalibration_report",
    "validate_recalibration_report",
    "write_recalibration_report_json",
    "write_recalibration_report_markdown",
]
