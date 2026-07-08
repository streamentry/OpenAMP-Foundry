# Calibration Proposal Provenance Fields

Required provenance fields for calibration proposals.

## Required Fields
| Field | Description | Example |
|-------|-------------|---------|
| proposal_id | Unique identifier | CP-2026-07-001 |
| created_at | ISO 8601 timestamp | 2026-07-08T12:00:00Z |
| created_by | Human or agent name | Maintainer name |
| intake_report | Link to intake report | outputs/intake_report.json |
| gate_verdict | Link to gate verdict | outputs/gate_verdict.json |
| current_weights | Weights before change | {"activity": 0.40} |
| proposed_weights | Weights after change | {"activity": 0.42} |
| rationale | Why the change is needed | "Improve selectivity detection" |

## Rules
- All fields are required for a valid proposal.
- Proposals without complete provenance must not be applied.
- Provenance fields should be included in the weight proposal JSON.
