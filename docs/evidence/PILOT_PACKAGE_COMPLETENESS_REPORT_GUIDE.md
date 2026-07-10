# Pilot Package Completeness Report Guide (PPC-)

## Purpose

A `PilotPackageCompletenessReport` (PPC-) is the auditable completeness gate for a
`PilotEvidencePackage` (PEP-). It confirms that all five required component IDs are
present and that an External Sharing Clearance (ESC-) exists before the package is
shared with an external lab.

Without a PPC-, a PEP could leave the foundry with missing components. A valid PPC-
means the completeness check was explicitly passed and recorded.

## Required Components

A complete pilot package requires:

| Component | Prefix | Description |
|-----------|--------|-------------|
| Calibration Cycle Summary | `CCS-` | Confirms calibration gate passed |
| Batch Selection Proposal | `BSP-` | Documents how candidates were selected |
| Pilot Safety Clearance | `PSC-` | Safety gate before synthesis |
| Pre-Registration Entry | `PRE-` | Hypothesis locked before wet-lab |
| Baseline Comparison Manifest | `BCM-` | Proves model beats cheap baselines |

An External Sharing Clearance (`ESC-`) must also exist, confirming the package
was cleared for release.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ppc_id` | str | Yes | Unique ID, must start with `PPC-` |
| `pipeline_version` | str | Yes | Version of pipeline that ran the check |
| `pep_id` | str | Yes | The PEP being checked (must start with `PEP-`) |
| `esc_id` | str | Yes | External sharing clearance (must start with `ESC-`) |
| `ccs_id` | str | Yes | Calibration cycle summary (must start with `CCS-`) |
| `bsp_id` | str | Yes | Batch selection proposal (must start with `BSP-`) |
| `psc_id` | str | Yes | Pilot safety clearance (must start with `PSC-`) |
| `pre_id` | str | Yes | Pre-registration entry (must start with `PRE-`) |
| `bcm_id` | str | Yes | Baseline comparison manifest (must start with `BCM-`) |
| `checked_date` | str | Yes | ISO date (YYYY-MM-DD) of completeness check |
| `completeness_confirmed` | bool | Yes | Must be `True`; do not record unless complete |
| `notes` | str | No | Reviewer context (≤300 chars) |

## Validation Rules

1. `ppc_id` must start with `PPC-`
2. `pipeline_version` must be non-empty
3. `pep_id` must start with `PEP-`
4. `esc_id` must start with `ESC-`
5. `ccs_id` must start with `CCS-`
6. `bsp_id` must start with `BSP-`
7. `psc_id` must start with `PSC-`
8. `pre_id` must start with `PRE-`
9. `bcm_id` must start with `BCM-`
10. `checked_date` must match `YYYY-MM-DD`
11. `completeness_confirmed` must be `True`
12. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `notes` is empty | No reviewer context recorded |
| Two or more component IDs are identical | Each component should have a unique ID |
| `pep_id` appears in a component ID slot | PEP- IDs should not be reused as component IDs |

## Boundaries

- **PPC- records completeness, not quality.** A complete package may still have scientific limitations; completeness only means all components are present.
- **`completeness_confirmed` must be True.** Do not record a PPC- unless the package genuinely passes. Incomplete packages do not get a PPC-.
- **PPC- is not a release approval.** An ESC- (External Sharing Clearance) is still required separately. PPC- verifies components; ESC- records who received the package and when.

## CLI

```bash
openamp-foundry pilot-package-completeness-check '{"ppc_id": "PPC-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
PEP-  ──→  PPC-  (completeness gate for the PEP bundle)
ESC-  ──→  PPC-  (ESC- confirms external sharing cleared)
CCS-  ──→  PPC-  (calibration gate passed)
BSP-  ──→  PPC-  (batch selection documented)
PSC-  ──→  PPC-  (safety clearance on record)
PRE-  ──→  PPC-  (pre-registration locked)
BCM-  ──→  PPC-  (baseline comparison confirmed)
```

PPC- is the final internal gate before an external lab receives a package.
