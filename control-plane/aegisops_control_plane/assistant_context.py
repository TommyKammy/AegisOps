from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import re
from typing import Any, Callable, Mapping

from .ai_trace_lifecycle import AITraceLifecycleService
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    HuntRunRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
    AlertRecord,
)


def _dedupe_strings(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set)):
        return ()
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def _collect_reviewed_context_scalar_paths(
    value: object,
    *,
    prefix: str = "",
) -> dict[str, set[str]]:
    collected: dict[str, set[str]] = {}
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            for path, seen_values in _collect_reviewed_context_scalar_paths(
                child,
                prefix=child_prefix,
            ).items():
                collected.setdefault(path, set()).update(seen_values)
        return collected
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            for path, seen_values in _collect_reviewed_context_scalar_paths(
                item,
                prefix=child_prefix,
            ).items():
                collected.setdefault(path, set()).update(seen_values)
        return collected
    if prefix:
        collected[prefix] = {repr(value)}
    return collected


def _reviewed_context_identifier_citations(
    reviewed_context: Mapping[str, object],
) -> tuple[str, ...]:
    citations: list[str] = []
    for path, values in _collect_reviewed_context_scalar_paths(reviewed_context).items():
        leaf_name = path.rsplit(".", 1)[-1]
        if "[" in leaf_name:
            leaf_name = leaf_name.split("[", 1)[0]
        if not leaf_name.endswith("_id"):
            continue
        for value in sorted(values):
            normalized_value = value[1:-1] if value.startswith("'") and value.endswith("'") else value
            normalized_value = normalized_value.strip()
            if normalized_value in {"", "None"}:
                continue
            citation = f"reviewed_context.{path}={normalized_value}"
            if citation not in citations:
                citations.append(citation)
    return tuple(citations)


def _reviewed_context_conflict_paths(
    contexts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    by_path: dict[str, set[str]] = {}
    for context in contexts:
        for path, values in _collect_reviewed_context_scalar_paths(context).items():
            by_path.setdefault(path, set()).update(values)
    return tuple(sorted(path for path, values in by_path.items() if len(values) > 1))


def _assistant_advisory_output_kind(record_family: str) -> str:
    if record_family in {"recommendation", "ai_trace"}:
        return "recommendation_draft"
    if record_family in {"case", "reconciliation"}:
        return "case_summary"
    return "triage_summary"


def _reviewed_identity_is_alias_only(reviewed_context: Mapping[str, object]) -> bool:
    identity = reviewed_context.get("identity")
    if not isinstance(identity, Mapping):
        return False

    stable_identifier_keys = ("identity_id", "principal_id", "subject_id")
    if any(
        isinstance(identity.get(key), str) and identity.get(key)
        for key in stable_identifier_keys
    ):
        return False

    alias_like_keys = ("alias", "aliases", "display_name", "name", "username")
    return any(identity.get(key) for key in alias_like_keys)


def _normalized_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalized_string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        normalized_item = _normalized_optional_string(item)
        if normalized_item is not None and normalized_item not in normalized:
            normalized.append(normalized_item)
    return tuple(normalized)


def _assistant_draft_failure_flags(unresolved_reasons: tuple[str, ...]) -> tuple[str, ...]:
    flags: list[str] = []
    for reason in unresolved_reasons:
        lowered = reason.lower()
        if "bounded live assistant did not return a trusted summary" in lowered:
            flags.append("provider_generation_failed")
        elif "provider" in lowered and "trusted summary" in lowered:
            flags.append("provider_generation_failed")
        elif "citation" in lowered:
            flags.append("missing_supporting_citations")
        elif "conflict" in lowered:
            flags.append("conflicting_reviewed_context")
    return _dedupe_strings(tuple(flags))


def _linked_casework_identity_ambiguity_records(
    linked_evidence_records: tuple[dict[str, object], ...],
) -> tuple[dict[str, str], ...]:
    blocking_reasons = {
        "stable_identifier_mismatch",
        "alias_like_overlap",
        "alias_overlap",
        "identity_alias_overlap",
    }
    unresolved_records: list[dict[str, str]] = []
    seen_record_ids: set[str] = set()
    for evidence in linked_evidence_records:
        evidence_id = _normalized_optional_string(evidence.get("evidence_id"))
        if evidence_id is None or evidence_id in seen_record_ids:
            continue
        provenance = evidence.get("provenance")
        if not isinstance(provenance, Mapping):
            continue
        ambiguity_badge = _normalized_optional_string(provenance.get("ambiguity_badge"))
        classification = _normalized_optional_string(provenance.get("classification"))
        blocking_reason = _normalized_optional_string(provenance.get("blocking_reason"))
        if ambiguity_badge != "unresolved" and classification != "unresolved-linkage":
            continue
        if blocking_reason not in blocking_reasons:
            continue
        seen_record_ids.add(evidence_id)
        unresolved_records.append(
            {
                "evidence_id": evidence_id,
                "blocking_reason": blocking_reason,
            }
        )
    return tuple(unresolved_records)


def _recommendation_draft_review_summary(
    record_family: str,
    record_id: str,
    lifecycle_state: object,
) -> str:
    state = lifecycle_state if isinstance(lifecycle_state, str) else ""
    if record_family == "recommendation" and state == "accepted":
        return (
            f"Recommendation draft {record_id} has been accepted and is anchored "
            "to cited evidence and reviewed lineage."
        )
    if record_family == "recommendation" and state == "rejected":
        return (
            f"Recommendation draft {record_id} has been rejected and is anchored "
            "to cited evidence and reviewed lineage."
        )
    if state == "accepted_for_reference":
        return (
            f"Recommendation draft {record_id} has been accepted for reference and is "
            "anchored to cited evidence and reviewed lineage."
        )
    if state == "rejected_for_reference":
        return (
            f"Recommendation draft {record_id} has been rejected for reference and is "
            "anchored to cited evidence and reviewed lineage."
        )
    return (
        f"Recommendation draft {record_id} remains under review and is anchored "
        "to cited evidence and reviewed lineage."
    )


def _advisory_text_claims_authority_or_scope_expansion(text: object) -> tuple[str, ...]:
    if not isinstance(text, str):
        return ()

    lowered = text.lower()
    flags: list[str] = []

    def contains_term(term: str) -> bool:
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        return re.search(pattern, lowered) is not None

    authority_terms = (
        "approval granted",
        "approved",
        "execute",
        "execution",
        "reconcile",
        "reconciliation",
        "resolved",
        "closed",
    )
    if any(contains_term(term) for term in authority_terms):
        flags.append("authority_overreach")

    scope_terms = (
        "all tenants",
        "tenant-wide",
        "organization-wide",
        "entire organization",
        "fleet-wide",
        "global",
    )
    if any(contains_term(term) for term in scope_terms):
        flags.append("scope_expansion_attempt")

    return _dedupe_strings(tuple(flags))


def _assistant_advisory_draft_without_revision_history(
    draft: Mapping[str, object],
) -> dict[str, object]:
    return {
        str(key): value
        for key, value in draft.items()
        if str(key) != "revision_history"
    }


def _assistant_advisory_draft_revision_history(
    draft: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_history = draft.get("revision_history", ())
    if not isinstance(raw_history, (list, tuple)):
        return ()
    revision_history: list[dict[str, object]] = []
    for entry in raw_history:
        if isinstance(entry, Mapping):
            revision_history.append(
                _assistant_advisory_draft_without_revision_history(entry)
            )
    return tuple(revision_history)


def _build_assistant_advisory_output(
    *,
    record_family: str,
    record_id: str,
    record: dict[str, object],
    reviewed_context: Mapping[str, object],
    linked_alert_ids: tuple[str, ...],
    linked_case_ids: tuple[str, ...],
    linked_evidence_ids: tuple[str, ...],
    linked_recommendation_ids: tuple[str, ...],
    linked_alert_records: tuple[dict[str, object], ...],
    linked_case_records: tuple[dict[str, object], ...],
    linked_evidence_records: tuple[dict[str, object], ...],
    linked_recommendation_records: tuple[dict[str, object], ...],
) -> dict[str, object]:
    output_kind = _assistant_advisory_output_kind(record_family)
    reviewed_context_citations = _reviewed_context_identifier_citations(reviewed_context)
    citations = _dedupe_strings(
        (
            record_id,
            *linked_alert_ids,
            *linked_case_ids,
            *linked_evidence_ids,
            *linked_recommendation_ids,
            *reviewed_context_citations,
        )
    )
    supporting_citations = _dedupe_strings(
        (
            *linked_alert_ids,
            *linked_case_ids,
            *linked_evidence_ids,
            *reviewed_context_citations,
        )
    )
    context_conflicts = _reviewed_context_conflict_paths(
        tuple(
            context
            for context in (
                record.get("reviewed_context"),
                *(linked_alert.get("reviewed_context") for linked_alert in linked_alert_records),
                *(linked_case.get("reviewed_context") for linked_case in linked_case_records),
                *(
                    linked_recommendation.get("reviewed_context")
                    for linked_recommendation in linked_recommendation_records
                ),
            )
            if isinstance(context, Mapping)
        )
    )

    uncertainty_flags = ["advisory_only"]
    unresolved_questions: list[dict[str, object]] = []
    fail_closed = False
    unresolved_summary_override: str | None = None
    unresolved_summary_citations: tuple[str, ...] | None = None
    intended_outcome = record.get("intended_outcome")
    unsafe_intended_outcome_flags = _advisory_text_claims_authority_or_scope_expansion(
        intended_outcome
    )
    assistant_advisory_draft = record.get("assistant_advisory_draft")
    if isinstance(assistant_advisory_draft, Mapping):
        draft_status = _normalized_optional_string(assistant_advisory_draft.get("status"))
        draft_unresolved_reasons = _normalized_string_tuple(
            assistant_advisory_draft.get("unresolved_reasons")
        )
        if draft_status == "unresolved" and draft_unresolved_reasons:
            fail_closed = True
            draft_failure_flags = _assistant_draft_failure_flags(draft_unresolved_reasons)
            uncertainty_flags.extend(draft_failure_flags or ("assistant_advisory_unresolved",))
            draft_cited_summary = assistant_advisory_draft.get("cited_summary")
            if isinstance(draft_cited_summary, Mapping):
                unresolved_summary_override = _normalized_optional_string(
                    draft_cited_summary.get("text")
                )
            unresolved_questions.append(
                {
                    "text": (
                        "Which reviewed provider result, retry evidence, or citation repair "
                        "resolves this advisory failure: "
                        + "; ".join(draft_unresolved_reasons)
                        + "?"
                    ),
                    "citations": _dedupe_strings(
                        (
                            record_id,
                            _normalized_optional_string(
                                assistant_advisory_draft.get("source_ai_trace_id")
                            ),
                        )
                    ),
                }
            )

    if not supporting_citations:
        fail_closed = True
        uncertainty_flags.append("missing_supporting_citations")
        unresolved_questions.append(
            {
                "text": "Which reviewed records, linked evidence, or stable reviewed-context identifiers support this advisory output?",
                "citations": (record_id,),
            }
        )
    if output_kind == "recommendation_draft" and not linked_evidence_ids:
        fail_closed = True
        uncertainty_flags.append("missing_evidence_citation")
        unresolved_questions.append(
            {
                "text": "Which linked evidence anchor supports this recommendation draft?",
                "citations": (record_id,),
            }
        )
    if context_conflicts:
        fail_closed = True
        uncertainty_flags.append("conflicting_reviewed_context")
        unresolved_questions.append(
            {
                "text": (
                    "Which reviewed-context values are authoritative for: "
                    + ", ".join(context_conflicts)
                    + "?"
                ),
                "citations": citations,
            }
        )
    if _reviewed_identity_is_alias_only(reviewed_context):
        fail_closed = True
        uncertainty_flags.append("ambiguous_identity_alias_only")
        unresolved_questions.append(
            {
                "text": (
                    "Which stable identity identifier or reviewed linkage resolves the "
                    "alias-style identity metadata for this advisory output?"
                ),
                "citations": citations,
            }
        )
    linked_casework_identity_ambiguity = _linked_casework_identity_ambiguity_records(
        linked_evidence_records
    )
    if linked_casework_identity_ambiguity:
        fail_closed = True
        uncertainty_flags.append("reviewed_casework_identity_ambiguity")
        ambiguity_citations = _dedupe_strings(
            (
                record_id,
                *(
                    entry["evidence_id"]
                    for entry in linked_casework_identity_ambiguity
                ),
            )
        )
        ambiguity_details = ", ".join(
            f"{entry['evidence_id']} ({entry['blocking_reason']})"
            for entry in linked_casework_identity_ambiguity
        )
        unresolved_summary_override = (
            f"{output_kind.replace('_', ' ').capitalize()} {record_id} remains unresolved "
            "because reviewed multi-source casework still contains unresolved identity "
            f"ambiguity: {ambiguity_details}."
        )
        unresolved_summary_citations = ambiguity_citations
        unresolved_questions.append(
            {
                "text": (
                    "Which stable identity identifier or explicit reviewed linkage resolves "
                    "the multi-source identity ambiguity attached to: "
                    f"{ambiguity_details}?"
                ),
                "citations": ambiguity_citations,
            }
        )
    if unsafe_intended_outcome_flags:
        fail_closed = True
        uncertainty_flags.extend(unsafe_intended_outcome_flags)
        unresolved_questions.append(
            {
                "text": (
                    "Which reviewed records constrain the recommendation scope and keep "
                    "approval, execution, and reconciliation authority outside the "
                    "assistant output?"
                ),
                "citations": citations,
            }
        )

    key_observations: list[dict[str, object]] = []
    if linked_evidence_ids:
        key_observations.append(
            {
                "text": (
                    "Linked evidence anchors this advisory output through "
                    + ", ".join(linked_evidence_ids)
                    + "."
                ),
                "citations": _dedupe_strings((record_id, *linked_evidence_ids)),
            }
        )
    if reviewed_context_citations:
        key_observations.append(
            {
                "text": "Reviewed context exposes stable identifiers for the cited advisory output.",
                "citations": reviewed_context_citations,
            }
        )
    if linked_alert_ids or linked_case_ids:
        key_observations.append(
            {
                "text": "Record linkage preserves the reviewed alert and case lineage for this advisory output.",
                "citations": _dedupe_strings((record_id, *linked_alert_ids, *linked_case_ids)),
            }
        )

    status = "unresolved" if fail_closed else "ready"
    if status == "ready":
        if output_kind == "recommendation_draft":
            summary_text = _recommendation_draft_review_summary(
                record_family,
                record_id,
                record.get("lifecycle_state"),
            )
        elif output_kind == "case_summary":
            summary_text = (
                f"Case summary {record_id} is grounded in reviewed record linkage, "
                f"linked evidence, and stable reviewed-context identifiers."
            )
        else:
            summary_text = (
                f"Triage summary {record_id} is grounded in reviewed record linkage, "
                f"linked evidence, and stable reviewed-context identifiers."
            )
    else:
        summary_text = unresolved_summary_override or (
            f"{output_kind.replace('_', ' ').capitalize()} {record_id} remains unresolved "
            "because citation completeness or reviewed-context consistency is incomplete."
        )

    candidate_recommendations: list[dict[str, object]] = []
    if (
        isinstance(intended_outcome, str)
        and intended_outcome
        and not unsafe_intended_outcome_flags
    ):
        candidate_recommendations.append(
            {
                "text": f"Proposal only: {intended_outcome}.",
                "citations": _dedupe_strings((record_id, *supporting_citations)),
            }
        )
    elif supporting_citations:
        candidate_recommendations.append(
            {
                "text": (
                    "Proposal only: review the cited evidence and unresolved conditions "
                    "before any approval, execution, or reconciliation decision."
                ),
                "citations": supporting_citations,
            }
        )

    return {
        "output_kind": output_kind,
        "status": status,
        "cited_summary": {
            "text": summary_text,
            "citations": unresolved_summary_citations
            or _dedupe_strings((record_id, *supporting_citations)),
        },
        "key_observations": tuple(key_observations),
        "unresolved_questions": tuple(unresolved_questions),
        "candidate_recommendations": tuple(candidate_recommendations),
        "citations": citations,
        "uncertainty_flags": _dedupe_strings(tuple(uncertainty_flags)),
        "reviewed_context_conflicts": context_conflicts,
    }


@dataclass(frozen=True)
class _AssistantContextLineage:
    alert_ids: tuple[str, ...]
    case_ids: tuple[str, ...]
    finding_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    ai_trace_records: tuple[AITraceRecord, ...]
    recommendation_records: tuple[RecommendationRecord, ...]
    reconciliation_records: tuple[ReconciliationRecord, ...]


@dataclass(frozen=True)
class _AssistantContextLinkedRecords:
    alert_records: tuple[dict[str, object], ...]
    case_records: tuple[dict[str, object], ...]
    evidence_records: tuple[EvidenceRecord, ...]
    recommendation_payloads: tuple[dict[str, object], ...]
    reconciliation_records: tuple[ReconciliationRecord, ...]


@dataclass(frozen=True)
class _AssistantContextIds:
    alert_ids: tuple[str, ...]
    case_ids: tuple[str, ...]
    finding_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


class AssistantContextAssembler:
    def __init__(
        self,
        service: Any,
        *,
        record_types_by_family: Mapping[str, type[object]],
        record_to_dict: Callable[[object], dict[str, object]],
        merge_reviewed_context: Callable[[Mapping[str, object], object], dict[str, object]],
        assistant_context_snapshot_factory: Callable[..., Any],
        advisory_snapshot_from_context: Callable[[Any], Any],
        recommendation_draft_snapshot_from_context: Callable[[Any], Any],
        ai_trace_lifecycle: AITraceLifecycleService,
    ) -> None:
        self._service = service
        self._record_types_by_family = record_types_by_family
        self._record_to_dict = record_to_dict
        self._merge_reviewed_context = merge_reviewed_context
        self._assistant_context_snapshot_factory = assistant_context_snapshot_factory
        self._advisory_snapshot_from_context = advisory_snapshot_from_context
        self._recommendation_draft_snapshot_from_context = (
            recommendation_draft_snapshot_from_context
        )
        self._ai_trace_lifecycle = ai_trace_lifecycle

    def inspect_assistant_context(self, record_family: str, record_id: str) -> Any:
        record_family = self._service._require_non_empty_string(record_family, "record_family")
        record_id = self._service._require_non_empty_string(record_id, "record_id")
        record = self._require_context_record(record_family, record_id)
        lineage = self._context_lineage(record)
        linked_records = self._linked_records_for_context(record, lineage)
        reviewed_context = self._context_reviewed_context(
            record=record,
            linked_alert_records=linked_records.alert_records,
            linked_case_records=linked_records.case_records,
        )
        return self._build_context_snapshot(
            record_family=record_family,
            record_id=record_id,
            record=record,
            lineage=lineage,
            linked_records=linked_records,
            reviewed_context=reviewed_context,
        )

    def _require_context_record(self, record_family: str, record_id: str) -> object:
        record_type = self._record_types_by_family.get(record_family)
        if record_type is None:
            known_families = ", ".join(sorted(self._record_types_by_family))
            raise ValueError(
                f"Unsupported control-plane record family {record_family!r}; "
                f"expected one of: {known_families}"
            )
        record = self._service._store.get(record_type, record_id)
        if record is None:
            raise LookupError(
                f"Missing {record_family} record {record_id!r} for assistant context"
            )
        if record_family == "case":
            self._service._require_reviewed_operator_case_record(record)
        return record

    def _context_lineage(self, record: object) -> _AssistantContextLineage:
        ids = self._anchor_record_lineage(record)
        linked_ai_trace_records = self._ai_trace_lifecycle.ai_trace_records_for_context(record)
        ids = self._merge_ai_trace_lineage(ids, linked_ai_trace_records)
        linked_evidence_records, ids = self._merge_evidence_lineage(record, ids)
        linked_recommendation_records, ids = self._merge_recommendation_lineage(
            record=record,
            ids=ids,
            linked_ai_trace_records=linked_ai_trace_records,
        )
        linked_reconciliation_records = (
            self._ai_trace_lifecycle.reconciliation_records_for_context(
                record=record,
                alert_ids=ids.alert_ids,
                case_ids=ids.case_ids,
                finding_ids=ids.finding_ids,
                evidence_ids=ids.evidence_ids,
                exclude_reconciliation_id=(
                    record.record_id if isinstance(record, ReconciliationRecord) else None
                ),
            )
        )
        return _AssistantContextLineage(
            alert_ids=ids.alert_ids,
            case_ids=ids.case_ids,
            finding_ids=ids.finding_ids,
            evidence_ids=ids.evidence_ids,
            ai_trace_records=linked_ai_trace_records,
            recommendation_records=linked_recommendation_records,
            reconciliation_records=linked_reconciliation_records,
        )

    def _anchor_record_lineage(self, record: object) -> _AssistantContextIds:
        linked_alert_ids = self._ai_trace_lifecycle.ids_from_value(
            getattr(record, "alert_id", None)
        )
        linked_case_ids = self._ai_trace_lifecycle.ids_from_value(
            getattr(record, "case_id", None)
        )
        linked_finding_ids = self._ai_trace_lifecycle.ids_from_value(
            getattr(record, "finding_id", None)
        )
        linked_evidence_ids = self._ai_trace_lifecycle.linked_evidence_ids(record)

        if isinstance(record, (ApprovalDecisionRecord, ActionExecutionRecord)):
            action_request_id = self._service._require_non_empty_string(
                getattr(record, "action_request_id", None),
                "action_request_id",
            )
            action_request = self._service._store.get(ActionRequestRecord, action_request_id)
            if action_request is None:
                raise LookupError(
                    f"Missing action request {action_request_id!r} for assistant context"
                )
            linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                linked_alert_ids,
                action_request.alert_id,
            )
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                action_request.case_id,
            )
            linked_finding_ids = self._ai_trace_lifecycle.merge_ids(
                linked_finding_ids,
                action_request.finding_id,
            )

        if isinstance(record, AnalyticSignalRecord):
            linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                linked_alert_ids,
                record.alert_ids,
            )
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                record.case_ids,
            )
        elif isinstance(record, CaseRecord):
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                record.evidence_ids,
            )
        elif isinstance(record, EvidenceRecord):
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.evidence_siblings(record),
            )
        elif isinstance(record, ObservationRecord):
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                record.supporting_evidence_ids,
            )
        elif isinstance(record, ReconciliationRecord):
            return self._reconciliation_anchor_lineage(
                record,
                _AssistantContextIds(
                    alert_ids=linked_alert_ids,
                    case_ids=linked_case_ids,
                    finding_ids=linked_finding_ids,
                    evidence_ids=linked_evidence_ids,
                ),
            )
        elif isinstance(record, HuntRunRecord):
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.ids_from_mapping(record.output_linkage, "evidence_ids"),
            )

        return _AssistantContextIds(
            alert_ids=linked_alert_ids,
            case_ids=linked_case_ids,
            finding_ids=linked_finding_ids,
            evidence_ids=linked_evidence_ids,
        )

    def _reconciliation_anchor_lineage(
        self,
        record: ReconciliationRecord,
        ids: _AssistantContextIds,
    ) -> _AssistantContextIds:
        linked_alert_ids = self._service._merge_linked_ids(ids.alert_ids, record.alert_id)
        linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
            linked_alert_ids,
            self._ai_trace_lifecycle.ids_from_mapping(record.subject_linkage, "alert_ids"),
        )
        linked_case_ids = ids.case_ids
        linked_finding_ids = ids.finding_ids
        linked_evidence_ids = ids.evidence_ids
        (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        ) = self._ai_trace_lifecycle.action_lineage_ids(record)
        for action_request_id in action_request_ids:
            action_request = self._service._store.get(ActionRequestRecord, action_request_id)
            if action_request is not None:
                (
                    linked_alert_ids,
                    linked_case_ids,
                    linked_finding_ids,
                ) = self._ai_trace_lifecycle.merge_action_request_linkage(
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                    action_request=action_request,
                )
        for approval_decision_id in approval_decision_ids:
            approval_decision = self._service._store.get(
                ApprovalDecisionRecord,
                approval_decision_id,
            )
            if approval_decision is None:
                continue
            action_request = self._service._store.get(
                ActionRequestRecord,
                approval_decision.action_request_id,
            )
            if action_request is not None:
                (
                    linked_alert_ids,
                    linked_case_ids,
                    linked_finding_ids,
                ) = self._ai_trace_lifecycle.merge_action_request_linkage(
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                    action_request=action_request,
                )
        linked_alert_ids, linked_case_ids, linked_finding_ids, linked_evidence_ids = (
            self._merge_reconciliation_execution_lineage(
                action_execution_ids=action_execution_ids,
                delegation_ids=delegation_ids,
                linked_alert_ids=linked_alert_ids,
                linked_case_ids=linked_case_ids,
                linked_finding_ids=linked_finding_ids,
                linked_evidence_ids=linked_evidence_ids,
            )
        )
        for analytic_signal_id in self._ai_trace_lifecycle.ids_from_mapping(
            record.subject_linkage,
            "analytic_signal_ids",
        ):
            signal = self._service._store.get(AnalyticSignalRecord, analytic_signal_id)
            if signal is None:
                continue
            linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                linked_alert_ids,
                signal.alert_ids,
            )
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                signal.case_ids,
            )
            linked_finding_ids = self._ai_trace_lifecycle.merge_ids(
                linked_finding_ids,
                signal.finding_id,
            )
        for alert_id in linked_alert_ids:
            alert = self._service._store.get(AlertRecord, alert_id)
            if alert is None:
                continue
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                alert.case_id,
            )
            linked_finding_ids = self._ai_trace_lifecycle.merge_ids(
                linked_finding_ids,
                alert.finding_id,
            )
        return _AssistantContextIds(
            alert_ids=linked_alert_ids,
            case_ids=self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                self._ai_trace_lifecycle.ids_from_mapping(
                    record.subject_linkage,
                    "case_ids",
                ),
            ),
            finding_ids=self._ai_trace_lifecycle.merge_ids(
                linked_finding_ids,
                self._ai_trace_lifecycle.ids_from_mapping(
                    record.subject_linkage,
                    "finding_ids",
                ),
            ),
            evidence_ids=self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.ids_from_mapping(
                    record.subject_linkage,
                    "evidence_ids",
                ),
            ),
        )

    def _merge_reconciliation_execution_lineage(
        self,
        *,
        action_execution_ids: tuple[str, ...],
        delegation_ids: tuple[str, ...],
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
        linked_evidence_ids: tuple[str, ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        for action_execution_id in action_execution_ids:
            action_execution = self._service._store.get(
                ActionExecutionRecord,
                action_execution_id,
            )
            if action_execution is None:
                continue
            linked_alert_ids, linked_case_ids, linked_finding_ids = (
                self._merge_action_execution_request_lineage(
                    action_execution=action_execution,
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                )
            )
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.linked_evidence_ids(action_execution),
            )
        for delegation_id in delegation_ids:
            action_execution = self._ai_trace_lifecycle.action_execution_for_delegation_id(
                delegation_id
            )
            if action_execution is None:
                continue
            linked_alert_ids, linked_case_ids, linked_finding_ids = (
                self._merge_action_execution_request_lineage(
                    action_execution=action_execution,
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                )
            )
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.linked_evidence_ids(action_execution),
            )
        return (
            linked_alert_ids,
            linked_case_ids,
            linked_finding_ids,
            linked_evidence_ids,
        )

    def _merge_action_execution_request_lineage(
        self,
        *,
        action_execution: ActionExecutionRecord,
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        action_request = self._service._store.get(
            ActionRequestRecord,
            action_execution.action_request_id,
        )
        if action_request is None:
            return linked_alert_ids, linked_case_ids, linked_finding_ids
        return self._ai_trace_lifecycle.merge_action_request_linkage(
            linked_alert_ids=linked_alert_ids,
            linked_case_ids=linked_case_ids,
            linked_finding_ids=linked_finding_ids,
            action_request=action_request,
        )

    def _merge_ai_trace_lineage(
        self,
        ids: _AssistantContextIds,
        linked_ai_trace_records: tuple[AITraceRecord, ...],
    ) -> _AssistantContextIds:
        linked_alert_ids = ids.alert_ids
        linked_case_ids = ids.case_ids
        linked_evidence_ids = ids.evidence_ids
        for ai_trace_record in linked_ai_trace_records:
            linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                linked_alert_ids,
                self._ai_trace_lifecycle.ids_from_mapping(
                    ai_trace_record.subject_linkage,
                    "alert_ids",
                ),
            )
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                self._ai_trace_lifecycle.ids_from_mapping(
                    ai_trace_record.subject_linkage,
                    "case_ids",
                ),
            )
            linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
                linked_evidence_ids,
                self._ai_trace_lifecycle.ai_trace_evidence_ids(ai_trace_record),
            )
        return _AssistantContextIds(
            alert_ids=linked_alert_ids,
            case_ids=linked_case_ids,
            finding_ids=ids.finding_ids,
            evidence_ids=linked_evidence_ids,
        )

    def _merge_evidence_lineage(
        self,
        record: object,
        ids: _AssistantContextIds,
    ) -> tuple[tuple[EvidenceRecord, ...], _AssistantContextIds]:
        linked_evidence_records = self._ai_trace_lifecycle.evidence_records_for_context(
            alert_ids=ids.alert_ids,
            case_ids=ids.case_ids,
            evidence_ids=ids.evidence_ids,
            exclude_evidence_id=(
                record.evidence_id if isinstance(record, EvidenceRecord) else None
            ),
        )
        linked_evidence_ids = self._ai_trace_lifecycle.merge_ids(
            ids.evidence_ids,
            tuple(evidence.evidence_id for evidence in linked_evidence_records),
        )
        linked_alert_ids = ids.alert_ids
        linked_case_ids = ids.case_ids
        for evidence in linked_evidence_records:
            linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                linked_alert_ids,
                evidence.alert_id,
            )
            linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                linked_case_ids,
                evidence.case_id,
            )
        return (
            linked_evidence_records,
            _AssistantContextIds(
                alert_ids=linked_alert_ids,
                case_ids=linked_case_ids,
                finding_ids=ids.finding_ids,
                evidence_ids=linked_evidence_ids,
            ),
        )

    def _merge_recommendation_lineage(
        self,
        *,
        record: object,
        ids: _AssistantContextIds,
        linked_ai_trace_records: tuple[AITraceRecord, ...],
    ) -> tuple[tuple[RecommendationRecord, ...], _AssistantContextIds]:
        linked_recommendation_records = self._ai_trace_lifecycle.recommendation_records_for_context(
            record=record,
            alert_ids=ids.alert_ids,
            case_ids=ids.case_ids,
            ai_trace_records=linked_ai_trace_records,
            exclude_recommendation_id=(
                record.record_id if isinstance(record, RecommendationRecord) else None
            ),
        )
        linked_alert_ids = ids.alert_ids
        linked_case_ids = ids.case_ids
        has_direct_recommendation_lineage = isinstance(record, RecommendationRecord) and (
            record.alert_id is not None or record.case_id is not None
        )
        if not has_direct_recommendation_lineage:
            for recommendation in linked_recommendation_records:
                linked_alert_ids = self._ai_trace_lifecycle.merge_ids(
                    linked_alert_ids,
                    recommendation.alert_id,
                )
                linked_case_ids = self._ai_trace_lifecycle.merge_ids(
                    linked_case_ids,
                    recommendation.case_id,
                )
        return (
            linked_recommendation_records,
            _AssistantContextIds(
                alert_ids=linked_alert_ids,
                case_ids=linked_case_ids,
                finding_ids=ids.finding_ids,
                evidence_ids=ids.evidence_ids,
            ),
        )

    def _linked_records_for_context(
        self,
        record: object,
        lineage: _AssistantContextLineage,
    ) -> _AssistantContextLinkedRecords:
        linked_alert_records_list: list[dict[str, object]] = []
        for alert_id in lineage.alert_ids:
            alert = self._service._store.get(AlertRecord, alert_id)
            if alert is not None:
                linked_alert_records_list.append(self._record_to_dict(alert))
        linked_alert_records = tuple(linked_alert_records_list)

        linked_case_records_list: list[dict[str, object]] = []
        for case_id in lineage.case_ids:
            case = self._service._store.get(CaseRecord, case_id)
            if case is not None:
                linked_case_records_list.append(self._record_to_dict(case))
        linked_case_records = tuple(linked_case_records_list)

        return _AssistantContextLinkedRecords(
            alert_records=linked_alert_records,
            case_records=linked_case_records,
            evidence_records=self._ai_trace_lifecycle.evidence_records_for_context(
                alert_ids=lineage.alert_ids,
                case_ids=lineage.case_ids,
                evidence_ids=lineage.evidence_ids,
                exclude_evidence_id=(
                    record.evidence_id if isinstance(record, EvidenceRecord) else None
                ),
            ),
            recommendation_payloads=tuple(
                self._record_to_dict(recommendation)
                for recommendation in lineage.recommendation_records
            ),
            reconciliation_records=lineage.reconciliation_records,
        )

    def _context_reviewed_context(
        self,
        *,
        record: object,
        linked_alert_records: tuple[dict[str, object], ...],
        linked_case_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        reviewed_context: dict[str, object] = {}
        raw_reviewed_context = getattr(record, "reviewed_context", None)
        if isinstance(raw_reviewed_context, Mapping):
            reviewed_context = dict(raw_reviewed_context)
        if isinstance(
            record,
            (
                ApprovalDecisionRecord,
                ActionRequestRecord,
                ActionExecutionRecord,
                ReconciliationRecord,
                RecommendationRecord,
                AITraceRecord,
            ),
        ):
            for alert in linked_alert_records:
                reviewed_context = self._merge_reviewed_context(
                    reviewed_context,
                    alert.get("reviewed_context"),
                )
            for case in linked_case_records:
                reviewed_context = self._merge_reviewed_context(
                    reviewed_context,
                    case.get("reviewed_context"),
                )
        return reviewed_context

    def _build_context_snapshot(
        self,
        *,
        record_family: str,
        record_id: str,
        record: object,
        lineage: _AssistantContextLineage,
        linked_records: _AssistantContextLinkedRecords,
        reviewed_context: dict[str, object],
    ) -> Any:
        record_payload = self._record_to_dict(record)
        linked_evidence_payloads = tuple(
            self._record_to_dict(evidence) for evidence in linked_records.evidence_records
        )
        linked_reconciliation_ids = tuple(
            reconciliation.reconciliation_id
            for reconciliation in linked_records.reconciliation_records
        )

        return self._assistant_context_snapshot_factory(
            read_only=True,
            record_family=record_family,
            record_id=record_id,
            record=record_payload,
            advisory_output=_build_assistant_advisory_output(
                record_family=record_family,
                record_id=record_id,
                record=record_payload,
                reviewed_context=reviewed_context,
                linked_alert_ids=lineage.alert_ids,
                linked_case_ids=lineage.case_ids,
                linked_evidence_ids=lineage.evidence_ids,
                linked_recommendation_ids=tuple(
                    recommendation.recommendation_id
                    for recommendation in lineage.recommendation_records
                ),
                linked_alert_records=linked_records.alert_records,
                linked_case_records=linked_records.case_records,
                linked_evidence_records=linked_evidence_payloads,
                linked_recommendation_records=linked_records.recommendation_payloads,
            ),
            reviewed_context=reviewed_context,
            linked_alert_ids=lineage.alert_ids,
            linked_case_ids=lineage.case_ids,
            linked_evidence_ids=lineage.evidence_ids,
            linked_recommendation_ids=tuple(
                recommendation.recommendation_id
                for recommendation in lineage.recommendation_records
            ),
            linked_reconciliation_ids=linked_reconciliation_ids,
            linked_alert_records=linked_records.alert_records,
            linked_case_records=linked_records.case_records,
            linked_evidence_records=linked_evidence_payloads,
            linked_recommendation_records=linked_records.recommendation_payloads,
            linked_reconciliation_records=tuple(
                self._record_to_dict(reconciliation)
                for reconciliation in linked_records.reconciliation_records
            ),
            lifecycle_transitions=tuple(
                self._record_to_dict(transition)
                for transition in self._service._store.list_lifecycle_transitions(
                    record_family,
                    record_id,
                )
            ),
        )

    def inspect_advisory_output(self, record_family: str, record_id: str) -> Any:
        context_snapshot = self.inspect_assistant_context(record_family, record_id)
        self._service._require_reviewed_case_scoped_advisory_read(context_snapshot)
        return self._advisory_snapshot_from_context(context_snapshot)

    def render_recommendation_draft(self, record_family: str, record_id: str) -> Any:
        context_snapshot = self.inspect_assistant_context(record_family, record_id)
        self._service._require_reviewed_case_scoped_advisory_read(context_snapshot)
        return self._recommendation_draft_snapshot_from_context(context_snapshot)

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        record_family = self._service._require_non_empty_string(
            record_family,
            "record_family",
        )
        record_id = self._service._require_non_empty_string(record_id, "record_id")
        if record_family not in {"recommendation", "ai_trace"}:
            raise ValueError(
                "assistant advisory drafts may only be attached to "
                "'recommendation' or 'ai_trace' records"
            )

        record_type = self._record_types_by_family[record_family]
        with self._service._store.transaction():
            self._service._lock_lifecycle_transition_subject(record_family, record_id)
            record = self._service._store.get(record_type, record_id)
            if record is None:
                raise LookupError(
                    f"Missing {record_family} record {record_id!r} "
                    "for advisory draft attachment"
                )
            if not isinstance(record, (RecommendationRecord, AITraceRecord)):
                raise TypeError(
                    "assistant advisory drafts may only be attached to recommendation "
                    "or ai_trace records"
                )

            draft_snapshot = self.render_recommendation_draft(record_family, record_id)
            attached_draft = {
                "draft_id": f"assistant-advisory-draft:{record_family}:{record_id}",
                "source_record_family": record_family,
                "source_record_id": record_id,
                "review_lifecycle_state": record.lifecycle_state,
                **draft_snapshot.recommendation_draft,
                "linked_alert_ids": draft_snapshot.linked_alert_ids,
                "linked_case_ids": draft_snapshot.linked_case_ids,
                "linked_evidence_ids": draft_snapshot.linked_evidence_ids,
                "linked_recommendation_ids": draft_snapshot.linked_recommendation_ids,
                "linked_reconciliation_ids": draft_snapshot.linked_reconciliation_ids,
            }
            current_attached_draft = _assistant_advisory_draft_without_revision_history(
                record.assistant_advisory_draft
            )
            if current_attached_draft == attached_draft:
                return record
            revision_history = _assistant_advisory_draft_revision_history(
                record.assistant_advisory_draft
            )
            if current_attached_draft:
                attached_draft["revision_history"] = (
                    *revision_history,
                    current_attached_draft,
                )
            return self._service._store.save(
                replace(record, assistant_advisory_draft=attached_draft)
            )
