"""JSON-LD context generation for OpenAMP evidence certificates."""

from __future__ import annotations

from dataclasses import dataclass, field

JSONLD_CONTEXT_ID_PREFIX = "JLC-"

JSONLD_CONTEXT_VERSION = "1.0"

OPENAMP_NAMESPACE = "https://openamp-foundry.org/ns/v1#"

SCHEMA_ORG_NAMESPACE = "https://schema.org/"

VALID_EVIDENCE_TYPES: frozenset = frozenset(
    {
        "EvidenceCertificate",
        "BatchOutcomeSummary",
        "NegativeResultRecord",
        "BenchmarkCard",
        "ExternalReviewPacket",
        "ReleaseManifest",
        "CalibrationCycleSummary",
    }
)

VALID_PROOF_LADDER_LEVELS: frozenset = frozenset(
    {
        "dry_lab_candidate",
        "multi_signal_candidate_evidence",
        "expert_reviewed_assay_proposal",
        "validated_assay_result",
        "independently_replicated",
    }
)

REQUIRED_CERTIFICATE_FIELDS: frozenset = frozenset(
    {
        "certificate_id",
        "candidate_id",
        "proof_ladder_level",
        "dry_lab_only",
        "created_at",
    }
)

JSONLD_BASE_CONTEXT: dict = {
    "@vocab": OPENAMP_NAMESPACE,
    "schema": SCHEMA_ORG_NAMESPACE,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "certificate_id": {"@id": "openamp:certificateId"},
    "candidate_id": {"@id": "openamp:candidateId"},
    "proof_ladder_level": {"@id": "openamp:proofLadderLevel"},
    "dry_lab_only": {"@id": "openamp:dryLabOnly", "@type": "xsd:boolean"},
    "created_at": {"@id": "schema:dateCreated"},
    "pipeline_version": {"@id": "openamp:pipelineVersion"},
    "run_id": {"@id": "openamp:runId"},
    "unsupported_claims": {"@id": "openamp:unsupportedClaims"},
    "baseline_caveat": {"@id": "openamp:baselineCaveat"},
    "selection_rationale": {"@id": "openamp:selectionRationale"},
    "failure_modes": {"@id": "openamp:failureModes"},
    "human_review_required": {
        "@id": "openamp:humanReviewRequired",
        "@type": "xsd:boolean",
    },
    "release_status": {"@id": "openamp:releaseStatus"},
    "batch_id": {"@id": "openamp:batchId"},
    "evidence_type": {"@id": "@type"},
}


@dataclass
class JsonLdContextRecord:
    context_id: str
    context_version: str
    evidence_type: str
    context_document: dict = field(default_factory=dict)
    namespace: str = OPENAMP_NAMESPACE
    is_dry_lab_constrained: bool = True
    generation_note: str = ""


@dataclass
class JsonLdContextValidationResult:
    is_valid: bool
    violations: list = field(default_factory=list)


def build_jsonld_context_record(
    context_id: str,
    evidence_type: str,
    context_version: str = JSONLD_CONTEXT_VERSION,
    extra_terms: dict | None = None,
    generation_note: str = "",
) -> JsonLdContextRecord:
    context_doc = dict(JSONLD_BASE_CONTEXT)
    if extra_terms:
        context_doc.update(extra_terms)
    return JsonLdContextRecord(
        context_id=context_id,
        context_version=context_version,
        evidence_type=evidence_type,
        context_document=context_doc,
        namespace=OPENAMP_NAMESPACE,
        is_dry_lab_constrained=True,
        generation_note=generation_note or f"Auto-generated context for {evidence_type}",
    )


def validate_jsonld_context_record(
    record: JsonLdContextRecord,
) -> JsonLdContextValidationResult:
    violations: list[str] = []

    if not record.context_id.startswith(JSONLD_CONTEXT_ID_PREFIX):
        violations.append(
            f"context_id must start with '{JSONLD_CONTEXT_ID_PREFIX}', got '{record.context_id}'"
        )

    if record.evidence_type not in VALID_EVIDENCE_TYPES:
        violations.append(
            f"evidence_type '{record.evidence_type}' not in VALID_EVIDENCE_TYPES"
        )

    if not record.context_version:
        violations.append("context_version must not be empty")

    if "@vocab" not in record.context_document:
        violations.append("context_document must contain '@vocab' key")

    if record.namespace != OPENAMP_NAMESPACE:
        violations.append(
            f"namespace must be '{OPENAMP_NAMESPACE}', got '{record.namespace}'"
        )

    missing_required = REQUIRED_CERTIFICATE_FIELDS - set(record.context_document.keys())
    if missing_required:
        violations.append(
            f"context_document missing required certificate fields: {sorted(missing_required)}"
        )

    if not record.is_dry_lab_constrained:
        violations.append(
            "is_dry_lab_constrained must be True; wet-lab contexts require human review"
        )

    if not record.generation_note:
        violations.append("generation_note must not be empty")

    return JsonLdContextValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def format_jsonld_context_record(record: JsonLdContextRecord) -> str:
    import json

    doc = {
        "@context": record.context_document,
        "_meta": {
            "context_id": record.context_id,
            "context_version": record.context_version,
            "evidence_type": record.evidence_type,
            "namespace": record.namespace,
            "is_dry_lab_constrained": record.is_dry_lab_constrained,
            "generation_note": record.generation_note,
        },
    }
    return json.dumps(doc, indent=2, sort_keys=False)


def annotate_certificate_with_context(
    certificate_dict: dict,
    context_record: JsonLdContextRecord,
) -> dict:
    annotated = dict(certificate_dict)
    annotated["@context"] = context_record.context_document
    annotated["@type"] = context_record.evidence_type
    return annotated
