from __future__ import annotations

from contextlib import AbstractContextManager
from collections import Counter
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
import hashlib
import hmac
import ipaddress
import json
import re
import uuid
from typing import Mapping, Protocol, Type, TypeVar

from .adapters.executor import IsolatedExecutorAdapter
from .adapters.n8n import N8NReconciliationAdapter
from .adapters.postgres import PostgresControlPlaneStore
from .adapters.shuffle import ShuffleActionAdapter
from .adapters.wazuh import WazuhAlertAdapter
from .config import RuntimeConfig
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: RecordT) -> RecordT:
        ...

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def transaction(self) -> AbstractContextManager[None]:
        ...


class NativeDetectionRecordAdapter(Protocol):
    substrate_key: str

    def build_analytic_signal_admission(
        self,
        record: NativeDetectionRecord,
    ) -> AnalyticSignalAdmission:
        ...


@dataclass(frozen=True)
class RuntimeSnapshot:
    service_name: str
    bind_host: str
    bind_port: int
    postgres_dsn: str
    persistence_mode: str
    opensearch_url: str
    n8n_base_url: str
    shuffle_base_url: str
    isolated_executor_base_url: str
    ownership_boundary: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FindingAlertIngestResult:
    alert: AlertRecord
    reconciliation: ReconciliationRecord
    disposition: str


@dataclass(frozen=True)
class RecordInspectionSnapshot:
    read_only: bool
    record_family: str
    total_records: int
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "total_records": self.total_records,
                "records": self.records,
            }
        )


@dataclass(frozen=True)
class ReconciliationStatusSnapshot:
    read_only: bool
    total_records: int
    latest_compared_at: datetime | None
    by_lifecycle_state: dict[str, int]
    by_ingest_disposition: dict[str, int]
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "total_records": self.total_records,
                "latest_compared_at": self.latest_compared_at,
                "by_lifecycle_state": self.by_lifecycle_state,
                "by_ingest_disposition": self.by_ingest_disposition,
                "records": self.records,
            }
        )


@dataclass(frozen=True)
class AnalystQueueSnapshot:
    read_only: bool
    queue_name: str
    total_records: int
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "queue_name": self.queue_name,
                "total_records": self.total_records,
                "records": self.records,
            }
        )


@dataclass(frozen=True)
class AnalystAssistantContextSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    record: dict[str, object]
    advisory_output: dict[str, object]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]
    linked_alert_records: tuple[dict[str, object], ...]
    linked_case_records: tuple[dict[str, object], ...]
    linked_evidence_records: tuple[dict[str, object], ...]
    linked_recommendation_records: tuple[dict[str, object], ...]
    linked_reconciliation_records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "record": self.record,
                "advisory_output": self.advisory_output,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
                "linked_alert_records": self.linked_alert_records,
                "linked_case_records": self.linked_case_records,
                "linked_evidence_records": self.linked_evidence_records,
                "linked_recommendation_records": self.linked_recommendation_records,
                "linked_reconciliation_records": self.linked_reconciliation_records,
            }
        )


@dataclass(frozen=True)
class AdvisoryInspectionSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    output_kind: str
    status: str
    cited_summary: dict[str, object]
    key_observations: tuple[dict[str, object], ...]
    unresolved_questions: tuple[dict[str, object], ...]
    candidate_recommendations: tuple[dict[str, object], ...]
    citations: tuple[str, ...]
    uncertainty_flags: tuple[str, ...]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "output_kind": self.output_kind,
                "status": self.status,
                "cited_summary": self.cited_summary,
                "key_observations": self.key_observations,
                "unresolved_questions": self.unresolved_questions,
                "candidate_recommendations": self.candidate_recommendations,
                "citations": self.citations,
                "uncertainty_flags": self.uncertainty_flags,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
            }
        )


@dataclass(frozen=True)
class RecommendationDraftSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    recommendation_draft: dict[str, object]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "recommendation_draft": self.recommendation_draft,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
            }
        )


RECORD_TYPES_BY_FAMILY: dict[str, Type[ControlPlaneRecord]] = {
    record_type.record_family: record_type
    for record_type in (
        AlertRecord,
        AnalyticSignalRecord,
        CaseRecord,
        EvidenceRecord,
        ObservationRecord,
        LeadRecord,
        RecommendationRecord,
        ApprovalDecisionRecord,
        ActionRequestRecord,
        ActionExecutionRecord,
        HuntRecord,
        HuntRunRecord,
        AITraceRecord,
        ReconciliationRecord,
    )
}

_ACTION_POLICY_ALLOWED_VALUES: dict[str, tuple[str, ...]] = {
    "severity": ("low", "medium", "high", "critical"),
    "target_scope": (
        "single_identity",
        "single_asset",
        "multi_identity",
        "multi_asset",
        "fleet",
        "organization",
    ),
    "action_reversibility": (
        "reversible",
        "bounded_reversible",
        "irreversible",
    ),
    "asset_criticality": ("standard", "elevated", "high", "critical"),
    "identity_criticality": ("standard", "elevated", "high", "critical"),
    "blast_radius": (
        "single_target",
        "bounded_group",
        "multi_target",
        "organization",
    ),
    "execution_constraint": (
        "routine_allowed",
        "isolated_preferred",
        "requires_isolated_executor",
    ),
}

_ACTION_POLICY_RANKS: dict[str, dict[str, int]] = {
    field_name: {
        allowed_value: index for index, allowed_value in enumerate(allowed_values)
    }
    for field_name, allowed_values in _ACTION_POLICY_ALLOWED_VALUES.items()
}


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
    }


def _approved_payload_binding_hash(
    *,
    target_scope: Mapping[str, object],
    approved_payload: Mapping[str, object],
    execution_surface_type: str,
    execution_surface_id: str,
) -> str:
    binding = _json_ready(
        {
            "approved_payload": approved_payload,
            "execution_surface_id": execution_surface_id,
            "execution_surface_type": execution_surface_type,
            "target_scope": target_scope,
        }
    )
    encoded = json.dumps(binding, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _merge_reviewed_context(
    existing_context: Mapping[str, object] | None,
    incoming_context: Mapping[str, object] | None,
) -> dict[str, object]:
    merged: dict[str, object] = {}
    if isinstance(existing_context, Mapping):
        merged.update({str(key): value for key, value in existing_context.items()})
    if not isinstance(incoming_context, Mapping):
        return merged

    for key, value in incoming_context.items():
        normalized_key = str(key)
        existing_value = merged.get(normalized_key)
        if isinstance(existing_value, Mapping) and isinstance(value, Mapping):
            merged[normalized_key] = _merge_reviewed_context(existing_value, value)
        else:
            merged[normalized_key] = value
    return merged


def _dedupe_strings(values: object) -> tuple[str, ...]:
    deduped: list[str] = []
    if not isinstance(values, (list, tuple)):
        return ()
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
        for key, item in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            for path, seen_values in _collect_reviewed_context_scalar_paths(
                item,
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


def _normalize_admission_provenance(
    value: object,
) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for field_name in ("admission_kind", "admission_channel"):
        field_value = value.get(field_name)
        if isinstance(field_value, str) and field_value.strip():
            normalized[field_name] = field_value
    if len(normalized) != 2:
        return None
    return normalized


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
    intended_outcome = record.get("intended_outcome")
    unsafe_intended_outcome_flags = _advisory_text_claims_authority_or_scope_expansion(
        intended_outcome
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
        summary_text = (
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
            "citations": _dedupe_strings((record_id, *supporting_citations)),
        },
        "key_observations": tuple(key_observations),
        "unresolved_questions": tuple(unresolved_questions),
        "candidate_recommendations": tuple(candidate_recommendations),
        "citations": citations,
        "uncertainty_flags": _dedupe_strings(tuple(uncertainty_flags)),
    }


def _advisory_inspection_snapshot_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> AdvisoryInspectionSnapshot:
    advisory_output = snapshot.advisory_output
    return AdvisoryInspectionSnapshot(
        read_only=True,
        record_family=snapshot.record_family,
        record_id=snapshot.record_id,
        output_kind=str(advisory_output["output_kind"]),
        status=str(advisory_output["status"]),
        cited_summary=dict(advisory_output["cited_summary"]),
        key_observations=tuple(advisory_output["key_observations"]),
        unresolved_questions=tuple(advisory_output["unresolved_questions"]),
        candidate_recommendations=tuple(advisory_output["candidate_recommendations"]),
        citations=tuple(advisory_output["citations"]),
        uncertainty_flags=tuple(advisory_output["uncertainty_flags"]),
        reviewed_context=dict(snapshot.reviewed_context),
        linked_alert_ids=snapshot.linked_alert_ids,
        linked_case_ids=snapshot.linked_case_ids,
        linked_evidence_ids=snapshot.linked_evidence_ids,
        linked_recommendation_ids=snapshot.linked_recommendation_ids,
        linked_reconciliation_ids=snapshot.linked_reconciliation_ids,
    )


def _recommendation_draft_snapshot_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> RecommendationDraftSnapshot:
    advisory_output = snapshot.advisory_output
    return RecommendationDraftSnapshot(
        read_only=True,
        record_family=snapshot.record_family,
        record_id=snapshot.record_id,
        recommendation_draft={
            "source_output_kind": advisory_output["output_kind"],
            "status": advisory_output["status"],
            "review_lifecycle_state": snapshot.record.get("lifecycle_state"),
            "cited_summary": advisory_output["cited_summary"],
            "candidate_recommendations": advisory_output["candidate_recommendations"],
            "unresolved_questions": advisory_output["unresolved_questions"],
            "citations": advisory_output["citations"],
            "uncertainty_flags": advisory_output["uncertainty_flags"],
        },
        reviewed_context=dict(snapshot.reviewed_context),
        linked_alert_ids=snapshot.linked_alert_ids,
        linked_case_ids=snapshot.linked_case_ids,
        linked_evidence_ids=snapshot.linked_evidence_ids,
        linked_recommendation_ids=snapshot.linked_recommendation_ids,
        linked_reconciliation_ids=snapshot.linked_reconciliation_ids,
    )


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


class AegisOpsControlPlaneService:
    """Minimal local runtime skeleton for the first control-plane service."""

    def __init__(
        self,
        config: RuntimeConfig,
        store: ControlPlaneStore | None = None,
    ) -> None:
        self._config = config
        self._store = store or PostgresControlPlaneStore(config.postgres_dsn)
        self._reconciliation = N8NReconciliationAdapter(config.n8n_base_url)
        self._shuffle = ShuffleActionAdapter(config.shuffle_base_url)
        self._isolated_executor = IsolatedExecutorAdapter(
            config.isolated_executor_base_url
        )

    def describe_runtime(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            service_name="aegisops-control-plane",
            bind_host=self._config.host,
            bind_port=self._config.port,
            postgres_dsn=self._store.dsn,
            persistence_mode=self._store.persistence_mode,
            opensearch_url=self._config.opensearch_url,
            n8n_base_url=self._reconciliation.base_url,
            shuffle_base_url=self._shuffle.base_url,
            isolated_executor_base_url=self._isolated_executor.base_url,
            ownership_boundary={
                "runtime_root": "control-plane/",
                "postgres_contract_root": "postgres/control-plane/",
                "native_detection_intake": "substrate-adapters/",
                "admitted_signal_model": "control-plane/analytic-signals",
                "routine_automation_substrate": "shuffle/",
                "controlled_execution_surface": "executor/isolated-executor",
            },
        )

    def persist_record(self, record: RecordT) -> RecordT:
        return self._store.save(record)

    def get_record(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        return self._store.get(record_type, record_id)

    def validate_wazuh_ingest_runtime(self) -> None:
        if self._config.wazuh_ingest_shared_secret.strip() == "":
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set "
                "before starting the live Wazuh ingest runtime"
            )
        for cidr in self._config.wazuh_ingest_trusted_proxy_cidrs:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must contain "
                    f"only valid IP networks, got: {cidr!r}"
                ) from exc
        if (
            not self._wazuh_ingest_listener_is_loopback()
            and not self._config.wazuh_ingest_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set "
                "before starting the live Wazuh ingest runtime on a non-loopback interface"
            )

    def ingest_wazuh_alert(
        self,
        *,
        raw_alert: Mapping[str, object],
        authorization_header: str | None,
        forwarded_proto: str | None,
        peer_addr: str | None,
    ) -> FindingAlertIngestResult:
        self.validate_wazuh_ingest_runtime()

        if not self._is_trusted_wazuh_ingest_peer(peer_addr):
            raise PermissionError(
                "live Wazuh ingest rejects requests that bypass the reviewed reverse proxy peer boundary"
            )

        if (forwarded_proto or "").strip().lower() != "https":
            raise PermissionError(
                "live Wazuh ingest requires the reviewed reverse proxy HTTPS boundary"
            )

        scheme, separator, supplied_secret = (authorization_header or "").partition(" ")
        if separator == "" or scheme != "Bearer" or supplied_secret.strip() == "":
            raise PermissionError(
                "live Wazuh ingest requires Authorization: Bearer <shared secret>"
            )
        if not hmac.compare_digest(
            supplied_secret.strip(),
            self._config.wazuh_ingest_shared_secret,
        ):
            raise PermissionError(
                "live Wazuh ingest bearer credential did not match the reviewed shared secret"
            )

        native_alert = self._require_mapping(raw_alert, "alert")
        source_family = self._normalize_optional_string(
            (
                self._require_mapping(
                    native_alert.get("data"),
                    "data",
                )
            ).get("source_family"),
            "data.source_family",
        )
        if source_family != "github_audit":
            raise ValueError(
                "live Wazuh ingest only admits the reviewed github_audit first live source family"
            )

        adapter = WazuhAlertAdapter()
        native_record = self._with_native_detection_admission_provenance(
            adapter.build_native_detection_record(native_alert),
            admission_kind="live",
            admission_channel="live_wazuh_webhook",
        )
        return self.ingest_native_detection_record(adapter, native_record)

    def _wazuh_ingest_listener_is_loopback(self) -> bool:
        host = self._config.host.strip()
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def _is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        if self._wazuh_ingest_listener_is_loopback():
            return True
        if peer_addr is None or peer_addr.strip() == "":
            return False
        try:
            peer_ip = ipaddress.ip_address(peer_addr)
        except ValueError:
            return False
        for cidr in self._config.wazuh_ingest_trusted_proxy_cidrs:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        return False

    def delegate_approved_action_to_shuffle(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        delegated_at = self._require_aware_datetime(delegated_at, "delegated_at")
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        delegation_issuer = self._require_non_empty_string(
            delegation_issuer,
            "delegation_issuer",
        )
        normalized_payload = self._require_mapping(approved_payload, "approved_payload")
        with self._store.transaction():
            action_request, approval_decision = self._load_approved_delegation_context(
                action_request_id=action_request_id,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                invalid_execution_surface_type_message=(
                    "approved action request is not delegated through the automation "
                    "substrate path"
                ),
                invalid_execution_surface_id_message=(
                    "approved action request is not routed to the reviewed shuffle adapter"
                ),
                delegation_label="shuffle",
            )
            approval_decision_id = approval_decision.approval_decision_id
            for existing in self._store.list(ActionExecutionRecord):
                if (
                    existing.action_request_id == action_request.action_request_id
                    and existing.execution_surface_type == "automation_substrate"
                    and existing.execution_surface_id == "shuffle"
                    and existing.idempotency_key == action_request.idempotency_key
                ):
                    return existing

            delegation_id = self._next_identifier("delegation")
            receipt = self._shuffle.dispatch_approved_action(
                delegation_id=delegation_id,
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval_decision_id,
                payload_hash=action_request.payload_hash,
                idempotency_key=action_request.idempotency_key,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
            )
            provenance: dict[str, object] = {
                "delegation_issuer": delegation_issuer,
                "evidence_ids": evidence_ids,
                "adapter": receipt.adapter,
            }
            if receipt.base_url.strip() and receipt.base_url != "<set-me>":
                provenance["adapter_base_url"] = receipt.base_url

            return self.persist_record(
                ActionExecutionRecord(
                    action_execution_id=self._next_identifier("action-execution"),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval_decision_id,
                    delegation_id=delegation_id,
                    execution_surface_type=receipt.execution_surface_type,
                    execution_surface_id=receipt.execution_surface_id,
                    execution_run_id=receipt.execution_run_id,
                    idempotency_key=action_request.idempotency_key,
                    target_scope=action_request.target_scope,
                    approved_payload=normalized_payload,
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=action_request.expires_at,
                    provenance=provenance,
                    lifecycle_state="queued",
                )
            )

    def delegate_approved_action_to_isolated_executor(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        delegated_at = self._require_aware_datetime(delegated_at, "delegated_at")
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        delegation_issuer = self._require_non_empty_string(
            delegation_issuer,
            "delegation_issuer",
        )
        normalized_payload = self._require_mapping(approved_payload, "approved_payload")
        with self._store.transaction():
            action_request, approval_decision = self._load_approved_delegation_context(
                action_request_id=action_request_id,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
                execution_surface_type="executor",
                execution_surface_id="isolated-executor",
                invalid_execution_surface_type_message=(
                    "approved action request is not delegated through the isolated "
                    "executor path"
                ),
                invalid_execution_surface_id_message=(
                    "approved action request is not routed to the reviewed isolated executor"
                ),
                delegation_label="isolated executor",
            )
            approval_decision_id = approval_decision.approval_decision_id
            for existing in self._store.list(ActionExecutionRecord):
                if (
                    existing.action_request_id == action_request.action_request_id
                    and existing.execution_surface_type == "executor"
                    and existing.execution_surface_id == "isolated-executor"
                    and existing.idempotency_key == action_request.idempotency_key
                ):
                    return existing

            delegation_id = self._next_identifier("delegation")
            receipt = self._isolated_executor.dispatch_approved_action(
                delegation_id=delegation_id,
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval_decision_id,
                payload_hash=action_request.payload_hash,
                idempotency_key=action_request.idempotency_key,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
            )
            provenance: dict[str, object] = {
                "delegation_issuer": delegation_issuer,
                "evidence_ids": evidence_ids,
                "adapter": receipt.adapter,
            }
            if receipt.base_url.strip() and receipt.base_url != "<set-me>":
                provenance["adapter_base_url"] = receipt.base_url

            return self.persist_record(
                ActionExecutionRecord(
                    action_execution_id=self._next_identifier("action-execution"),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval_decision_id,
                    delegation_id=delegation_id,
                    execution_surface_type=receipt.execution_surface_type,
                    execution_surface_id=receipt.execution_surface_id,
                    execution_run_id=receipt.execution_run_id,
                    idempotency_key=action_request.idempotency_key,
                    target_scope=action_request.target_scope,
                    approved_payload=normalized_payload,
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=action_request.expires_at,
                    provenance=provenance,
                    lifecycle_state="queued",
                )
            )

    def evaluate_action_policy(self, action_request_id: str) -> ActionRequestRecord:
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")

        normalized_policy_basis = self._normalize_action_policy_basis(
            action_request.policy_basis
        )
        policy_evaluation = self._determine_action_policy(normalized_policy_basis)
        evaluated = ActionRequestRecord(
            action_request_id=action_request.action_request_id,
            approval_decision_id=action_request.approval_decision_id,
            case_id=action_request.case_id,
            alert_id=action_request.alert_id,
            finding_id=action_request.finding_id,
            idempotency_key=action_request.idempotency_key,
            target_scope=action_request.target_scope,
            payload_hash=action_request.payload_hash,
            requested_at=action_request.requested_at,
            expires_at=action_request.expires_at,
            lifecycle_state=action_request.lifecycle_state,
            policy_basis=normalized_policy_basis,
            policy_evaluation=policy_evaluation,
        )
        return self.persist_record(evaluated)

    def inspect_records(self, record_family: str) -> RecordInspectionSnapshot:
        record_type = RECORD_TYPES_BY_FAMILY.get(record_family)
        if record_type is None:
            known_families = ", ".join(sorted(RECORD_TYPES_BY_FAMILY))
            raise ValueError(
                f"Unsupported control-plane record family {record_family!r}; "
                f"expected one of: {known_families}"
            )

        records = tuple(_record_to_dict(record) for record in self._store.list(record_type))
        return RecordInspectionSnapshot(
            read_only=True,
            record_family=record_family,
            total_records=len(records),
            records=records,
        )

    def inspect_reconciliation_status(self) -> ReconciliationStatusSnapshot:
        records = self._store.list(ReconciliationRecord)
        latest_compared_at = max(
            (record.compared_at for record in records),
            default=None,
        )
        by_lifecycle_state = dict(
            sorted(Counter(record.lifecycle_state for record in records).items())
        )
        by_ingest_disposition = dict(
            sorted(Counter(record.ingest_disposition for record in records).items())
        )
        return ReconciliationStatusSnapshot(
            read_only=True,
            total_records=len(records),
            latest_compared_at=latest_compared_at,
            by_lifecycle_state=by_lifecycle_state,
            by_ingest_disposition=by_ingest_disposition,
            records=tuple(_record_to_dict(record) for record in records),
        )

    def inspect_analyst_queue(self) -> AnalystQueueSnapshot:
        latest_reconciliation_by_alert_id: dict[str, ReconciliationRecord] = {}
        for record in self._store.list(ReconciliationRecord):
            if (
                record.alert_id is None
                or not self._reconciliation_has_detection_lineage(record)
            ):
                continue
            current = latest_reconciliation_by_alert_id.get(record.alert_id)
            if current is None or record.compared_at > current.compared_at:
                latest_reconciliation_by_alert_id[record.alert_id] = record

        active_alert_states = {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "reopened",
        }
        queue_records: list[dict[str, object]] = []
        for alert in self._store.list(AlertRecord):
            if alert.lifecycle_state not in active_alert_states:
                continue
            reconciliation = latest_reconciliation_by_alert_id.get(alert.alert_id)
            if reconciliation is None:
                continue

            source_systems = self._merge_linked_ids(
                reconciliation.subject_linkage.get("source_systems"),
                None,
            )
            substrate_detection_record_ids = self._merge_linked_ids(
                reconciliation.subject_linkage.get("substrate_detection_record_ids"),
                None,
            )
            is_wazuh_origin = "wazuh" in source_systems or any(
                detection_id.startswith("wazuh:")
                for detection_id in substrate_detection_record_ids
            )
            if not is_wazuh_origin:
                continue

            case_record = (
                self._store.get(CaseRecord, alert.case_id)
                if alert.case_id is not None
                else None
            )
            review_state = self._alert_review_state(alert)
            queue_records.append(
                {
                    "alert_id": alert.alert_id,
                    "finding_id": alert.finding_id,
                    "analytic_signal_id": alert.analytic_signal_id,
                    "case_id": alert.case_id,
                    "case_lifecycle_state": (
                        case_record.lifecycle_state if case_record is not None else None
                    ),
                    "queue_selection": "business_hours_triage",
                    "review_state": review_state,
                    "escalation_boundary": self._alert_escalation_boundary(alert),
                    "source_system": (
                        "wazuh"
                        if is_wazuh_origin
                        else (source_systems[0] if source_systems else "wazuh")
                    ),
                    "substrate_detection_record_ids": substrate_detection_record_ids,
                    "accountable_source_identities": self._merge_linked_ids(
                        reconciliation.subject_linkage.get(
                            "accountable_source_identities"
                        ),
                        None,
                    ),
                    "reviewed_context": dict(alert.reviewed_context),
                    "native_rule": reconciliation.subject_linkage.get(
                        "latest_native_rule"
                    ),
                    "evidence_ids": self._merge_linked_ids(
                        reconciliation.subject_linkage.get("evidence_ids"),
                        None,
                    ),
                    "correlation_key": reconciliation.correlation_key,
                    "first_seen_at": reconciliation.first_seen_at,
                    "last_seen_at": reconciliation.last_seen_at,
                }
            )

        queue_records.sort(
            key=lambda record: (
                record["last_seen_at"]
                or datetime.min.replace(tzinfo=timezone.utc),
                record["alert_id"],
            ),
            reverse=True,
        )
        return AnalystQueueSnapshot(
            read_only=True,
            queue_name="analyst_review",
            total_records=len(queue_records),
            records=tuple(queue_records),
        )

    def inspect_assistant_context(
        self,
        record_family: str,
        record_id: str,
    ) -> AnalystAssistantContextSnapshot:
        record_family = self._require_non_empty_string(record_family, "record_family")
        record_id = self._require_non_empty_string(record_id, "record_id")
        record_type = RECORD_TYPES_BY_FAMILY.get(record_family)
        if record_type is None:
            known_families = ", ".join(sorted(RECORD_TYPES_BY_FAMILY))
            raise ValueError(
                f"Unsupported control-plane record family {record_family!r}; "
                f"expected one of: {known_families}"
            )

        record = self._store.get(record_type, record_id)
        if record is None:
            raise LookupError(
                f"Missing {record_family} record {record_id!r} for assistant context"
            )

        linked_alert_ids = self._assistant_ids_from_value(
            getattr(record, "alert_id", None)
        )
        linked_case_ids = self._assistant_ids_from_value(getattr(record, "case_id", None))
        linked_finding_ids = self._assistant_ids_from_value(
            getattr(record, "finding_id", None)
        )
        linked_evidence_ids = self._assistant_linked_evidence_ids(record)

        if isinstance(record, (ApprovalDecisionRecord, ActionExecutionRecord)):
            action_request_id = self._require_non_empty_string(
                getattr(record, "action_request_id", None),
                "action_request_id",
            )
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if action_request is None:
                raise LookupError(
                    f"Missing action request {action_request_id!r} for assistant context"
                )
            linked_alert_ids = self._assistant_merge_ids(
                linked_alert_ids,
                action_request.alert_id,
            )
            linked_case_ids = self._assistant_merge_ids(
                linked_case_ids,
                action_request.case_id,
            )
            linked_finding_ids = self._assistant_merge_ids(
                linked_finding_ids,
                action_request.finding_id,
            )

        if isinstance(record, AnalyticSignalRecord):
            linked_alert_ids = self._assistant_merge_ids(
                linked_alert_ids,
                record.alert_ids,
            )
            linked_case_ids = self._assistant_merge_ids(
                linked_case_ids,
                record.case_ids,
            )
        elif isinstance(record, CaseRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                record.evidence_ids,
            )
        elif isinstance(record, EvidenceRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_evidence_siblings(record),
            )
        elif isinstance(record, ObservationRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                record.supporting_evidence_ids,
            )
        elif isinstance(record, ReconciliationRecord):
            linked_alert_ids = self._merge_linked_ids(
                linked_alert_ids,
                record.alert_id,
            )
            linked_alert_ids = self._assistant_merge_ids(
                linked_alert_ids,
                self._assistant_ids_from_mapping(record.subject_linkage, "alert_ids"),
            )
            (
                action_request_ids,
                approval_decision_ids,
                action_execution_ids,
                delegation_ids,
            ) = self._assistant_action_lineage_ids(record)
            for action_request_id in action_request_ids:
                action_request = self._store.get(ActionRequestRecord, action_request_id)
                if action_request is None:
                    continue
                (
                    linked_alert_ids,
                    linked_case_ids,
                    linked_finding_ids,
                ) = self._assistant_merge_action_request_linkage(
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                    action_request=action_request,
                )
            for approval_decision_id in approval_decision_ids:
                approval_decision = self._store.get(
                    ApprovalDecisionRecord,
                    approval_decision_id,
                )
                if approval_decision is None:
                    continue
                action_request = self._store.get(
                    ActionRequestRecord,
                    approval_decision.action_request_id,
                )
                if action_request is None:
                    continue
                (
                    linked_alert_ids,
                    linked_case_ids,
                    linked_finding_ids,
                ) = self._assistant_merge_action_request_linkage(
                    linked_alert_ids=linked_alert_ids,
                    linked_case_ids=linked_case_ids,
                    linked_finding_ids=linked_finding_ids,
                    action_request=action_request,
                )
            for action_execution_id in action_execution_ids:
                action_execution = self._store.get(ActionExecutionRecord, action_execution_id)
                if action_execution is None:
                    continue
                action_request = self._store.get(
                    ActionRequestRecord,
                    action_execution.action_request_id,
                )
                if action_request is not None:
                    (
                        linked_alert_ids,
                        linked_case_ids,
                        linked_finding_ids,
                    ) = self._assistant_merge_action_request_linkage(
                        linked_alert_ids=linked_alert_ids,
                        linked_case_ids=linked_case_ids,
                        linked_finding_ids=linked_finding_ids,
                        action_request=action_request,
                    )
                linked_evidence_ids = self._assistant_merge_ids(
                    linked_evidence_ids,
                    self._assistant_linked_evidence_ids(action_execution),
                )
            for delegation_id in delegation_ids:
                action_execution = self._assistant_action_execution_for_delegation_id(
                    delegation_id
                )
                if action_execution is None:
                    continue
                action_request = self._store.get(
                    ActionRequestRecord,
                    action_execution.action_request_id,
                )
                if action_request is not None:
                    (
                        linked_alert_ids,
                        linked_case_ids,
                        linked_finding_ids,
                    ) = self._assistant_merge_action_request_linkage(
                        linked_alert_ids=linked_alert_ids,
                        linked_case_ids=linked_case_ids,
                        linked_finding_ids=linked_finding_ids,
                        action_request=action_request,
                    )
                linked_evidence_ids = self._assistant_merge_ids(
                    linked_evidence_ids,
                    self._assistant_linked_evidence_ids(action_execution),
                )
            subject_analytic_signal_ids = self._assistant_ids_from_mapping(
                record.subject_linkage,
                "analytic_signal_ids",
            )
            for analytic_signal_id in subject_analytic_signal_ids:
                signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
                if signal is None:
                    continue
                linked_alert_ids = self._assistant_merge_ids(
                    linked_alert_ids,
                    signal.alert_ids,
                )
                linked_case_ids = self._assistant_merge_ids(
                    linked_case_ids,
                    signal.case_ids,
                )
                linked_finding_ids = self._assistant_merge_ids(
                    linked_finding_ids,
                    signal.finding_id,
                )
            for alert_id in linked_alert_ids:
                alert = self._store.get(AlertRecord, alert_id)
                if alert is None:
                    continue
                linked_case_ids = self._assistant_merge_ids(
                    linked_case_ids,
                    alert.case_id,
                )
                linked_finding_ids = self._assistant_merge_ids(
                    linked_finding_ids,
                    alert.finding_id,
                )
            linked_case_ids = self._assistant_merge_ids(
                linked_case_ids,
                self._assistant_ids_from_mapping(record.subject_linkage, "case_ids"),
            )
            linked_finding_ids = self._assistant_merge_ids(
                linked_finding_ids,
                self._assistant_ids_from_mapping(record.subject_linkage, "finding_ids"),
            )
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "evidence_ids",
                ),
            )
        elif isinstance(record, HuntRunRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(record.output_linkage, "evidence_ids"),
            )

        linked_ai_trace_records = self._assistant_ai_trace_records_for_context(record)
        for ai_trace_record in linked_ai_trace_records:
            linked_alert_ids = self._assistant_merge_ids(
                linked_alert_ids,
                self._assistant_ids_from_mapping(ai_trace_record.subject_linkage, "alert_ids"),
            )
            linked_case_ids = self._assistant_merge_ids(
                linked_case_ids,
                self._assistant_ids_from_mapping(ai_trace_record.subject_linkage, "case_ids"),
            )
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ai_trace_evidence_ids(ai_trace_record),
            )

        linked_evidence_records = self._assistant_evidence_records_for_context(
            alert_ids=linked_alert_ids,
            case_ids=linked_case_ids,
            evidence_ids=linked_evidence_ids,
            exclude_evidence_id=(
                record.evidence_id if isinstance(record, EvidenceRecord) else None
            ),
        )
        linked_evidence_ids = self._assistant_merge_ids(
            linked_evidence_ids,
            tuple(evidence.evidence_id for evidence in linked_evidence_records),
        )
        for evidence in linked_evidence_records:
            linked_alert_ids = self._assistant_merge_ids(
                linked_alert_ids,
                evidence.alert_id,
            )
            linked_case_ids = self._assistant_merge_ids(
                linked_case_ids,
                evidence.case_id,
            )

        linked_recommendation_records = self._assistant_recommendation_records_for_context(
            record=record,
            alert_ids=linked_alert_ids,
            case_ids=linked_case_ids,
            ai_trace_records=linked_ai_trace_records,
            exclude_recommendation_id=(
                record.record_id if isinstance(record, RecommendationRecord) else None
            ),
        )
        linked_recommendation_ids = tuple(
            recommendation.recommendation_id
            for recommendation in linked_recommendation_records
        )
        has_direct_recommendation_lineage = isinstance(record, RecommendationRecord) and (
            record.alert_id is not None or record.case_id is not None
        )
        if not has_direct_recommendation_lineage:
            for recommendation in linked_recommendation_records:
                linked_alert_ids = self._assistant_merge_ids(
                    linked_alert_ids,
                    recommendation.alert_id,
                )
                linked_case_ids = self._assistant_merge_ids(
                    linked_case_ids,
                    recommendation.case_id,
                )

        linked_alert_records_list: list[dict[str, object]] = []
        for alert_id in linked_alert_ids:
            alert = self._store.get(AlertRecord, alert_id)
            if alert is not None:
                linked_alert_records_list.append(_record_to_dict(alert))
        linked_alert_records = tuple(linked_alert_records_list)

        linked_case_records_list: list[dict[str, object]] = []
        for case_id in linked_case_ids:
            case = self._store.get(CaseRecord, case_id)
            if case is not None:
                linked_case_records_list.append(_record_to_dict(case))
        linked_case_records = tuple(linked_case_records_list)

        linked_reconciliation_records = (
            self._assistant_reconciliation_records_for_context(
                record=record,
                alert_ids=linked_alert_ids,
                case_ids=linked_case_ids,
                finding_ids=linked_finding_ids,
                evidence_ids=linked_evidence_ids,
                exclude_reconciliation_id=(
                    record.record_id if isinstance(record, ReconciliationRecord) else None
                ),
            )
        )
        linked_reconciliation_ids = tuple(
            reconciliation.reconciliation_id
            for reconciliation in linked_reconciliation_records
        )

        reviewed_context = {}
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
                reviewed_context = _merge_reviewed_context(
                    reviewed_context,
                    alert.get("reviewed_context"),
                )
            for case in linked_case_records:
                reviewed_context = _merge_reviewed_context(
                    reviewed_context,
                    case.get("reviewed_context"),
                )

        record_payload = _record_to_dict(record)
        linked_recommendation_payloads = tuple(
            _record_to_dict(recommendation)
            for recommendation in linked_recommendation_records
        )

        return AnalystAssistantContextSnapshot(
            read_only=True,
            record_family=record_family,
            record_id=record_id,
            record=record_payload,
            advisory_output=_build_assistant_advisory_output(
                record_family=record_family,
                record_id=record_id,
                record=record_payload,
                reviewed_context=reviewed_context,
                linked_alert_ids=linked_alert_ids,
                linked_case_ids=linked_case_ids,
                linked_evidence_ids=linked_evidence_ids,
                linked_recommendation_ids=linked_recommendation_ids,
                linked_alert_records=linked_alert_records,
                linked_case_records=linked_case_records,
                linked_recommendation_records=linked_recommendation_payloads,
            ),
            reviewed_context=reviewed_context,
            linked_alert_ids=linked_alert_ids,
            linked_case_ids=linked_case_ids,
            linked_evidence_ids=linked_evidence_ids,
            linked_recommendation_ids=linked_recommendation_ids,
            linked_reconciliation_ids=linked_reconciliation_ids,
            linked_alert_records=linked_alert_records,
            linked_case_records=linked_case_records,
            linked_evidence_records=tuple(
                _record_to_dict(evidence) for evidence in linked_evidence_records
            ),
            linked_recommendation_records=linked_recommendation_payloads,
            linked_reconciliation_records=tuple(
                _record_to_dict(reconciliation)
                for reconciliation in linked_reconciliation_records
            ),
        )

    def inspect_advisory_output(
        self,
        record_family: str,
        record_id: str,
    ) -> AdvisoryInspectionSnapshot:
        context_snapshot = self.inspect_assistant_context(record_family, record_id)
        return _advisory_inspection_snapshot_from_context(context_snapshot)

    def render_recommendation_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationDraftSnapshot:
        context_snapshot = self.inspect_assistant_context(record_family, record_id)
        return _recommendation_draft_snapshot_from_context(context_snapshot)

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        record_family = self._require_non_empty_string(record_family, "record_family")
        record_id = self._require_non_empty_string(record_id, "record_id")
        if record_family not in {"recommendation", "ai_trace"}:
            raise ValueError(
                "assistant advisory drafts may only be attached to "
                "'recommendation' or 'ai_trace' records"
            )

        record_type = RECORD_TYPES_BY_FAMILY[record_family]
        record = self._store.get(record_type, record_id)
        if record is None:
            raise LookupError(
                f"Missing {record_family} record {record_id!r} for advisory draft attachment"
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
        return self.persist_record(
            replace(record, assistant_advisory_draft=attached_draft)
        )

    def _reconciliation_has_detection_lineage(
        self, record: ReconciliationRecord
    ) -> bool:
        return any(
            (
                record.analytic_signal_id is not None,
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("analytic_signal_ids"),
                        None,
                    )
                ),
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("substrate_detection_record_ids"),
                        None,
                    )
                ),
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("source_systems"),
                        None,
                    )
                ),
            )
        )

    @staticmethod
    def _assistant_ids_from_value(value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(item for item in value if isinstance(item, str))
        return ()

    @staticmethod
    def _assistant_ids_from_mapping(
        mapping: Mapping[str, object],
        key: str,
    ) -> tuple[str, ...]:
        return AegisOpsControlPlaneService._assistant_ids_from_value(mapping.get(key))

    @staticmethod
    def _assistant_merge_ids(
        existing_values: object,
        incoming_values: object,
    ) -> tuple[str, ...]:
        merged = AegisOpsControlPlaneService._merge_linked_ids(existing_values, None)
        if isinstance(incoming_values, (list, tuple)):
            for value in incoming_values:
                merged = AegisOpsControlPlaneService._merge_linked_ids(merged, value)
        else:
            merged = AegisOpsControlPlaneService._merge_linked_ids(
                merged,
                incoming_values if isinstance(incoming_values, str) else None,
            )
        return merged

    def _assistant_action_lineage_ids(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        action_request_ids = self._assistant_ids_from_value(
            getattr(record, "action_request_id", None)
        )
        approval_decision_ids = self._assistant_ids_from_value(
            getattr(record, "approval_decision_id", None)
        )
        action_execution_ids = self._assistant_ids_from_value(
            getattr(record, "action_execution_id", None)
        )
        delegation_ids = self._assistant_ids_from_value(getattr(record, "delegation_id", None))
        if isinstance(record, ReconciliationRecord):
            action_request_ids = self._assistant_merge_ids(
                action_request_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "action_request_ids",
                ),
            )
            approval_decision_ids = self._assistant_merge_ids(
                approval_decision_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "approval_decision_ids",
                ),
            )
            action_execution_ids = self._assistant_merge_ids(
                action_execution_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "action_execution_ids",
                ),
            )
            delegation_ids = self._assistant_merge_ids(
                delegation_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "delegation_ids",
                ),
            )
        return (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        )

    def _assistant_merge_action_request_linkage(
        self,
        *,
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
        action_request: ActionRequestRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return (
            self._assistant_merge_ids(linked_alert_ids, action_request.alert_id),
            self._assistant_merge_ids(linked_case_ids, action_request.case_id),
            self._assistant_merge_ids(linked_finding_ids, action_request.finding_id),
        )

    def _assistant_action_execution_for_delegation_id(
        self,
        delegation_id: str,
    ) -> ActionExecutionRecord | None:
        for execution in self._store.list(ActionExecutionRecord):
            if execution.delegation_id == delegation_id:
                return execution
        return None

    def _assistant_ai_trace_records_for_context(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[AITraceRecord, ...]:
        records: list[AITraceRecord] = []
        seen_trace_ids: set[str] = set()

        def add_trace(trace: AITraceRecord | None) -> None:
            if trace is None or trace.ai_trace_id in seen_trace_ids:
                return
            seen_trace_ids.add(trace.ai_trace_id)
            records.append(trace)

        ai_trace_id = getattr(record, "ai_trace_id", None)
        if ai_trace_id is not None:
            add_trace(self._store.get(AITraceRecord, ai_trace_id))
        if isinstance(record, AITraceRecord):
            add_trace(record)

        record_recommendation_id = getattr(record, "recommendation_id", None)
        if record_recommendation_id is not None:
            for trace in self._store.list(AITraceRecord):
                if trace.ai_trace_id in seen_trace_ids:
                    continue
                if record_recommendation_id in self._assistant_ids_from_mapping(
                    trace.subject_linkage,
                    "recommendation_ids",
                ):
                    add_trace(trace)

        return tuple(records)

    def _assistant_ai_trace_evidence_ids(
        self,
        ai_trace_record: AITraceRecord,
    ) -> tuple[str, ...]:
        linked_evidence_ids = self._assistant_ids_from_mapping(
            ai_trace_record.subject_linkage,
            "evidence_ids",
        )
        linked_evidence_ids = self._assistant_merge_ids(
            linked_evidence_ids,
            ai_trace_record.material_input_refs,
        )
        return tuple(
            evidence_id
            for evidence_id in linked_evidence_ids
            if self._store.get(EvidenceRecord, evidence_id) is not None
        )

    def _assistant_linked_evidence_ids(self, record: ControlPlaneRecord) -> tuple[str, ...]:
        linked_evidence_ids = self._assistant_ids_from_value(getattr(record, "evidence_ids", ()))
        linked_evidence_ids = self._assistant_merge_ids(
            linked_evidence_ids,
            getattr(record, "supporting_evidence_ids", ()),
        )
        if isinstance(record, ActionExecutionRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(record.provenance, "evidence_ids"),
            )
        if isinstance(record, ReconciliationRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(record.subject_linkage, "evidence_ids"),
            )
        for ai_trace_record in self._assistant_ai_trace_records_for_context(record):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ai_trace_evidence_ids(ai_trace_record),
            )
        return linked_evidence_ids

    def _assistant_evidence_siblings(self, record: EvidenceRecord) -> tuple[str, ...]:
        evidence_records = self._assistant_evidence_records_for_context(
            alert_ids=self._assistant_ids_from_value(record.alert_id),
            case_ids=self._assistant_ids_from_value(record.case_id),
            evidence_ids=(),
            exclude_evidence_id=record.evidence_id,
        )
        return tuple(evidence.evidence_id for evidence in evidence_records)

    def _assistant_evidence_records_for_context(
        self,
        *,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_evidence_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        records: list[EvidenceRecord] = []
        seen_ids: set[str] = set()
        for evidence_id in evidence_ids:
            evidence = self._store.get(EvidenceRecord, evidence_id)
            if evidence is None:
                continue
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            seen_ids.add(evidence.evidence_id)
            records.append(evidence)
        for evidence in self._store.list(EvidenceRecord):
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            if evidence.alert_id in alert_ids or (
                evidence.case_id is not None and evidence.case_id in case_ids
            ):
                seen_ids.add(evidence.evidence_id)
                records.append(evidence)
        records.sort(key=lambda evidence: evidence.evidence_id)
        return tuple(records)

    def _assistant_recommendation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        ai_trace_records: tuple[AITraceRecord, ...],
        exclude_recommendation_id: str | None,
    ) -> tuple[RecommendationRecord, ...]:
        records: list[RecommendationRecord] = []
        lead_id = getattr(record, "lead_id", None)
        hunt_run_id = getattr(record, "hunt_run_id", None)
        ai_trace_id = getattr(record, "ai_trace_id", None)
        ai_trace_recommendation_ids: set[str] = set()
        for ai_trace_record in ai_trace_records:
            ai_trace_recommendation_ids.update(
                self._assistant_ids_from_mapping(
                    ai_trace_record.subject_linkage,
                    "recommendation_ids",
                )
            )
        for recommendation in self._store.list(RecommendationRecord):
            if (
                exclude_recommendation_id is not None
                and recommendation.recommendation_id == exclude_recommendation_id
            ):
                continue
            if recommendation.alert_id in alert_ids:
                records.append(recommendation)
                continue
            if recommendation.case_id is not None and recommendation.case_id in case_ids:
                records.append(recommendation)
                continue
            if lead_id is not None and recommendation.lead_id == lead_id:
                records.append(recommendation)
                continue
            if hunt_run_id is not None and recommendation.hunt_run_id == hunt_run_id:
                records.append(recommendation)
                continue
            if ai_trace_id is not None and recommendation.ai_trace_id == ai_trace_id:
                records.append(recommendation)
                continue
            if recommendation.recommendation_id in ai_trace_recommendation_ids:
                records.append(recommendation)
        records.sort(key=lambda recommendation: recommendation.recommendation_id)
        return tuple(records)

    def _assistant_reconciliation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        finding_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_reconciliation_id: str | None,
    ) -> tuple[ReconciliationRecord, ...]:
        records: list[ReconciliationRecord] = []
        analytic_signal_id = getattr(record, "analytic_signal_id", None)
        finding_id = getattr(record, "finding_id", None)
        (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        ) = self._assistant_action_lineage_ids(record)
        linked_finding_ids = set(finding_ids)
        for reconciliation in self._store.list(ReconciliationRecord):
            if (
                exclude_reconciliation_id is not None
                and reconciliation.reconciliation_id == exclude_reconciliation_id
            ):
                continue
            subject_action_request_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            )
            if any(
                action_request_id in subject_action_request_ids
                for action_request_id in action_request_ids
            ):
                records.append(reconciliation)
                continue
            subject_approval_decision_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            )
            if any(
                approval_decision_id in subject_approval_decision_ids
                for approval_decision_id in approval_decision_ids
            ):
                records.append(reconciliation)
                continue
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            if any(
                action_execution_id in subject_action_execution_ids
                for action_execution_id in action_execution_ids
            ):
                records.append(reconciliation)
                continue
            subject_delegation_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            )
            if any(
                delegation_id in subject_delegation_ids
                for delegation_id in delegation_ids
            ):
                records.append(reconciliation)
                continue
            if reconciliation.alert_id is not None and reconciliation.alert_id in alert_ids:
                records.append(reconciliation)
                continue
            if (
                analytic_signal_id is not None
                and reconciliation.analytic_signal_id == analytic_signal_id
            ):
                records.append(reconciliation)
                continue
            subject_alert_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "alert_ids",
            )
            if any(alert_id in subject_alert_ids for alert_id in alert_ids):
                records.append(reconciliation)
                continue
            subject_analytic_signal_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "analytic_signal_ids",
            )
            if (
                analytic_signal_id is not None
                and analytic_signal_id in subject_analytic_signal_ids
            ):
                records.append(reconciliation)
                continue
            if finding_id is not None and reconciliation.finding_id == finding_id:
                records.append(reconciliation)
                continue
            if (
                reconciliation.finding_id is not None
                and reconciliation.finding_id in linked_finding_ids
            ):
                records.append(reconciliation)
                continue
            subject_finding_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "finding_ids",
            )
            if any(finding_id in subject_finding_ids for finding_id in linked_finding_ids):
                records.append(reconciliation)
                continue
            subject_case_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "case_ids",
            )
            if any(case_id in subject_case_ids for case_id in case_ids):
                records.append(reconciliation)
                continue
            subject_evidence_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "evidence_ids",
            )
            if any(evidence_id in subject_evidence_ids for evidence_id in evidence_ids):
                records.append(reconciliation)
        records.sort(key=lambda reconciliation: reconciliation.reconciliation_id)
        return tuple(records)

    @staticmethod
    def _require_aware_datetime(value: object, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return value

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _normalize_optional_string(
        value: object,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string when provided")
        if not value.strip():
            return None
        return value

    def ingest_finding_alert(
        self,
        *,
        finding_id: str,
        analytic_signal_id: str | None,
        substrate_detection_record_id: str | None = None,
        correlation_key: str,
        first_seen_at: datetime,
        last_seen_at: datetime,
        materially_new_work: bool = False,
        reviewed_context: Mapping[str, object] | None = None,
    ) -> FindingAlertIngestResult:
        return self._ingest_analytic_signal_admission(
            AnalyticSignalAdmission(
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                substrate_detection_record_id=substrate_detection_record_id,
                correlation_key=correlation_key,
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                materially_new_work=materially_new_work,
                reviewed_context=reviewed_context or {},
            )
        )

    def promote_alert_to_case(
        self,
        alert_id: str,
        *,
        case_id: str | None = None,
        case_lifecycle_state: str = "open",
    ) -> CaseRecord:
        alert_id = self._require_non_empty_string(alert_id, "alert_id")
        requested_case_id = self._normalize_optional_string(case_id, "case_id")
        case_lifecycle_state = self._require_non_empty_string(
            case_lifecycle_state,
            "case_lifecycle_state",
        )
        with self._store.transaction():
            alert = self._store.get(AlertRecord, alert_id)
            if alert is None:
                raise LookupError(f"Missing alert {alert_id!r}")

            if alert.case_id is not None:
                resolved_case_id = alert.case_id
                if (
                    requested_case_id is not None
                    and requested_case_id != resolved_case_id
                ):
                    raise ValueError(
                        f"Alert {alert_id!r} is already linked to case {resolved_case_id!r}"
                    )
            else:
                resolved_case_id = requested_case_id or self._next_identifier("case")

            evidence_records = self._list_alert_evidence_records(
                alert_id=alert.alert_id,
                case_id=resolved_case_id,
            )
            if not evidence_records:
                raise ValueError(
                    f"Alert {alert_id!r} has no linked evidence to promote into a case"
                )

            merged_evidence_ids: tuple[str, ...] = ()
            for evidence in evidence_records:
                merged_evidence_ids = self._merge_linked_ids(
                    merged_evidence_ids,
                    evidence.evidence_id,
                )
                updated_lifecycle_state = (
                    "linked"
                    if evidence.lifecycle_state == "collected"
                    else evidence.lifecycle_state
                )
                if (
                    evidence.case_id == resolved_case_id
                    and updated_lifecycle_state == evidence.lifecycle_state
                ):
                    continue
                self.persist_record(
                    EvidenceRecord(
                        evidence_id=evidence.evidence_id,
                        source_record_id=evidence.source_record_id,
                        alert_id=evidence.alert_id,
                        case_id=resolved_case_id,
                        source_system=evidence.source_system,
                        collector_identity=evidence.collector_identity,
                        acquired_at=evidence.acquired_at,
                        derivation_relationship=evidence.derivation_relationship,
                        lifecycle_state=updated_lifecycle_state,
                    )
                )

            existing_case = self._store.get(CaseRecord, resolved_case_id)
            if existing_case is not None:
                if (
                    existing_case.alert_id is not None
                    and existing_case.alert_id != alert.alert_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to alert {existing_case.alert_id!r}"
                    )
                if (
                    existing_case.finding_id is not None
                    and existing_case.finding_id != alert.finding_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to finding {existing_case.finding_id!r}"
                    )
            merged_case_evidence_ids = self._merge_linked_ids(
                existing_case.evidence_ids if existing_case is not None else (),
                None,
            )
            for evidence_id in merged_evidence_ids:
                merged_case_evidence_ids = self._merge_linked_ids(
                    merged_case_evidence_ids,
                    evidence_id,
                )

            promoted_case = self.persist_record(
                CaseRecord(
                    case_id=resolved_case_id,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    lifecycle_state=(
                        existing_case.lifecycle_state
                        if existing_case is not None
                        else case_lifecycle_state
                    ),
                    reviewed_context=_merge_reviewed_context(
                        existing_case.reviewed_context if existing_case is not None else {},
                        alert.reviewed_context,
                    ),
                )
            )
            promoted_alert = self.persist_record(
                AlertRecord(
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    analytic_signal_id=alert.analytic_signal_id,
                    case_id=promoted_case.case_id,
                    lifecycle_state="escalated_to_case",
                    reviewed_context=alert.reviewed_context,
                )
            )
            if promoted_alert.analytic_signal_id is not None:
                self._link_case_to_analytic_signals(
                    (promoted_alert.analytic_signal_id,),
                    promoted_case.case_id,
                )
            self._link_case_to_alert_reconciliations(
                alert_id=promoted_alert.alert_id,
                case_id=promoted_case.case_id,
                evidence_ids=merged_evidence_ids,
            )
            return promoted_case

    def ingest_native_detection_record(
        self,
        adapter: NativeDetectionRecordAdapter,
        record: NativeDetectionRecord,
    ) -> FindingAlertIngestResult:
        record = self._with_native_detection_admission_provenance(
            record,
            admission_kind="replay",
            admission_channel="fixture_replay",
        )
        adapter_substrate_key = self._require_non_empty_string(
            adapter.substrate_key,
            "adapter.substrate_key",
        )
        record_substrate_key = self._require_non_empty_string(
            record.substrate_key,
            "record.substrate_key",
        )
        if record_substrate_key != adapter_substrate_key:
            raise ValueError(
                "native detection record substrate does not match adapter boundary "
                f"({record_substrate_key!r} != {adapter_substrate_key!r})"
            )
        admission = adapter.build_analytic_signal_admission(record)
        admission_provenance = _normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            admission = AnalyticSignalAdmission(
                finding_id=admission.finding_id,
                analytic_signal_id=admission.analytic_signal_id,
                substrate_detection_record_id=admission.substrate_detection_record_id,
                correlation_key=admission.correlation_key,
                first_seen_at=admission.first_seen_at,
                last_seen_at=admission.last_seen_at,
                materially_new_work=admission.materially_new_work,
                reviewed_context=_merge_reviewed_context(
                    admission.reviewed_context,
                    {"provenance": admission_provenance},
                ),
            )
        raw_substrate_detection_record_id = self._require_non_empty_string(
            admission.substrate_detection_record_id or record.native_record_id,
            "substrate_detection_record_id/native_record_id",
        )
        substrate_detection_record_id = self._normalize_substrate_detection_record_id(
            record_substrate_key,
            raw_substrate_detection_record_id,
        )
        admission = AnalyticSignalAdmission(
            finding_id=admission.finding_id,
            analytic_signal_id=admission.analytic_signal_id,
            substrate_detection_record_id=substrate_detection_record_id,
            correlation_key=admission.correlation_key,
            first_seen_at=admission.first_seen_at,
            last_seen_at=admission.last_seen_at,
            materially_new_work=admission.materially_new_work,
            reviewed_context=admission.reviewed_context,
        )
        with self._store.transaction():
            result = self._ingest_analytic_signal_admission(admission)
            return self._attach_native_detection_context(
                record=record,
                ingest_result=result,
                substrate_detection_record_id=substrate_detection_record_id,
            )

    def _ingest_analytic_signal_admission(
        self,
        admission: AnalyticSignalAdmission,
    ) -> FindingAlertIngestResult:
        finding_id = self._require_non_empty_string(
            admission.finding_id,
            "finding_id",
        )
        analytic_signal_id = self._normalize_optional_string(
            admission.analytic_signal_id,
            "analytic_signal_id",
        )
        substrate_detection_record_id = self._normalize_optional_string(
            admission.substrate_detection_record_id,
            "substrate_detection_record_id",
        )
        correlation_key = self._require_non_empty_string(
            admission.correlation_key,
            "correlation_key",
        )
        first_seen_at = self._require_aware_datetime(
            admission.first_seen_at,
            "first_seen_at",
        )
        last_seen_at = self._require_aware_datetime(
            admission.last_seen_at,
            "last_seen_at",
        )
        if last_seen_at < first_seen_at:
            raise ValueError(
                "last_seen_at must be greater than or equal to first_seen_at"
            )
        materially_new_work = admission.materially_new_work
        reviewed_context = _merge_reviewed_context({}, admission.reviewed_context)

        existing_reconciliations = [
            record
            for record in self._store.list(ReconciliationRecord)
            if record.correlation_key == correlation_key and record.alert_id is not None
        ]
        latest_reconciliation = max(
            existing_reconciliations,
            key=lambda record: record.compared_at,
            default=None,
        )
        analytic_signal_id = self._resolve_analytic_signal_id(
            analytic_signal_id=analytic_signal_id,
            finding_id=finding_id,
            correlation_key=correlation_key,
            substrate_detection_record_id=substrate_detection_record_id,
            latest_reconciliation=latest_reconciliation,
        )

        if latest_reconciliation is None:
            alert = self.persist_record(
                AlertRecord(
                    alert_id=self._next_identifier("alert"),
                    finding_id=finding_id,
                    analytic_signal_id=analytic_signal_id,
                    case_id=None,
                    lifecycle_state="new",
                    reviewed_context=reviewed_context,
                )
            )
            disposition = "created"
            linked_finding_ids = (finding_id,)
            linked_signal_ids = (
                (analytic_signal_id,) if analytic_signal_id is not None else tuple()
            )
            linked_substrate_detection_ids = self._merge_linked_ids(
                (),
                substrate_detection_record_id,
            )
            linked_case_ids = self._merge_linked_ids((), alert.case_id)
            persisted_first_seen = first_seen_at
            persisted_last_seen = last_seen_at
        else:
            alert = self._store.get(AlertRecord, latest_reconciliation.alert_id)
            if alert is None:
                raise LookupError(
                    f"Missing alert {latest_reconciliation.alert_id!r} for correlation key {correlation_key!r}"
                )
            merged_reviewed_context = _merge_reviewed_context(
                alert.reviewed_context,
                admission.reviewed_context,
            )
            existing_finding_ids = latest_reconciliation.subject_linkage.get("finding_ids")
            existing_signal_ids = latest_reconciliation.subject_linkage.get(
                "analytic_signal_ids"
            )
            existing_substrate_detection_ids = latest_reconciliation.subject_linkage.get(
                "substrate_detection_record_ids"
            )
            existing_case_ids = latest_reconciliation.subject_linkage.get("case_ids")
            linked_finding_ids = self._merge_linked_ids(
                existing_finding_ids,
                finding_id,
            )
            linked_signal_ids = self._merge_linked_ids(
                existing_signal_ids,
                analytic_signal_id,
            )
            linked_substrate_detection_ids = self._merge_linked_ids(
                existing_substrate_detection_ids,
                substrate_detection_record_id,
            )
            linked_case_ids = self._merge_linked_ids(
                existing_case_ids,
                alert.case_id,
            )
            persisted_first_seen = min(
                latest_reconciliation.first_seen_at or first_seen_at,
                first_seen_at,
            )
            persisted_last_seen = max(
                latest_reconciliation.last_seen_at or last_seen_at,
                last_seen_at,
            )
            already_linked = (
                self._linked_id_exists(existing_finding_ids, finding_id)
                and (
                    analytic_signal_id is None
                    or self._linked_id_exists(existing_signal_ids, analytic_signal_id)
                )
                and (
                    substrate_detection_record_id is None
                    or self._linked_id_exists(
                        existing_substrate_detection_ids,
                        substrate_detection_record_id,
                    )
                )
            )
            if materially_new_work:
                alert = self.persist_record(
                    AlertRecord(
                        alert_id=alert.alert_id,
                        finding_id=finding_id,
                        analytic_signal_id=analytic_signal_id,
                        case_id=alert.case_id,
                        lifecycle_state=alert.lifecycle_state,
                        reviewed_context=merged_reviewed_context,
                    )
                )
                disposition = "updated"
            elif merged_reviewed_context != alert.reviewed_context:
                alert = self.persist_record(
                    AlertRecord(
                        alert_id=alert.alert_id,
                        finding_id=alert.finding_id,
                        analytic_signal_id=alert.analytic_signal_id,
                        case_id=alert.case_id,
                        lifecycle_state=alert.lifecycle_state,
                        reviewed_context=merged_reviewed_context,
                    )
                )
                disposition = "updated"
            elif already_linked:
                disposition = "deduplicated"
            else:
                disposition = "restated"

            if alert.case_id is not None:
                existing_case = self._store.get(CaseRecord, alert.case_id)
                if existing_case is not None:
                    merged_case_reviewed_context = _merge_reviewed_context(
                        existing_case.reviewed_context,
                        alert.reviewed_context,
                    )
                    if merged_case_reviewed_context != existing_case.reviewed_context:
                        self.persist_record(
                            CaseRecord(
                                case_id=existing_case.case_id,
                                alert_id=existing_case.alert_id,
                                finding_id=existing_case.finding_id,
                                evidence_ids=existing_case.evidence_ids,
                                lifecycle_state=existing_case.lifecycle_state,
                                reviewed_context=merged_case_reviewed_context,
                            )
                        )

        if analytic_signal_id is not None:
            existing_signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
            signal_reviewed_context = _merge_reviewed_context(
                alert.reviewed_context,
                admission.reviewed_context,
            )
            signal_alert_ids = self._merge_linked_ids(
                existing_signal.alert_ids if existing_signal is not None else (),
                alert.alert_id,
            )
            signal_case_ids = self._merge_linked_ids(
                existing_signal.case_ids if existing_signal is not None else (),
                alert.case_id,
            )
            signal_first_seen = first_seen_at
            if existing_signal is not None and existing_signal.first_seen_at is not None:
                signal_first_seen = min(existing_signal.first_seen_at, first_seen_at)
            signal_last_seen = last_seen_at
            if existing_signal is not None and existing_signal.last_seen_at is not None:
                signal_last_seen = max(existing_signal.last_seen_at, last_seen_at)
            self.persist_record(
                AnalyticSignalRecord(
                    analytic_signal_id=analytic_signal_id,
                    substrate_detection_record_id=(
                        substrate_detection_record_id
                        if substrate_detection_record_id is not None
                        else (
                            existing_signal.substrate_detection_record_id
                            if existing_signal is not None
                            else None
                        )
                    ),
                    finding_id=finding_id,
                    alert_ids=signal_alert_ids,
                    case_ids=signal_case_ids,
                    correlation_key=correlation_key,
                    first_seen_at=signal_first_seen,
                    last_seen_at=signal_last_seen,
                    lifecycle_state="active",
                    reviewed_context=signal_reviewed_context,
                )
            )

        self._link_case_to_analytic_signals(linked_signal_ids, alert.case_id)

        reconciliation = self.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._next_identifier("reconciliation"),
                subject_linkage={
                    "alert_ids": (alert.alert_id,),
                    "case_ids": linked_case_ids,
                    "substrate_detection_record_ids": linked_substrate_detection_ids,
                    "finding_ids": linked_finding_ids,
                    "analytic_signal_ids": linked_signal_ids,
                },
                alert_id=alert.alert_id,
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=correlation_key,
                first_seen_at=persisted_first_seen,
                last_seen_at=persisted_last_seen,
                ingest_disposition=disposition,
                mismatch_summary=f"{disposition} upstream analytic signal into alert lifecycle",
                compared_at=datetime.now(timezone.utc),
                lifecycle_state="matched",
            )
        )

        return FindingAlertIngestResult(
            alert=alert,
            reconciliation=reconciliation,
            disposition=disposition,
        )

    def _attach_native_detection_context(
        self,
        *,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        substrate_detection_record_id: str,
    ) -> FindingAlertIngestResult:
        source_system = self._normalize_optional_string(
            record.metadata.get("source_system"),
            "metadata.source_system",
        ) or record.substrate_key
        evidence_id = f"evidence-{uuid.uuid5(uuid.NAMESPACE_URL, substrate_detection_record_id)}"
        case_id = ingest_result.alert.case_id
        evidence = self.persist_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                source_record_id=substrate_detection_record_id,
                alert_id=ingest_result.alert.alert_id,
                case_id=case_id,
                source_system=source_system,
                collector_identity=f"{record.substrate_key}-native-detection-adapter",
                acquired_at=self._require_aware_datetime(
                    record.first_seen_at,
                    "record.first_seen_at",
                ),
                derivation_relationship="native_detection_record",
                lifecycle_state="linked" if case_id is not None else "collected",
            )
        )

        if case_id is not None:
            existing_case = self._store.get(CaseRecord, case_id)
            if existing_case is not None:
                merged_case_evidence_ids = self._merge_linked_ids(
                    existing_case.evidence_ids,
                    evidence.evidence_id,
                )
                merged_case_reviewed_context = _merge_reviewed_context(
                    existing_case.reviewed_context,
                    ingest_result.alert.reviewed_context,
                )
                if (
                    merged_case_evidence_ids != existing_case.evidence_ids
                    or merged_case_reviewed_context != existing_case.reviewed_context
                ):
                    self.persist_record(
                        CaseRecord(
                            case_id=existing_case.case_id,
                            alert_id=existing_case.alert_id,
                            finding_id=existing_case.finding_id,
                            evidence_ids=merged_case_evidence_ids,
                            lifecycle_state=existing_case.lifecycle_state,
                            reviewed_context=merged_case_reviewed_context,
                        )
                    )

        subject_linkage = dict(ingest_result.reconciliation.subject_linkage)
        subject_linkage["evidence_ids"] = self._merge_linked_ids(
            subject_linkage.get("evidence_ids"),
            evidence.evidence_id,
        )
        subject_linkage["source_systems"] = self._merge_linked_ids(
            subject_linkage.get("source_systems"),
            source_system,
        )

        source_provenance = record.metadata.get("source_provenance")
        if isinstance(source_provenance, Mapping):
            accountable_source_identity = self._normalize_optional_string(
                source_provenance.get("accountable_source_identity"),
                "metadata.source_provenance.accountable_source_identity",
            )
            if accountable_source_identity is not None:
                subject_linkage["accountable_source_identities"] = (
                    self._merge_linked_ids(
                        subject_linkage.get("accountable_source_identities"),
                        accountable_source_identity,
                    )
                )

        native_rule = record.metadata.get("native_rule")
        if isinstance(native_rule, Mapping):
            native_rule_id = self._normalize_optional_string(
                native_rule.get("id"),
                "metadata.native_rule.id",
            )
            native_rule_description = self._normalize_optional_string(
                native_rule.get("description"),
                "metadata.native_rule.description",
            )
            rule_level = native_rule.get("level")
            subject_linkage["latest_native_rule"] = {
                "id": native_rule_id,
                "level": rule_level if isinstance(rule_level, int) else None,
                "description": native_rule_description,
            }

        reviewed_correlation_context = record.metadata.get("reviewed_correlation_context")
        if isinstance(reviewed_correlation_context, Mapping):
            subject_linkage["reviewed_correlation_context"] = {
                str(field_name): field_value
                for field_name, field_value in reviewed_correlation_context.items()
                if isinstance(field_value, str) and field_value.strip()
            }

        reviewed_source_profile = record.metadata.get("reviewed_source_profile")
        if isinstance(reviewed_source_profile, Mapping):
            subject_linkage["reviewed_source_profile"] = dict(reviewed_source_profile)

        raw_alert = record.metadata.get("raw_alert")
        if isinstance(raw_alert, Mapping):
            subject_linkage["latest_native_payload"] = dict(raw_alert)

        admission_provenance = _normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            subject_linkage["admission_provenance"] = admission_provenance

        reconciliation = self.persist_record(
            ReconciliationRecord(
                reconciliation_id=ingest_result.reconciliation.reconciliation_id,
                subject_linkage=subject_linkage,
                alert_id=ingest_result.reconciliation.alert_id,
                finding_id=ingest_result.reconciliation.finding_id,
                analytic_signal_id=ingest_result.reconciliation.analytic_signal_id,
                execution_run_id=ingest_result.reconciliation.execution_run_id,
                linked_execution_run_ids=(
                    ingest_result.reconciliation.linked_execution_run_ids
                ),
                correlation_key=ingest_result.reconciliation.correlation_key,
                first_seen_at=ingest_result.reconciliation.first_seen_at,
                last_seen_at=ingest_result.reconciliation.last_seen_at,
                ingest_disposition=ingest_result.reconciliation.ingest_disposition,
                mismatch_summary=ingest_result.reconciliation.mismatch_summary,
                compared_at=ingest_result.reconciliation.compared_at,
                lifecycle_state=ingest_result.reconciliation.lifecycle_state,
            )
        )
        return FindingAlertIngestResult(
            alert=ingest_result.alert,
            reconciliation=reconciliation,
            disposition=ingest_result.disposition,
        )

    def _with_native_detection_admission_provenance(
        self,
        record: NativeDetectionRecord,
        *,
        admission_kind: str,
        admission_channel: str,
    ) -> NativeDetectionRecord:
        if _normalize_admission_provenance(record.metadata.get("admission_provenance")) is not None:
            return record
        metadata = dict(record.metadata)
        metadata["admission_provenance"] = {
            "admission_kind": admission_kind,
            "admission_channel": admission_channel,
        }
        return replace(record, metadata=metadata)

    def reconcile_action_execution(
        self,
        *,
        action_request_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
        observed_executions: tuple[Mapping[str, object], ...],
        compared_at: datetime,
        stale_after: datetime,
    ) -> ReconciliationRecord:
        compared_at = self._require_aware_datetime(compared_at, "compared_at")
        stale_after = self._require_aware_datetime(stale_after, "stale_after")
        execution_surface_type = self._require_non_empty_string(
            execution_surface_type,
            "execution_surface_type",
        )
        execution_surface_id = self._require_non_empty_string(
            execution_surface_id,
            "execution_surface_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        if action_request.lifecycle_state != "approved":
            raise ValueError(
                f"Action request {action_request_id!r} is not approved "
                f"(state={action_request.lifecycle_state!r})"
            )

        normalized_executions = self._normalize_observed_executions(observed_executions)
        linked_execution_run_ids = tuple(
            execution["execution_run_id"] for execution in normalized_executions
        )
        unique_execution_run_ids = tuple(dict.fromkeys(linked_execution_run_ids))
        latest_execution = normalized_executions[-1] if normalized_executions else None
        authoritative_execution = self._find_authoritative_action_execution(
            action_request_id=action_request.action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            execution_run_id=(
                None if latest_execution is None else latest_execution["execution_run_id"]
            ),
            idempotency_key=(
                action_request.idempotency_key
                if latest_execution is None
                else latest_execution["idempotency_key"]
            ),
        )

        subject_linkage: dict[str, object] = {
            "action_request_ids": (action_request.action_request_id,),
            "execution_surface_types": (execution_surface_type,),
            "execution_surface_ids": (execution_surface_id,),
        }
        if action_request.approval_decision_id is not None:
            subject_linkage["approval_decision_ids"] = (
                action_request.approval_decision_id,
            )
        if action_request.alert_id is not None:
            subject_linkage["alert_ids"] = (action_request.alert_id,)
        if action_request.case_id is not None:
            subject_linkage["case_ids"] = (action_request.case_id,)
        if action_request.finding_id is not None:
            subject_linkage["finding_ids"] = (action_request.finding_id,)
        if authoritative_execution is not None:
            subject_linkage["action_execution_ids"] = (
                authoritative_execution.action_execution_id,
            )
            subject_linkage["delegation_ids"] = (
                authoritative_execution.delegation_id,
            )
            evidence_ids = self._merge_linked_ids(
                authoritative_execution.provenance.get("evidence_ids"),
                None,
            )
            if evidence_ids:
                subject_linkage["evidence_ids"] = evidence_ids

        ingest_disposition: str
        lifecycle_state: str
        mismatch_summary: str
        execution_run_id: str | None = None
        last_seen_at = action_request.requested_at

        if latest_execution is None:
            ingest_disposition = "missing"
            lifecycle_state = "pending"
            mismatch_summary = (
                "missing downstream execution for approved action request correlation"
            )
        else:
            execution_run_id = latest_execution["execution_run_id"]
            last_seen_at = latest_execution["observed_at"]
            observed_execution_surface_id = latest_execution["execution_surface_id"]
            observed_idempotency_key = latest_execution["idempotency_key"]
            if last_seen_at < stale_after and compared_at >= stale_after:
                ingest_disposition = "stale"
                lifecycle_state = "stale"
                mismatch_summary = "stale downstream execution observation requires refresh"
            elif len(unique_execution_run_ids) > 1:
                ingest_disposition = "duplicate"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "duplicate downstream executions observed for one approved request"
                )
            elif (
                observed_execution_surface_id != execution_surface_id
                or observed_idempotency_key != action_request.idempotency_key
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "execution surface/idempotency mismatch between approved request and observed execution"
                )
            else:
                ingest_disposition = "matched"
                lifecycle_state = "matched"
                mismatch_summary = (
                    "matched approved action request to reviewed execution run"
                )

        if (
            authoritative_execution is not None
            and latest_execution is not None
            and ingest_disposition == "matched"
        ):
            reconciled_lifecycle_state = self._action_execution_lifecycle_from_status(
                latest_execution.get("status"),
                authoritative_execution.lifecycle_state,
            )
            if reconciled_lifecycle_state != authoritative_execution.lifecycle_state:
                authoritative_execution = self.persist_record(
                    ActionExecutionRecord(
                        action_execution_id=authoritative_execution.action_execution_id,
                        action_request_id=authoritative_execution.action_request_id,
                        approval_decision_id=authoritative_execution.approval_decision_id,
                        delegation_id=authoritative_execution.delegation_id,
                        execution_surface_type=authoritative_execution.execution_surface_type,
                        execution_surface_id=authoritative_execution.execution_surface_id,
                        execution_run_id=authoritative_execution.execution_run_id,
                        idempotency_key=authoritative_execution.idempotency_key,
                        target_scope=authoritative_execution.target_scope,
                        approved_payload=authoritative_execution.approved_payload,
                        payload_hash=authoritative_execution.payload_hash,
                        delegated_at=authoritative_execution.delegated_at,
                        expires_at=authoritative_execution.expires_at,
                        provenance=authoritative_execution.provenance,
                        lifecycle_state=reconciled_lifecycle_state,
                    )
                )

        return self.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._next_identifier("reconciliation"),
                subject_linkage=subject_linkage,
                alert_id=action_request.alert_id,
                finding_id=action_request.finding_id,
                analytic_signal_id=None,
                execution_run_id=execution_run_id,
                linked_execution_run_ids=linked_execution_run_ids,
                correlation_key=self._build_action_execution_reconciliation_key(
                    action_request=action_request,
                    execution_surface_type=execution_surface_type,
                    execution_surface_id=execution_surface_id,
                    authoritative_execution=authoritative_execution,
                ),
                first_seen_at=action_request.requested_at,
                last_seen_at=last_seen_at,
                ingest_disposition=ingest_disposition,
                mismatch_summary=mismatch_summary,
                compared_at=compared_at,
                lifecycle_state=lifecycle_state,
            )
        )

    def _build_action_execution_reconciliation_key(
        self,
        *,
        action_request: ActionRequestRecord,
        execution_surface_type: str,
        execution_surface_id: str,
        authoritative_execution: ActionExecutionRecord | None,
    ) -> str:
        components = [action_request.action_request_id]
        if action_request.approval_decision_id is not None:
            components.append(action_request.approval_decision_id)
        if authoritative_execution is not None:
            components.append(authoritative_execution.delegation_id)
        components.extend(
            (
                execution_surface_type,
                execution_surface_id,
                action_request.idempotency_key,
            )
        )
        return ":".join(components)

    def _normalize_action_policy_basis(
        self,
        policy_basis: Mapping[str, object],
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for field_name, allowed_values in _ACTION_POLICY_ALLOWED_VALUES.items():
            raw_value = policy_basis.get(field_name)
            value = self._require_non_empty_string(raw_value, f"policy_basis.{field_name}")
            if value not in allowed_values:
                raise ValueError(
                    f"policy_basis.{field_name} must be one of {list(allowed_values)!r}"
                )
            normalized[field_name] = value
        return normalized

    def _determine_action_policy(
        self,
        policy_basis: Mapping[str, str],
    ) -> dict[str, str]:
        severity_rank = _ACTION_POLICY_RANKS["severity"][policy_basis["severity"]]
        target_scope_rank = _ACTION_POLICY_RANKS["target_scope"][
            policy_basis["target_scope"]
        ]
        reversibility_rank = _ACTION_POLICY_RANKS["action_reversibility"][
            policy_basis["action_reversibility"]
        ]
        blast_radius_rank = _ACTION_POLICY_RANKS["blast_radius"][
            policy_basis["blast_radius"]
        ]
        highest_criticality_rank = max(
            _ACTION_POLICY_RANKS["asset_criticality"][
                policy_basis["asset_criticality"]
            ],
            _ACTION_POLICY_RANKS["identity_criticality"][
                policy_basis["identity_criticality"]
            ],
        )
        execution_constraint = policy_basis["execution_constraint"]

        requires_isolated_executor = any(
            (
                execution_constraint == "requires_isolated_executor",
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["critical"],
                reversibility_rank
                >= _ACTION_POLICY_RANKS["action_reversibility"]["irreversible"],
                blast_radius_rank
                >= _ACTION_POLICY_RANKS["blast_radius"]["organization"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["critical"],
                target_scope_rank >= _ACTION_POLICY_RANKS["target_scope"]["organization"],
            )
        )
        if execution_constraint == "isolated_preferred" and any(
            (
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["high"],
                blast_radius_rank >= _ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["high"],
            )
        ):
            requires_isolated_executor = True

        approval_required = any(
            (
                requires_isolated_executor,
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["high"],
                target_scope_rank >= _ACTION_POLICY_RANKS["target_scope"]["multi_identity"],
                reversibility_rank
                >= _ACTION_POLICY_RANKS["action_reversibility"][
                    "bounded_reversible"
                ],
                blast_radius_rank
                >= _ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["high"],
            )
        )

        if requires_isolated_executor:
            execution_surface_type = "executor"
            execution_surface_id = "isolated-executor"
        else:
            execution_surface_type = "automation_substrate"
            execution_surface_id = "shuffle"

        return {
            "approval_requirement": (
                "human_required" if approval_required else "policy_authorized"
            ),
            "routing_target": (
                "approval"
                if approval_required
                else (
                    "shuffle"
                    if execution_surface_type == "automation_substrate"
                    else "executor"
                )
            ),
            "execution_surface_type": execution_surface_type,
            "execution_surface_id": execution_surface_id,
        }

    @staticmethod
    def _merge_linked_ids(
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        merged: list[str] = []
        if isinstance(existing_values, (list, tuple)):
            for value in existing_values:
                if isinstance(value, str) and value not in merged:
                    merged.append(value)
        if incoming_value is not None and incoming_value not in merged:
            merged.append(incoming_value)
        return tuple(merged)

    @staticmethod
    def _linked_id_exists(existing_values: object, candidate: str) -> bool:
        return isinstance(existing_values, (list, tuple)) and candidate in existing_values

    def _link_case_to_analytic_signals(
        self,
        analytic_signal_ids: tuple[str, ...],
        case_id: str | None,
    ) -> None:
        if case_id is None:
            return

        for analytic_signal_id in analytic_signal_ids:
            existing_signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
            if existing_signal is None:
                continue
            linked_case_ids = self._merge_linked_ids(existing_signal.case_ids, case_id)
            if linked_case_ids == existing_signal.case_ids:
                continue
            self.persist_record(
                AnalyticSignalRecord(
                    analytic_signal_id=existing_signal.analytic_signal_id,
                    substrate_detection_record_id=(
                        existing_signal.substrate_detection_record_id
                    ),
                    finding_id=existing_signal.finding_id,
                    alert_ids=existing_signal.alert_ids,
                    case_ids=linked_case_ids,
                    correlation_key=existing_signal.correlation_key,
                    first_seen_at=existing_signal.first_seen_at,
                    last_seen_at=existing_signal.last_seen_at,
                    lifecycle_state=existing_signal.lifecycle_state,
                    reviewed_context=existing_signal.reviewed_context,
                )
            )

    def _list_alert_evidence_records(
        self,
        *,
        alert_id: str,
        case_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        evidence_records: list[EvidenceRecord] = []
        for evidence in self._store.list(EvidenceRecord):
            if evidence.alert_id == alert_id or (
                case_id is not None and evidence.case_id == case_id
            ):
                evidence_records.append(evidence)
        return tuple(evidence_records)

    def _link_case_to_alert_reconciliations(
        self,
        *,
        alert_id: str,
        case_id: str,
        evidence_ids: tuple[str, ...],
    ) -> None:
        for reconciliation in self._store.list(ReconciliationRecord):
            if reconciliation.alert_id != alert_id:
                continue
            subject_linkage = dict(reconciliation.subject_linkage)
            updated_case_ids = self._merge_linked_ids(
                subject_linkage.get("case_ids"),
                case_id,
            )
            updated_evidence_ids = self._merge_linked_ids(
                subject_linkage.get("evidence_ids"),
                None,
            )
            for evidence_id in evidence_ids:
                updated_evidence_ids = self._merge_linked_ids(
                    updated_evidence_ids,
                    evidence_id,
                )
            if (
                tuple(subject_linkage.get("case_ids", ())) == updated_case_ids
                and tuple(subject_linkage.get("evidence_ids", ()))
                == updated_evidence_ids
            ):
                continue
            subject_linkage["case_ids"] = updated_case_ids
            subject_linkage["evidence_ids"] = updated_evidence_ids
            self.persist_record(
                ReconciliationRecord(
                    reconciliation_id=reconciliation.reconciliation_id,
                    subject_linkage=subject_linkage,
                    alert_id=reconciliation.alert_id,
                    finding_id=reconciliation.finding_id,
                    analytic_signal_id=reconciliation.analytic_signal_id,
                    execution_run_id=reconciliation.execution_run_id,
                    linked_execution_run_ids=(
                        reconciliation.linked_execution_run_ids
                    ),
                    correlation_key=reconciliation.correlation_key,
                    first_seen_at=reconciliation.first_seen_at,
                    last_seen_at=reconciliation.last_seen_at,
                    ingest_disposition=reconciliation.ingest_disposition,
                    mismatch_summary=reconciliation.mismatch_summary,
                    compared_at=reconciliation.compared_at,
                    lifecycle_state=reconciliation.lifecycle_state,
                )
            )

    def _resolve_analytic_signal_id(
        self,
        *,
        analytic_signal_id: str | None,
        finding_id: str,
        correlation_key: str,
        substrate_detection_record_id: str | None,
        latest_reconciliation: ReconciliationRecord | None,
    ) -> str:
        if analytic_signal_id is not None:
            return analytic_signal_id

        existing_signal_ids = self._merge_linked_ids(
            (
                latest_reconciliation.subject_linkage.get("analytic_signal_ids")
                if latest_reconciliation is not None
                else ()
            ),
            None,
        )
        if substrate_detection_record_id is not None:
            for existing_signal_id in existing_signal_ids:
                existing_signal = self._store.get(
                    AnalyticSignalRecord,
                    existing_signal_id,
                )
                if (
                    existing_signal is not None
                    and existing_signal.substrate_detection_record_id
                    == substrate_detection_record_id
                ):
                    return existing_signal_id

        if substrate_detection_record_id is None and len(existing_signal_ids) == 1:
            return existing_signal_ids[0]

        mint_material = "|".join(
            (
                finding_id,
                correlation_key,
                substrate_detection_record_id or "",
            )
        )
        return f"analytic-signal-{uuid.uuid5(uuid.NAMESPACE_URL, mint_material)}"

    @staticmethod
    def _normalize_substrate_detection_record_id(
        substrate_key: str,
        substrate_detection_record_id: str,
    ) -> str:
        namespaced_prefix = f"{substrate_key}:"
        if substrate_detection_record_id.startswith(namespaced_prefix):
            return substrate_detection_record_id
        return f"{namespaced_prefix}{substrate_detection_record_id}"

    @staticmethod
    def _normalize_observed_executions(
        observed_executions: tuple[Mapping[str, object], ...],
    ) -> tuple[dict[str, object], ...]:
        normalized: list[dict[str, object]] = []
        for execution in observed_executions:
            execution_run_id = execution.get("execution_run_id")
            execution_surface_id = execution.get("execution_surface_id")
            idempotency_key = execution.get("idempotency_key")
            observed_at = execution.get("observed_at")
            if not isinstance(execution_run_id, str):
                raise ValueError("observed execution must include string execution_run_id")
            if not isinstance(execution_surface_id, str):
                raise ValueError(
                    "observed execution must include string execution_surface_id"
                )
            if not isinstance(idempotency_key, str):
                raise ValueError("observed execution must include string idempotency_key")
            if not isinstance(observed_at, datetime):
                raise ValueError("observed execution must include datetime observed_at")
            observed_at = AegisOpsControlPlaneService._require_aware_datetime(
                observed_at,
                "observed_at",
            )
            normalized.append(
                {
                    "execution_run_id": execution_run_id,
                    "execution_surface_id": execution_surface_id,
                    "idempotency_key": idempotency_key,
                    "observed_at": observed_at,
                    "status": execution.get("status"),
                }
            )

        normalized.sort(key=lambda execution: execution["observed_at"])
        return tuple(normalized)

    def _find_authoritative_action_execution(
        self,
        *,
        action_request_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
        execution_run_id: str | None,
        idempotency_key: str,
    ) -> ActionExecutionRecord | None:
        matches = [
            execution
            for execution in self._store.list(ActionExecutionRecord)
            if (
                execution.action_request_id == action_request_id
                and execution.execution_surface_type == execution_surface_type
                and execution.execution_surface_id == execution_surface_id
                and execution.idempotency_key == idempotency_key
            )
        ]
        if execution_run_id is not None:
            for execution in matches:
                if execution.execution_run_id == execution_run_id:
                    return execution
        return matches[0] if matches else None

    @staticmethod
    def _action_execution_lifecycle_from_status(
        status: object,
        current_lifecycle_state: str,
    ) -> str:
        if not isinstance(status, str):
            return current_lifecycle_state

        normalized_status = status.strip().lower()
        if normalized_status in {"queued", "pending"}:
            return "queued"
        if normalized_status in {"running", "in_progress"}:
            return "running"
        if normalized_status in {"success", "succeeded", "completed"}:
            return "succeeded"
        if normalized_status in {"failed", "error"}:
            return "failed"
        if normalized_status in {"canceled", "cancelled"}:
            return "canceled"
        return current_lifecycle_state

    @staticmethod
    def _next_identifier(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    @staticmethod
    def _require_exact_approved_payload_binding(
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord,
        approved_payload: Mapping[str, object],
        execution_surface_type: str,
        execution_surface_id: str,
    ) -> None:
        if approval_decision.action_request_id != action_request.action_request_id:
            raise ValueError(
                "approved payload binding does not match approved action request and approval decision"
            )
        if approval_decision.target_snapshot != action_request.target_scope:
            raise ValueError(
                "approved payload binding does not match approved action request and approval decision"
            )

        payload_hash = _approved_payload_binding_hash(
            target_scope=action_request.target_scope,
            approved_payload=approved_payload,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
        )
        if (
            payload_hash != action_request.payload_hash
            or payload_hash != approval_decision.payload_hash
        ):
            raise ValueError(
                "approved payload binding does not match approved action request and approval decision"
            )

    @staticmethod
    def _require_exact_approved_expiry_binding(
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord,
        delegated_at: datetime,
        delegation_label: str,
    ) -> None:
        if approval_decision.approved_expires_at != action_request.expires_at:
            raise ValueError("approved expiry window does not match action request expiry")
        if (
            approval_decision.approved_expires_at is not None
            and delegated_at > approval_decision.approved_expires_at
        ):
            raise ValueError(
                f"Action request {action_request.action_request_id!r} expired before {delegation_label} delegation"
            )

    def _load_approved_delegation_context(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        execution_surface_type: str,
        execution_surface_id: str,
        invalid_execution_surface_type_message: str,
        invalid_execution_surface_id_message: str,
        delegation_label: str,
    ) -> tuple[ActionRequestRecord, ApprovalDecisionRecord]:
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        if action_request.lifecycle_state != "approved":
            raise ValueError(
                f"Action request {action_request_id!r} is not approved "
                f"(state={action_request.lifecycle_state!r})"
            )
        approval_decision_id = self._require_non_empty_string(
            action_request.approval_decision_id,
            "action_request.approval_decision_id",
        )
        approval_decision = self._store.get(ApprovalDecisionRecord, approval_decision_id)
        if approval_decision is None:
            raise LookupError(
                f"Missing approval decision {approval_decision_id!r} for action request "
                f"{action_request_id!r}"
            )
        if approval_decision.lifecycle_state != "approved":
            raise ValueError(
                f"Approval decision {approval_decision_id!r} is not approved "
                f"(state={approval_decision.lifecycle_state!r})"
            )
        if approval_decision.payload_hash != action_request.payload_hash:
            raise ValueError(
                "approval decision payload_hash does not match action request payload_hash"
            )
        policy_evaluation = action_request.policy_evaluation
        if policy_evaluation.get("execution_surface_type") != execution_surface_type:
            raise ValueError(invalid_execution_surface_type_message)
        if policy_evaluation.get("execution_surface_id") != execution_surface_id:
            raise ValueError(invalid_execution_surface_id_message)
        self._require_exact_approved_payload_binding(
            action_request=action_request,
            approval_decision=approval_decision,
            approved_payload=approved_payload,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
        )
        self._require_exact_approved_expiry_binding(
            action_request=action_request,
            approval_decision=approval_decision,
            delegated_at=delegated_at,
            delegation_label=delegation_label,
        )
        return action_request, approval_decision

    @staticmethod
    def _alert_review_state(alert: AlertRecord) -> str:
        if alert.lifecycle_state in {"new", "reopened"}:
            return "pending_review"
        if alert.lifecycle_state == "escalated_to_case":
            return "case_required"
        if alert.lifecycle_state == "investigating":
            return "investigating"
        return "triaged"

    @staticmethod
    def _alert_escalation_boundary(alert: AlertRecord) -> str:
        if alert.lifecycle_state == "escalated_to_case":
            return "tracked_case"
        return "next_business_hours_review"

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _require_mapping(value: object, field_name: str) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return {str(key): item for key, item in value.items()}


def build_runtime_snapshot(environ: Mapping[str, str] | None = None) -> RuntimeSnapshot:
    config = RuntimeConfig.from_env(environ)
    service = AegisOpsControlPlaneService(config)
    return service.describe_runtime()


def build_runtime_service(
    environ: Mapping[str, str] | None = None,
) -> AegisOpsControlPlaneService:
    config = RuntimeConfig.from_env(environ)
    return AegisOpsControlPlaneService(config)
