from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Mapping

from .models import (
    AlertRecord,
    CaseRecord,
    EvidenceRecord,
    LifecycleTransitionRecord,
    RecommendationRecord,
    ReconciliationRecord,
)


_ALLOWED_RECOMMENDATION_LABEL_STATES = frozenset(
    {"accepted", "rejected", "superseded", "withdrawn"}
)
_RECORD_FAMILY_DISPLAY_NAMES = {
    "alert": "Alert",
    "case": "Case",
    "evidence": "Evidence",
    "recommendation": "Recommendation",
    "reconciliation": "Reconciliation",
}
_REQUIRED_ANCHOR_PROVENANCE_FIELDS = (
    "classification",
    "source_id",
    "timestamp",
)


class Phase29ShadowDatasetGenerationError(ValueError):
    """Raised when reviewed shadow dataset generation cannot stay within bounds."""


@dataclass(frozen=True)
class Phase29ShadowDatasetSnapshot:
    snapshot_id: str
    extraction_spec_version: str
    snapshot_timestamp: str
    example_count: int
    examples: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "extraction_spec_version": self.extraction_spec_version,
            "snapshot_timestamp": self.snapshot_timestamp,
            "example_count": self.example_count,
            "examples": self.examples,
        }


def generate_reviewed_shadow_dataset(
    service: object,
    *,
    extraction_spec_version: str,
    snapshot_timestamp: datetime,
) -> Phase29ShadowDatasetSnapshot:
    if (
        not isinstance(snapshot_timestamp, datetime)
        or snapshot_timestamp.tzinfo is None
        or snapshot_timestamp.utcoffset() is None
    ):
        raise ValueError("snapshot_timestamp must be a timezone-aware datetime")
    if not isinstance(extraction_spec_version, str) or not extraction_spec_version.strip():
        raise ValueError("extraction_spec_version must be a non-empty string")

    store = getattr(service, "_store", None)
    if store is None:
        raise TypeError("service must expose the authoritative control-plane store")

    recommendations = sorted(
        store.list(RecommendationRecord),
        key=lambda record: record.recommendation_id,
    )

    examples = tuple(
        _build_recommendation_example(
            service=service,
            store=store,
            recommendation=recommendation,
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
        )
        for recommendation in recommendations
        if recommendation.lifecycle_state in _ALLOWED_RECOMMENDATION_LABEL_STATES
    )

    snapshot_payload = {
        "extraction_spec_version": extraction_spec_version,
        "snapshot_timestamp": snapshot_timestamp.isoformat(),
        "examples": examples,
    }
    snapshot_id = hashlib.sha256(
        _canonical_json(snapshot_payload).encode("utf-8")
    ).hexdigest()
    return Phase29ShadowDatasetSnapshot(
        snapshot_id=snapshot_id,
        extraction_spec_version=extraction_spec_version,
        snapshot_timestamp=snapshot_timestamp.isoformat(),
        example_count=len(examples),
        examples=examples,
    )


def _build_recommendation_example(
    *,
    service: object,
    store: object,
    recommendation: RecommendationRecord,
    extraction_spec_version: str,
    snapshot_timestamp: datetime,
) -> dict[str, object]:
    if not recommendation.case_id or not recommendation.alert_id:
        raise Phase29ShadowDatasetGenerationError(
            f"recommendation {recommendation.recommendation_id} is missing reviewed subject linkage"
        )

    case_record = store.get(CaseRecord, recommendation.case_id)
    if case_record is None:
        raise Phase29ShadowDatasetGenerationError(
            f"recommendation {recommendation.recommendation_id} references missing case "
            f"{recommendation.case_id}"
        )
    alert_record = store.get(AlertRecord, recommendation.alert_id)
    if alert_record is None:
        raise Phase29ShadowDatasetGenerationError(
            f"recommendation {recommendation.recommendation_id} references missing alert "
            f"{recommendation.alert_id}"
        )

    source_family = _nested_string(
        alert_record.reviewed_context,
        ("source", "source_family"),
    )
    if source_family is None:
        raise Phase29ShadowDatasetGenerationError(
            f"recommendation {recommendation.recommendation_id} is missing reviewed source family linkage"
        )

    linked_evidence = _linked_evidence_records(
        store=store,
        case_id=case_record.case_id,
        alert_id=alert_record.alert_id,
    )
    anchor_evidence = _select_anchor_evidence(
        recommendation_id=recommendation.recommendation_id,
        linked_evidence=linked_evidence,
    )

    label_transition = _latest_lifecycle_transition(
        service,
        "recommendation",
        recommendation.recommendation_id,
    )
    if label_transition is None:
        raise Phase29ShadowDatasetGenerationError(
            "missing required reviewed label transition for recommendation "
            f"{recommendation.recommendation_id}"
        )

    ambiguity_badges = sorted(
        {
            ambiguity_badge
            for evidence in linked_evidence
            for ambiguity_badge in (_optional_string(evidence.provenance.get("ambiguity_badge")),)
            if ambiguity_badge is not None
        }
    )
    latest_reconciliation = _latest_reconciliation(
        store=store,
        alert_id=alert_record.alert_id,
        case_id=case_record.case_id,
    )

    case_transition = _latest_lifecycle_transition(service, "case", case_record.case_id)

    features: dict[str, object] = {
        "source_family": _feature_entry(
            value=source_family,
            record_family="alert",
            record_id=alert_record.alert_id,
            field_path="reviewed_context.source.source_family",
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
            classification=None,
            reviewed_by=_first_actor_identity(case_transition),
            reviewed_linkage="subject-alert-link",
        ),
        "case_lifecycle_state": _feature_entry(
            value=case_record.lifecycle_state,
            record_family="case",
            record_id=case_record.case_id,
            field_path="lifecycle_state",
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
            classification=None,
            reviewed_by=_first_actor_identity(case_transition),
            reviewed_linkage="subject-case-link",
        ),
    }

    case_triage_disposition = _nested_string(
        case_record.reviewed_context,
        ("triage", "disposition"),
    )
    if case_triage_disposition is not None:
        features["case_triage_disposition"] = _feature_entry(
            value=case_triage_disposition,
            record_family="case",
            record_id=case_record.case_id,
            field_path="reviewed_context.triage.disposition",
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
            classification=None,
            reviewed_by=_first_actor_identity(case_transition),
            reviewed_linkage="subject-case-link",
        )

    features["ambiguity_badges"] = _feature_entry(
        value=ambiguity_badges,
        record_family="evidence",
        record_id=anchor_evidence.evidence_id,
        field_path="provenance.ambiguity_badge",
        extraction_spec_version=extraction_spec_version,
        snapshot_timestamp=snapshot_timestamp,
        classification=_optional_string(anchor_evidence.provenance.get("classification")),
        reviewed_by=_optional_string(anchor_evidence.provenance.get("reviewed_by")),
        reviewed_linkage="subject-anchor-evidence-link",
    )

    if latest_reconciliation is not None:
        features["source_health_state"] = _feature_entry(
            value=latest_reconciliation.lifecycle_state,
            record_family="reconciliation",
            record_id=latest_reconciliation.reconciliation_id,
            field_path="lifecycle_state",
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
            classification=None,
            reviewed_by=None,
            reviewed_linkage="subject-alert-link",
        )
        features["source_health_ingest_disposition"] = _feature_entry(
            value=latest_reconciliation.ingest_disposition,
            record_family="reconciliation",
            record_id=latest_reconciliation.reconciliation_id,
            field_path="ingest_disposition",
            extraction_spec_version=extraction_spec_version,
            snapshot_timestamp=snapshot_timestamp,
            classification=None,
            reviewed_by=None,
            reviewed_linkage="subject-alert-link",
        )

    return {
        "subject_record_family": "recommendation",
        "subject_record_id": recommendation.recommendation_id,
        "linked_case_id": case_record.case_id,
        "linked_alert_id": alert_record.alert_id,
        "features": features,
        "label": {
            "value": recommendation.lifecycle_state,
            "provenance": {
                "label_record_family": _display_record_family("recommendation"),
                "label_record_id": recommendation.recommendation_id,
                "label_field_path": "lifecycle_state",
                "label_decision_basis": "reviewed recommendation lifecycle_state",
                "label_decided_at": label_transition.transitioned_at.isoformat(),
                "label_reviewed_by": (
                    _first_actor_identity(label_transition) or recommendation.review_owner
                ),
                "label_linked_subject_record_id": recommendation.recommendation_id,
            },
        },
    }


def _linked_evidence_records(
    *,
    store: object,
    case_id: str,
    alert_id: str,
) -> tuple[EvidenceRecord, ...]:
    return tuple(
        sorted(
            (
                evidence
                for evidence in store.list(EvidenceRecord)
                if evidence.case_id == case_id or evidence.alert_id == alert_id
            ),
            key=lambda evidence: evidence.evidence_id,
        )
    )


def _select_anchor_evidence(
    *,
    recommendation_id: str,
    linked_evidence: tuple[EvidenceRecord, ...],
) -> EvidenceRecord:
    anchor_evidence = tuple(
        evidence
        for evidence in linked_evidence
        if evidence.derivation_relationship == "reviewed_context_anchor"
    )
    if not anchor_evidence:
        raise Phase29ShadowDatasetGenerationError(
            f"recommendation {recommendation_id} is missing required reviewed provenance "
            "anchor evidence"
        )

    for evidence in anchor_evidence:
        missing_fields = tuple(
            field_name
            for field_name in _REQUIRED_ANCHOR_PROVENANCE_FIELDS
            if _optional_string(evidence.provenance.get(field_name)) is None
        )
        if missing_fields:
            raise Phase29ShadowDatasetGenerationError(
                "missing required reviewed provenance on anchor evidence "
                f"{evidence.evidence_id}: {', '.join(missing_fields)}"
            )
    return anchor_evidence[0]


def _latest_reconciliation(
    *,
    store: object,
    alert_id: str,
    case_id: str,
) -> ReconciliationRecord | None:
    matching = [
        reconciliation
        for reconciliation in store.list(ReconciliationRecord)
        if reconciliation.alert_id == alert_id
        or case_id in _tuple_of_strings(reconciliation.subject_linkage.get("case_ids"))
    ]
    if not matching:
        return None
    return sorted(
        matching,
        key=lambda reconciliation: (
            reconciliation.compared_at,
            reconciliation.reconciliation_id,
        ),
    )[-1]


def _latest_lifecycle_transition(
    service: object,
    record_family: str,
    record_id: str,
) -> LifecycleTransitionRecord | None:
    list_transitions = getattr(service, "list_lifecycle_transitions", None)
    if not callable(list_transitions):
        raise TypeError("service must expose list_lifecycle_transitions")
    transitions = list_transitions(record_family, record_id)
    if not transitions:
        return None
    return transitions[-1]


def _feature_entry(
    *,
    value: object,
    record_family: str,
    record_id: str,
    field_path: str,
    extraction_spec_version: str,
    snapshot_timestamp: datetime,
    classification: str | None,
    reviewed_by: str | None,
    reviewed_linkage: str,
) -> dict[str, object]:
    return {
        "value": value,
        "provenance": {
            "feature_source_record_family": _display_record_family(record_family),
            "feature_source_record_id": record_id,
            "feature_source_field_path": field_path,
            "feature_extraction_spec_version": extraction_spec_version,
            "feature_snapshot_timestamp": snapshot_timestamp.isoformat(),
            "feature_reviewed_linkage": reviewed_linkage,
            "feature_source_provenance_classification": classification,
            "feature_source_reviewed_by": reviewed_by,
        },
    }


def _display_record_family(record_family: str) -> str:
    return _RECORD_FAMILY_DISPLAY_NAMES.get(record_family, record_family)


def _nested_string(
    mapping: Mapping[str, object],
    path: tuple[str, ...],
) -> str | None:
    current: object = mapping
    for part in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return _optional_string(current)


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _first_actor_identity(transition: LifecycleTransitionRecord | None) -> str | None:
    if transition is None:
        return None
    attribution = transition.attribution
    if not isinstance(attribution, Mapping):
        return None
    actor_identities = attribution.get("actor_identities")
    if not isinstance(actor_identities, tuple) or not actor_identities:
        return None
    return _optional_string(actor_identities[0])


def _tuple_of_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(
            item.strip() for item in value if isinstance(item, str) and item.strip()
        )
    return ()


def _canonical_json(value: object) -> str:
    return json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    )


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
