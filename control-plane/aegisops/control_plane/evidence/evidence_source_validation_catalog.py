from __future__ import annotations

import re

from .evidence_source_registry_data import EvidenceSourceEntry


def _normalize_boundary_text(value: str) -> str:
    split_camel_case = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", split_camel_case.lower()).strip()


def _match_normalized_term_at(
    tokens: tuple[str, ...],
    start: int,
    term_tokens: tuple[str, ...],
) -> int | None:
    term_text = "".join(term_tokens)
    if not term_text:
        return None
    assembled_text = ""
    token_index = start
    while token_index < len(tokens) and len(assembled_text) < len(term_text):
        assembled_text += tokens[token_index]
        token_index += 1
    if assembled_text != term_text:
        return None
    return token_index


def _normalized_term_spans(
    tokens: tuple[str, ...],
    term_tokens: tuple[str, ...],
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    for start in range(len(tokens)):
        end = _match_normalized_term_at(tokens, start, term_tokens)
        if end is not None:
            spans.append((start, end))
    return tuple(spans)


def _has_normalized_boundary_term(value: str, terms: tuple[str, ...]) -> bool:
    tokens = tuple(_normalize_boundary_text(value).split())
    return any(
        _normalized_term_spans(tokens, tuple(term.split()))
        for term in terms
    )


_PROHIBITED_RECORD_TRUTH_CLAIMS = (
    "alert_truth",
    "alert truths",
    "case_truth",
    "case truths",
    "source_truth",
    "source truths",
    "source of truth",
    "sources of truth",
    "evidence_truth",
    "evidence truths",
    "evidence_request_truth",
    "evidence request truths",
    "audit_truth",
    "audit truths",
)
_PROHIBITED_ACTION_TRUTH_CLAIMS = (
    "approval_truth",
    "approval truths",
    "action_request_truth",
    "action request truths",
    "receipt_truth",
    "receipt truths",
    "execution_receipt_truth",
    "execution receipt truths",
    "execution_truth",
    "execution truths",
    "reconciliation_truth",
    "reconciliation truths",
    "detector_activation_truth",
    "detector activation truths",
)
_READINESS_TRUTH_CLAIM = "readiness_truth"
_PROHIBITED_CLOSEOUT_TRUTH_CLAIMS = (
    "release_truth",
    "release truths",
    "release_gate_truth",
    "release gate truths",
    "gate_truth",
    "gate truths",
    "limitation_truth",
    "limitation truths",
    "closeout_truth",
    "closeout truths",
    "closeout_state_truth",
    "closeout state truths",
    _READINESS_TRUTH_CLAIM,
    "readiness truths",
)
_PROHIBITED_ENVIRONMENT_TRUTH_CLAIMS = (
    "production_truth",
    "production truths",
)
_PROHIBITED_WORKFLOW_TRUTH_CLAIMS = (
    *_PROHIBITED_RECORD_TRUTH_CLAIMS,
    *_PROHIBITED_ACTION_TRUTH_CLAIMS,
    *_PROHIBITED_CLOSEOUT_TRUTH_CLAIMS,
)
_DETECTOR_ACTIVATION_AUTHORITY_TERMS = (
    "activate detector",
    "activate detectors",
    "activate a detector",
    "activate the detector",
    "activates detector",
    "activates detectors",
    "activates a detector",
    "activates the detector",
    "activated detector",
    "activated detectors",
    "activated a detector",
    "activated the detector",
    "activating detector",
    "activating detectors",
    "activating a detector",
    "activating the detector",
    "detector activation",
    "detector activations",
    "detector activated",
    "detectors activated",
)
_ALERT_ADMISSION_AUTHORITY_TERMS = (
    "admitted alert",
    "admitted alerts",
    "admitted an alert",
    "admitted the alert",
    "admit alert",
    "admit alerts",
    "admit an alert",
    "admit the alert",
    "admits alert",
    "admits alerts",
    "admits an alert",
    "admits the alert",
    "admitting alert",
    "admitting alerts",
    "admitting an alert",
    "admitting the alert",
    "alert admission",
)
_REQUEST_AUTHORITY_TERMS = (
    "evidence request",
    "evidence requests",
    "action request",
    "action requests",
)
_APPROVAL_AUTHORITY_TERMS = (
    "approval",
    "approvals",
    "approved",
    "approves",
    "approve",
    "approving",
)
_EXECUTION_AUTHORITY_TERMS = (
    "executed",
    "execute",
    "executes",
    "executing",
)
_RECONCILIATION_AUTHORITY_TERMS = (
    "reconciled",
    "reconcile",
    "reconciles",
    "reconciling",
    "reconciliation owner",
    "reconciliation owners",
    "reconciliation ownership",
)
_CLOSURE_AUTHORITY_TERMS = (
    "closed",
    "close",
    "closes",
    "closing",
)
_RECORD_OWNER_AUTHORITY_TERMS = (
    "alert owner",
    "alert owners",
    "alert ownership",
    "case owner",
    "case owners",
    "case ownership",
    "evidence owner",
    "evidence owners",
    "evidence ownership",
    "approval owner",
    "approval owners",
    "approval ownership",
    "action request owner",
    "action request owners",
    "action request ownership",
    "execution receipt owner",
    "execution receipt owners",
    "execution receipt ownership",
    "audit owner",
    "audit owners",
    "audit ownership",
    "release owner",
    "release owners",
    "release ownership",
    "gate owner",
    "gate owners",
    "gate ownership",
    "closeout owner",
    "closeout owners",
    "closeout ownership",
)
_RECORD_SPECIFIC_AUTHORITY_TERMS = (
    "alert authority",
    "alert authorities",
    "case authority",
    "case authorities",
    "source authority",
    "source authorities",
    "evidence authority",
    "evidence authorities",
    "audit authority",
    "audit authorities",
    "approval authority",
    "approval authorities",
    "action request authority",
    "action request authorities",
    "execution receipt authority",
    "execution receipt authorities",
    "execution authority",
    "execution authorities",
    "reconciliation authority",
    "reconciliation authorities",
    "release authority",
    "release authorities",
    "release gate authority",
    "release gate authorities",
    "gate authority",
    "gate authorities",
    "limitation authority",
    "limitation authorities",
    "closeout authority",
    "closeout authorities",
    "readiness authority",
    "readiness authorities",
    "production authority",
    "production authorities",
)
_AUTHORITY_WIDENING_TERMS = (
    "authoritative",
    "workflow authority",
    "workflow authorities",
    "workflow truth",
    "workflow truths",
    *_ALERT_ADMISSION_AUTHORITY_TERMS,
    *_REQUEST_AUTHORITY_TERMS,
    *_APPROVAL_AUTHORITY_TERMS,
    *_EXECUTION_AUTHORITY_TERMS,
    *_RECONCILIATION_AUTHORITY_TERMS,
    *_CLOSURE_AUTHORITY_TERMS,
    *_DETECTOR_ACTIVATION_AUTHORITY_TERMS,
    *_RECORD_OWNER_AUTHORITY_TERMS,
    *_RECORD_SPECIFIC_AUTHORITY_TERMS,
    "execution receipt",
    "execution receipts",
    "release gate",
    "release gates",
    "gate release",
    "gate releases",
    "limitation",
    "limitations",
    "closeout state",
    "claim readiness",
    "claims readiness",
    "claimed readiness",
    "claiming readiness",
    "readiness claim",
    "readiness claims",
    "readiness claimed",
    "close cases",
    "case closure",
    *_PROHIBITED_WORKFLOW_TRUTH_CLAIMS,
    *_PROHIBITED_ENVIRONMENT_TRUTH_CLAIMS,
)
_NORMALIZED_AUTHORITY_WIDENING_TERMS = tuple(
    _normalize_boundary_text(term) for term in _AUTHORITY_WIDENING_TERMS
)
_DEFERRED_EVIDENCE_SOURCE_TERMS = (
    "Velociraptor",
    "YARA",
    "capa",
    "MISP",
    "Suricata",
    "IntelOwl",
)
_BROAD_OR_DEFAULT_SOURCE_TERMS = (
    *_DEFERRED_EVIDENCE_SOURCE_TERMS,
    "default evidence source list",
    "default evidence source lists",
    "evidence source marketplace",
    "evidence source marketplaces",
    "public internet pivot",
    "public internet pivots",
)
_NORMALIZED_BROAD_OR_DEFAULT_SOURCE_TERMS = tuple(
    _normalize_boundary_text(term) for term in _BROAD_OR_DEFAULT_SOURCE_TERMS
)
_NORMALIZED_BROAD_SOURCE_ALIASES = tuple(
    alias
    for alias in (
        "m i s p",
        "y a r a",
        "c a p a",
        "intel owl",
    )
)
_AUTHORITY_FIELD_ERROR_CODES = {
    "source_id": "source_id_promotes_workflow_authority",
    "source_type": "source_type_promotes_workflow_authority",
    "owner": "owner_promotes_workflow_authority",
    "allowed_target_class": "allowed_target_class_promotes_workflow_authority",
    "custody_requirements": "custody_requirements_promote_workflow_authority",
    "freshness_window": "freshness_window_promotes_workflow_authority",
    "confidence_posture": "confidence_posture_promotes_workflow_authority",
    "status": "status_promotes_workflow_authority",
    "authority_posture": "authority_posture_promotes_workflow_authority",
    "degraded_states": "degraded_states_promotes_workflow_authority",
    "disabled_states": "disabled_states_promotes_workflow_authority",
}
_STATE_LIST_FIELD_ERROR_CODES = {
    "degraded_states": "degraded_states_not_sequence",
    "disabled_states": "disabled_states_not_sequence",
}
_STATE_LIST_BLANK_ENTRY_ERROR_CODES = {
    "degraded_states": "degraded_states_blank_entry",
    "disabled_states": "disabled_states_blank_entry",
}
_STATE_LIST_WHITESPACE_ENTRY_ERROR_CODES = {
    "degraded_states": "degraded_states_whitespace_drift",
    "disabled_states": "disabled_states_whitespace_drift",
}
_SCALAR_FIELD_WHITESPACE_ERROR_CODES = {
    "source_id": "source_id_whitespace_drift",
    "source_type": "source_type_whitespace_drift",
    "owner": "owner_whitespace_drift",
    "allowed_target_class": "allowed_target_class_whitespace_drift",
    "custody_requirements": "custody_requirements_whitespace_drift",
    "freshness_window": "freshness_window_whitespace_drift",
    "confidence_posture": "confidence_posture_whitespace_drift",
    "status": "status_whitespace_drift",
    "authority_posture": "authority_posture_whitespace_drift",
}
_SCALAR_FIELD_TYPE_ERROR_CODES = {
    "custody_requirements": "custody_requirements_not_string",
}
_MALFORMED_REGISTRY_ENTRY_ERROR = "registry_entry_not_object"
_NEGATED_REQUIRED_CUSTODY_PREFIXES = ("missing", "not", "no", "without", "un", "non")
_NEGATED_REQUIRED_CUSTODY_PREFIX_BRIDGE_TOKENS = frozenset(
    {
        "a",
        "an",
        "the",
        "any",
        "absolutely",
        "currently",
        "longer",
        "really",
        "yet",
    }
)
_NEGATED_REQUIRED_CUSTODY_SUFFIXES = (
    "absent",
    "missing",
    "not available",
    "not present",
    "not reviewed",
    "not verified",
    "omitted",
    "unavailable",
    "unverified",
)
_NEGATED_REQUIRED_CUSTODY_LINKING_VERBS = ("is", "are", "was", "were")
_NEGATED_REQUIRED_CUSTODY_CONTRACTIONS = ("isn t", "aren t", "wasn t", "weren t")
_NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES = (
    "available",
    "present",
    "reviewed",
    "verified",
)
_NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS = ("currently", "longer")


def _has_authority_widening_claim(value: str) -> bool:
    return _has_normalized_boundary_term(value, _NORMALIZED_AUTHORITY_WIDENING_TERMS)


def _has_broad_or_default_source_claim(value: str) -> bool:
    return _has_normalized_boundary_term(
        value,
        (
            *_NORMALIZED_BROAD_OR_DEFAULT_SOURCE_TERMS,
            *_NORMALIZED_BROAD_SOURCE_ALIASES,
        ),
    )


def _authority_widening_field_errors(entry: EvidenceSourceEntry) -> list[str]:
    scalar_fields = (
        "source_id",
        "source_type",
        "owner",
        "allowed_target_class",
        "custody_requirements",
        "freshness_window",
        "confidence_posture",
        "status",
        "authority_posture",
    )
    sequence_fields = ("degraded_states", "disabled_states")

    errors: list[str] = []
    for field_name in scalar_fields:
        if _has_authority_widening_claim(str(getattr(entry, field_name))):
            errors.append(_AUTHORITY_FIELD_ERROR_CODES[field_name])
    for field_name in sequence_fields:
        if any(
            _has_authority_widening_claim(value)
            for value in getattr(entry, field_name)
        ):
            errors.append(_AUTHORITY_FIELD_ERROR_CODES[field_name])
    return errors


def _entry_text_values(entry: EvidenceSourceEntry) -> tuple[str, ...]:
    return (
        entry.source_id,
        entry.source_type,
        entry.owner,
        entry.allowed_target_class,
        entry.custody_requirements,
        entry.freshness_window,
        entry.confidence_posture,
        entry.status,
        entry.authority_posture,
        *entry.degraded_states,
        *entry.disabled_states,
    )


def _broad_or_default_source_errors(entry: EvidenceSourceEntry) -> list[str]:
    if any(_has_broad_or_default_source_claim(value) for value in _entry_text_values(entry)):
        return ["unsupported_broad_source_reference"]
    return []


def _contains_required_custody_term(
    bounded_custody_text: str,
    required_custody_term: str,
) -> bool:
    return f" {required_custody_term} " in bounded_custody_text


def _prefix_negates_required_custody_term(
    prefix_tokens: tuple[str, ...],
    prefix_sequences: tuple[tuple[str, ...], ...],
) -> bool:
    for prefix_sequence in prefix_sequences:
        for _, prefix_end in _normalized_term_spans(prefix_tokens, prefix_sequence):
            bridge_tokens = prefix_tokens[prefix_end:]
            if all(
                token in _NEGATED_REQUIRED_CUSTODY_PREFIX_BRIDGE_TOKENS
                for token in bridge_tokens
            ):
                return True
    return False


def _contains_negated_required_custody_term(
    bounded_custody_text: str,
    required_custody_terms: tuple[str, ...],
) -> bool:
    custody_tokens = tuple(bounded_custody_text.split())
    prefix_sequences = tuple(
        tuple(_normalize_boundary_text(prefix).split())
        for prefix in _NEGATED_REQUIRED_CUSTODY_PREFIXES
    )

    suffix_sequences = tuple(
        tuple(_normalize_boundary_text(suffix).split())
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} {suffix}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{contraction} {state}").split())
        for contraction in _NEGATED_REQUIRED_CUSTODY_CONTRACTIONS
        for state in _NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} no {modifier} available").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} {modifier} {suffix}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} no {modifier} {state}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
        for state in _NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES
    )

    for required_term in required_custody_terms:
        term_tokens = required_term.split()
        if not term_tokens:
            continue
        for start, end in _normalized_term_spans(custody_tokens, tuple(term_tokens)):
            prefix_tokens = custody_tokens[:start]
            if _prefix_negates_required_custody_term(
                prefix_tokens,
                prefix_sequences,
            ):
                return True

            if any(
                _match_normalized_term_at(custody_tokens, end, sequence) is not None
                for sequence in suffix_sequences
            ):
                return True
    return False


def _contains_all_required_custody_terms(
    bounded_custody_text: str,
    required_custody_terms: tuple[str, ...],
) -> bool:
    return all(
        _contains_required_custody_term(bounded_custody_text, term)
        for term in required_custody_terms
    )
