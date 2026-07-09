# Downstream Project Template

## Overview

OpenAMP Foundry produces **computational (dry-lab) artifacts** for antimicrobial
peptide candidate selection. These artifacts are **hypotheses and review aids
— not biological proof**.

Available artifact types:

- **Candidate manifests** — structured descriptions of dry-lab candidates
  (sequence, scores, evidence level, safety flags, provenance)
- **Benchmark cards** — standard format for benchmark results with baseline
  comparison
- **Evidence certificates** — proof-ladder-level bounded claims with caveats
- **Simulation results** — virtual-assay module outputs with uncertainty
- **Artifact changelog** — version history for all artifact types

All artifacts carry `dry_lab_only: true`. They must never be presented as
validated biological findings without independent wet-lab confirmation.

---

## Minimum Viable Integration

The simplest way to consume OpenAMP artifacts is to read a candidate manifest,
validate it, and use the evidence level and scores for downstream decisions.

### Step 1: Consume a Candidate Manifest

Candidate manifests are produced by the OpenAMP pipeline (JSON format):

```json
{
  "candidate_id": "AMP-001",
  "sequence": "AKLWKR",
  "evidence_level": 2,
  "scopes": ["bacterial_binding"],
  "scores": {"binding_energy": 0.75},
  "uncertainty": 0.1,
  "source_modules": ["membrane_proxy"],
  "calibration_set": null,
  "safety_flags": [],
  "provenance_run_id": null,
  "dry_lab_only": true,
  "version": "1.0.0",
  "created_at": "2026-07-09T00:00:00Z",
  "notes": []
}
```

Required fields: `candidate_id`, `sequence`, `evidence_level`, `scopes`,
`scores`, `uncertainty`, `source_modules`, `calibration_set`, `safety_flags`,
`provenance_run_id`, `dry_lab_only`, `version`, `created_at`, `notes`.

### Step 2: Validate Against the Schema

```python
import json
from openamp_foundry.evidence.schemas import validate_json_schema

with open("candidate_manifest.schema.json") as f:
    schema = json.load(f)

with open("manifest.json") as f:
    manifest = json.load(f)

errors = validate_json_schema(manifest, schema)
if errors:
    raise ValueError(f"Manifest validation failed: {errors}")
```

The canonical schema is at `schemas/candidate_manifest.schema.json` in the
OpenAMP repository.

### Step 3: Use the Python Library (Optional)

```python
from openamp_foundry.manifests.candidate_manifest import (
    CandidateManifest,
    validate_candidate_manifest,
)

manifest = CandidateManifest(
    candidate_id="AMP-001",
    sequence="AKLWKR",
    evidence_level=2,
    scopes=["bacterial_binding"],
    scores={"binding_energy": 0.75},
    uncertainty=0.1,
    source_modules=["membrane_proxy"],
    calibration_set=None,
    safety_flags=[],
    provenance_run_id=None,
)

errors = validate_candidate_manifest(manifest)
assert not errors, errors
```

### Step 4: Run the Integration Checker

```bash
pip install openamp-foundry
openamp-foundry integration-check \
  --manifest-json '{"candidate_id":"AMP-001","sequence":"AKLWKR",...}'
```

The integration checker validates all required fields, evidence level range,
safety flag conventions, dry-lab acknowledgment, and baseline comparison.

---

## Schema Validation

Every OpenAMP artifact type has a corresponding JSON Schema in the `schemas/`
directory:

| Artifact | Schema |
|---|---|
| Candidate manifest | `schemas/candidate_manifest.schema.json` |
| Benchmark card | `schemas/benchmark_card.schema.json` |
| Simulation result | `schemas/simulation_result.schema.json` |
| Simulation module registry | `schemas/simulation_module_registry.schema.json` |

Validate any artifact against its schema using:

```python
from openamp_foundry.evidence.schemas import validate_json_schema
import json

with open("schemas/candidate_manifest.schema.json") as f:
    schema = json.load(f)
with open("my_manifest.json") as f:
    data = json.load(f)

errors = validate_json_schema(data, schema)
```

All schemas use JSON Schema Draft 2020-12 with `additionalProperties: false`.

---

## Evidence Level Interpretation

| Level | Label | Meaning | Caveat |
|---|---|---|---|
| **L1** | Computational nomination | ML/heuristic score above threshold | No biological testing |
| **L2** | Virtual-assay support | Simulation or proxy-model agreement | Proxy models are not validated biology |
| **L3** | In-silico ensemble agreement | Multiple independent scorers agree | Agreement is consistency, not proof |
| **L4** | Ex-vivo preliminary | Preliminary non-human assay data | Small sample, non-standard assay |
| **L5** | In-vivo preliminary | Animal model data | Not human data |
| **L6** | Clinical evidence | Human clinical data | Requires full clinical review |

**Rule:** Dry-lab scores (L1-L3) do not prove biological activity. L4-L6
require wet-lab or clinical evidence.

---

## Safety Flag Conventions

Safety flags are string identifiers attached to a candidate manifest:

| Flag | Meaning | Suggested Action |
|---|---|---|
| `hemolytic_risk` | Predicted hemolytic (HC50 < 25 µg/mL) | Flag for selectivity review |
| `cytotoxic_risk` | Predicted cytotoxic (low CC50) | Flag for counterscreen |
| `aggregation_risk` | Predicted aggregation-prone | Flag for formulation review |
| `oxidation_risk` | Contains oxidation-prone residues (M, W, C) | Flag for synthesis planning |
| `proteolytic_risk` | Predicted protease-sensitive | Flag for stability review |
| `dual_use_concern` | Sequence matches known toxins | Escalate for safety review |

An empty safety flags list (`[]`) means no flags were raised by the pipeline.
It does not guarantee biological safety — only that automated checks passed.

**Downstream consumers must review safety flags before any wet-lab or
release decision.**

---

## Benchmark Card Consumption

Benchmark cards describe how a method performed relative to a baseline:

```json
{
  "benchmark_id": "bench-auroc-001",
  "benchmark_name": "AMP vs Decoy AUROC",
  "metric": "AUROC",
  "metric_value": 0.82,
  "baseline_name": "random",
  "baseline_value": 0.50,
  "delta": 0.32,
  "beats_baseline": true,
  "dataset": "APD3",
  "dataset_size": 500,
  "scope": ["bacterial"],
  "caveats": ["charge-inflated benchmark"],
  "dry_lab_only": true
}
```

### How to Compare Against Baselines

1. **Check `caveats`** first — they describe known limitations.
2. **Compare `metric_value` to `baseline_value`:** `delta > 0` and
   `beats_baseline = true` means the method outperforms its baseline.
3. **Check the `scope`:** benchmark results are scope-specific.
4. **Evaluate `dataset_size`:** small benchmarks have wider confidence
   intervals.

```python
from openamp_foundry.benchmarks.benchmark_card import BenchmarkCard

card = BenchmarkCard(
    benchmark_id="bench-auroc-001",
    benchmark_name="AMP vs Decoy AUROC",
    version="1.0.0",
    date="2026-07-09",
    metric="AUROC",
    metric_value=0.82,
    baseline_name="random",
    baseline_value=0.50,
    delta=0.32,
    beats_baseline=True,
    dataset="APD3",
    dataset_size=500,
    scope=["bacterial"],
    caveats=["charge-inflated benchmark"],
)

print(f"Beats baseline: {card.beats_baseline} (delta={card.delta:+.4f})")
```

---

## Dry-Lab Limitations

**All OpenAMP artifacts are computational and dry-lab only.** They constitute:

- Hypotheses for expert review
- Computational evidence packages for candidate triage
- Structured metadata for pipeline reproducibility

They do **not** constitute:

- Biological proof of antimicrobial activity
- Safety or toxicity validation
- Clinical efficacy evidence
- Regulatory submission data
- A substitute for wet-lab or clinical testing

**No computational prediction, regardless of score or evidence level, should
be treated as biological validation without independent wet-lab confirmation.**

The `dry_lab_only: true` field is a safety constraint on every artifact.
Downstream projects must preserve this field and its semantics.

---

## Contact and Contribution

- **Repository:** https://github.com/anomalyco/openamp-foundry
- **Issues:** Bug reports, feature requests, adoption questions
- **Discussions:** Integration patterns, schema questions, use cases

To contribute integration examples or report issues with this template,
open a GitHub issue or pull request.

---

*This template is a dry-lab integration guide. It does not contain biological
instructions, assay protocols, or safety procedures requiring qualified
human review.*
