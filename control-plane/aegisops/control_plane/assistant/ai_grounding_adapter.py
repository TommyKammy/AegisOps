from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_NAME = "ai_grounding_adapter"
_TOOL_NAME = "evidence_grounding"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-63-7"
_REGISTRY_CITATIONS = (
    "docs/automation/ai-agent-registry.json",
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
    "docs/phase-51-6-authority-boundary-negative-test-policy.md",
    "docs/phase-59-4-ai-disabled-degraded-mode-contract.md",
    "docs/phase-63-5-evidence-freshness-provenance-projection.md",
)
_SUPPORTED_RECORD_FAMILIES = (
    "case",
    "evidence_request",
    "evidence",
    "source",
    "ai_trace",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "evidence_truth_creation",
    "release_truth",
    "readiness_truth",
    "workflow_truth",
)
_REQUIRED_CUSTODY_FIELDS = (
    "reviewed_file_hash",
    "enrichment_request_id",
    "collection_timestamp",
    "response_digest",
    "aegisops_evidence_record_id",
)
_REQUIRED_PROVENANCE_FIELDS = (
    "request_binding",
    "case_binding",
    "target_binding",
    "source_id",
    "enrichment_request_id",
    "collection_timestamp",
    "response_digest",
    "custody_reference",
    "authority_posture",
)
_REQUIRED_CONFIDENCE_FIELDS = (
    "posture",
    "freshness",
    "ambiguity_badge",
    "source_native_score_authority",
)
_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_evidence_context_only"
_NO_WORKFLOW_AUTHORITY = "none"
_ALLOWED_STATUS = frozenset({"available", "degraded", "unavailable"})
_ALLOWED_FRESHNESS = frozenset({"fresh", "stale"})
_ALLOWED_CONFLICT = frozenset({"none", "conflicting"})
_ALLOWED_SOURCE_STATE = frozenset({"available", "degraded", "unavailable"})
_ALLOWED_UNCERTAINTY = frozenset(
    {
        "related_entity_not_authoritative",
        "stale_review_required",
        "unresolved_conflict",
        "source_unavailable",
    }
)
_AUTHORITY_PRESSURE_TERMS = (
    "treat evidence as case truth",
    "evidence as case truth",
    "evidence as workflow truth",
    "evidence is authoritative",
    "promote evidence to truth",
    "approve the action",
    "execute the action",
    "reconcile the receipt",
    "close the case",
    "activate detectors",
    "activate detector",
    "create source truth",
    "create evidence truth",
)
_READINESS_PRESSURE_TERMS = (
    "mark this release ready",
    "mark release ready",
    "release ready",
    "readiness truth",
    "gate truth",
    "closeout truth",
    "production truth",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide citations",
    "hide citation",
    "suppress citations",
    "suppress citation",
    "hide uncertainty",
    "hide uncertainties",
    "suppress uncertainty",
    "hide stale",
    "suppress stale",
    "hide conflicts",
    "hide conflicting",
    "suppress conflicts",
)


def build_ai_grounding_adapter(
    *,
    grounding_context_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    validation = _validated_grounding_payload(grounding_context_payload)
    base = _base_payload(
        anchor_id=validation["anchor_id"],
        projections=validation["projections"],
    )
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)
    if validation["reasons"]:
        return _fallback_payload(
            base,
            mode="ai_grounding_untrusted",
            unresolved_reasons=validation["reasons"],
        )
    if ai_enablement_posture == "disabled":
        return _fallback_payload(
            base,
            mode="ai_disabled",
            unresolved_reasons=("ai_advisory_disabled",),
        )
    if ai_enablement_posture == "degraded":
        return _fallback_payload(
            base,
            mode="ai_degraded",
            unresolved_reasons=("ai_advisory_degraded",),
        )
    if ai_enablement_posture != "enabled":
        return _fallback_payload(
            base,
            mode="ai_enablement_untrusted",
            unresolved_reasons=("malformed_ai_enablement_posture",),
        )

    projections = validation["projections"]
    grounding_items = tuple(
        _grounding_item(projection)
        for projection in projections
    )
    uncertainty_flags = _uncertainty_flags(projections)
    unresolved_reasons = _unresolved_reasons(projections)
    return {
        **base,
        "decision": "ground",
        "mode": "phase63_evidence_grounding",
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": uncertainty_flags,
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_evidence_review_available": True,
        "grounding_items": grounding_items,
    }


def _base_payload(
    *,
    anchor_id: str | None = None,
    projections: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            *(("case:" + anchor_id,) if anchor_id is not None else ()),
            *(
                citation
                for projection in projections
                for citation in _string_tuple(projection.get("citation_ids"))
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": _SUPPORTED_RECORD_FAMILIES,
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "phase63_cited_evidence_grounding_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "approval_authority": False,
        "execution_authority": False,
        "reconciliation_authority": False,
        "case_closure_authority": False,
        "detector_activation_authority": False,
        "negative_authority": _NEGATIVE_AUTHORITY,
        "citations": citations,
    }


def _blocked_payload(
    base: Mapping[str, object],
    prompt_flags: tuple[str, ...],
) -> dict[str, object]:
    return {
        **base,
        "decision": "blocked",
        "mode": "prompt_pressure_blocked",
        "unresolved_reasons": prompt_flags,
        "uncertainty_flags": prompt_flags,
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_evidence_review_available": True,
        "grounding_items": (),
    }


def _fallback_payload(
    base: Mapping[str, object],
    *,
    mode: str,
    unresolved_reasons: tuple[str, ...],
) -> dict[str, object]:
    return {
        **base,
        "decision": "fallback",
        "mode": mode,
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": unresolved_reasons,
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_evidence_review_available": True,
        "grounding_items": (),
    }


def _validated_grounding_payload(
    grounding_context_payload: object,
) -> dict[str, object]:
    if not isinstance(grounding_context_payload, Mapping):
        return _invalid(("malformed_grounding_context_payload",))
    if grounding_context_payload.get("contract_version") != _CONTRACT_VERSION:
        return _invalid(("unsupported_ai_grounding_contract_version",))
    anchor = grounding_context_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return _invalid(("missing_review_anchor",))
    if anchor.get("direct_binding_required") is not True:
        return _invalid(("review_anchor_without_direct_binding",))
    anchor_family = _string(anchor.get("record_family"))
    anchor_id = _string(anchor.get("record_id"))
    if anchor_family != "case" or anchor_id is None:
        return _invalid(("unsupported_review_anchor",))

    raw_projections = grounding_context_payload.get("evidence_projections")
    if not isinstance(raw_projections, Sequence) or isinstance(
        raw_projections,
        (str, bytes),
    ):
        return _invalid(("malformed_evidence_projections",), anchor_id=anchor_id)
    if not raw_projections:
        return _invalid(("missing_grounding_projection",), anchor_id=anchor_id)

    reasons: list[str] = []
    projections: list[Mapping[str, object]] = []
    for raw_projection in raw_projections:
        if not isinstance(raw_projection, Mapping):
            reasons.append("malformed_evidence_projection")
            continue
        projection_reasons = _projection_reasons(raw_projection, anchor_id)
        reasons.extend(projection_reasons)
        if not projection_reasons:
            projections.append(raw_projection)

    return {
        "reasons": _dedupe_strings(tuple(reasons)),
        "anchor_id": anchor_id,
        "projections": tuple(projections),
    }


def _projection_reasons(
    projection: Mapping[str, object],
    anchor_id: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    case_id = _string(projection.get("case_id"))
    evidence_request_id = _string(projection.get("evidence_request_id"))
    source_id = _string(projection.get("source_id"))
    if projection.get("consumer") != "ai_grounding":
        reasons.append("unsupported_grounding_consumer")
    if case_id != anchor_id:
        reasons.append("grounding_not_bound_to_review_anchor")
    if evidence_request_id is None:
        reasons.append("missing_grounding_evidence_request_id")
    if source_id is None:
        reasons.append("missing_grounding_source_id")
    if projection.get("authoritative_workflow_truth") is not False:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("workflow_authority") != _NO_WORKFLOW_AUTHORITY:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("authority_posture") != _SUBORDINATE_AUTHORITY_POSTURE:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("status") not in _ALLOWED_STATUS:
        reasons.append("unsupported_grounding_status")
    if projection.get("freshness_state") not in _ALLOWED_FRESHNESS:
        reasons.append("unsupported_grounding_freshness")
    if projection.get("custody_state") != "complete":
        reasons.append("missing_grounding_custody")
    if projection.get("provenance_state") != "bound":
        reasons.append("missing_grounding_provenance")
    if projection.get("confidence_state") != "present":
        reasons.append("missing_grounding_confidence")
    if projection.get("conflict_state") not in _ALLOWED_CONFLICT:
        reasons.append("unsupported_grounding_conflict")
    if projection.get("source_state") not in _ALLOWED_SOURCE_STATE:
        reasons.append("unsupported_grounding_source_state")
    if projection.get("uncertainty_label") not in _ALLOWED_UNCERTAINTY:
        reasons.append("missing_grounding_uncertainty")
    custody = projection.get("custody")
    provenance = projection.get("provenance")
    confidence = projection.get("confidence")
    if not _mapping_has_non_empty_fields(custody, _REQUIRED_CUSTODY_FIELDS):
        reasons.append("missing_grounding_custody")
    if not _mapping_has_non_empty_fields(provenance, _REQUIRED_PROVENANCE_FIELDS):
        reasons.append("missing_grounding_provenance")
    if isinstance(custody, Mapping) and isinstance(provenance, Mapping):
        reasons.extend(
            _provenance_binding_reasons(
                provenance=provenance,
                custody=custody,
                projection=projection,
                anchor_id=anchor_id,
            )
        )
    if not _mapping_has_non_empty_fields(confidence, _REQUIRED_CONFIDENCE_FIELDS):
        reasons.append("missing_grounding_confidence")
    if isinstance(provenance, Mapping):
        if provenance.get("authority_posture") != _SUBORDINATE_AUTHORITY_POSTURE:
            reasons.append("grounding_authority_promotion_attempt")
    if isinstance(confidence, Mapping):
        if confidence.get("source_native_score_authority") != _NO_WORKFLOW_AUTHORITY:
            reasons.append("grounding_authority_promotion_attempt")
    reasons.extend(_citation_reasons(projection, anchor_id))
    return tuple(reasons)


def _provenance_binding_reasons(
    *,
    provenance: Mapping[str, object],
    custody: Mapping[str, object],
    projection: Mapping[str, object],
    anchor_id: str,
) -> tuple[str, ...]:
    expected_values = {
        "request_binding": _string(projection.get("evidence_request_id")),
        "case_binding": anchor_id,
        "target_binding": _string(custody.get("reviewed_file_hash")),
        "source_id": _string(projection.get("source_id")),
        "enrichment_request_id": _string(custody.get("enrichment_request_id")),
        "collection_timestamp": _string(custody.get("collection_timestamp")),
        "response_digest": _string(custody.get("response_digest")),
        "authority_posture": _SUBORDINATE_AUTHORITY_POSTURE,
    }
    for field_name, expected_value in expected_values.items():
        if expected_value is None:
            return ("grounding_provenance_binding_mismatch",)
        if _string(provenance.get(field_name)) != expected_value:
            return ("grounding_provenance_binding_mismatch",)
    return ()


def _citation_reasons(
    projection: Mapping[str, object],
    anchor_id: str,
) -> tuple[str, ...]:
    citation_ids = _string_tuple(projection.get("citation_ids"))
    if not citation_ids:
        return ("missing_required_grounding_citation",)
    evidence_request_id = _string(projection.get("evidence_request_id"))
    source_id = _string(projection.get("source_id"))
    custody = projection.get("custody")
    evidence_record_id = (
        _string(custody.get("aegisops_evidence_record_id"))
        if isinstance(custody, Mapping)
        else None
    )
    required = [
        "case:" + anchor_id,
        *(("evidence_request:" + evidence_request_id,) if evidence_request_id else ()),
        *(("source:" + source_id,) if source_id else ()),
        *(("evidence:" + evidence_record_id,) if evidence_record_id else ()),
    ]
    if any(citation not in citation_ids for citation in required):
        return ("missing_required_grounding_citation",)
    return ()


def _grounding_item(
    projection: Mapping[str, object],
) -> dict[str, object]:
    uncertainty_label = (
        _string(projection.get("uncertainty_label"))
        or "missing_grounding_uncertainty"
    )
    return {
        "evidence_request_id": projection.get("evidence_request_id"),
        "case_id": projection.get("case_id"),
        "source_id": projection.get("source_id"),
        "status": projection.get("status"),
        "freshness_state": projection.get("freshness_state"),
        "custody_state": projection.get("custody_state"),
        "provenance_state": projection.get("provenance_state"),
        "confidence_state": projection.get("confidence_state"),
        "conflict_state": projection.get("conflict_state"),
        "source_state": projection.get("source_state"),
        "uncertainty_label": uncertainty_label,
        "uncertainty_required": uncertainty_label != "related_entity_not_authoritative",
        "citation_ids": _string_tuple(projection.get("citation_ids")),
        "advisory_only": True,
        "counts_as_workflow_truth": False,
        "can_approve_action": False,
        "can_execute_action": False,
        "can_reconcile": False,
        "can_close_case": False,
        "can_activate_detector": False,
    }


def _uncertainty_flags(
    projections: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return _dedupe_strings(
        tuple(
            label
            for projection in projections
            if (label := _string(projection.get("uncertainty_label"))) is not None
        )
    )


def _unresolved_reasons(
    projections: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for projection in projections:
        if projection.get("freshness_state") == "stale":
            reasons.append("stale_evidence")
        if projection.get("conflict_state") == "conflicting":
            reasons.append("conflicting_evidence")
        if (
            projection.get("status") == "unavailable"
            or projection.get("source_state") == "unavailable"
        ):
            reasons.append("unavailable_evidence_source")
        if projection.get("uncertainty_label") != "related_entity_not_authoritative":
            reasons.append("uncertainty_required")
    return _dedupe_strings(tuple(reasons))


def _prompt_pressure_flags(prompt_text: object) -> tuple[str, ...]:
    flags = list(_advisory_text_claims_authority_or_scope_expansion(prompt_text))
    flags.extend(phase24_live_assistant_prompt_injection_flags(prompt_text))
    if not isinstance(prompt_text, str):
        return _dedupe_strings(tuple(flags))
    if _contains_any_term(prompt_text, _UNCERTAINTY_SUPPRESSION_TERMS):
        flags.append("citation_suppression_attempt")
    if _contains_any_term(prompt_text, _AUTHORITY_PRESSURE_TERMS):
        flags.append("authority_overreach")
    if _contains_any_term(prompt_text, _READINESS_PRESSURE_TERMS):
        flags.append("readiness_truth_attempt")
    return _dedupe_strings(tuple(flags))


def _contains_any_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = re.sub(r"[\W_]+", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for term in terms:
        normalized_term = re.sub(r"[\W_]+", " ", term.lower()).strip()
        pattern = rf"(?<!\w){re.escape(normalized_term)}(?!\w)"
        if re.search(pattern, normalized) is not None:
            return True
    return False


def _invalid(
    reasons: tuple[str, ...],
    *,
    anchor_id: str | None = None,
) -> dict[str, object]:
    return {
        "reasons": reasons,
        "anchor_id": anchor_id,
        "projections": (),
    }


def _mapping_has_non_empty_fields(
    value: object,
    required_fields: tuple[str, ...],
) -> bool:
    if not isinstance(value, Mapping):
        return False
    return all(
        isinstance(value.get(field_name), str) and bool(str(value[field_name]).strip())
        for field_name in required_fields
    )


def _string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        normalized_item = _string(item)
        if normalized_item is not None and normalized_item not in normalized:
            normalized.append(normalized_item)
    return tuple(normalized)


def _dedupe_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in deduped:
            deduped.append(value)
    return tuple(deduped)
