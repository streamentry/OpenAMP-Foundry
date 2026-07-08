# Adapter Capability Matrix

Capabilities of external adapters and simulation modules.

| Module | Type | Status | Requires Network | Calibration Data |
|--------|------|:------:|:----------------:|:----------------:|
| MembraneProxy | simulation | experimental | No | None |
| StructureProxy | simulation | experimental | No | None |
| ExternalSimulationAdapter | adapter | available | Depends | None |

## Rules
- Experimental modules must not affect candidate ranking.
- Adapters requiring network must document this.
- Calibration data must be referenced when available.
- Modules without calibration data are informational only.
