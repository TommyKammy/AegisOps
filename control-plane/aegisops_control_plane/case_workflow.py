from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Mapping

from .evidence_linkage import EvidenceLinkageService
from .models import (
    AlertRecord,
    CaseRecord,
    LeadRecord,
    ObservationRecord,
    RecommendationRecord,
)

if TYPE_CHECKING:
    from .service import AegisOpsControlPlaneService


class CaseWorkflowService:
    def __init__(
        self,
        service: AegisOpsControlPlaneService,
        *,
        evidence_linkage_service: EvidenceLinkageService,
        merge_reviewed_context: Callable[
            [Mapping[str, object], Mapping[str, object]],
            dict[str, object],
        ],
    ) -> None:
        self._service = service
        self._evidence_linkage_service = evidence_linkage_service
        self._merge_reviewed_context = merge_reviewed_context

    def record_case_observation(
        self,
        *,
        case_id: str,
        author_identity: str,
        observed_at: datetime,
        scope_statement: str,
        supporting_evidence_ids: tuple[str, ...] = (),
        observation_id: str | None = None,
        lifecycle_state: str = "confirmed",
    ) -> ObservationRecord:
        service = self._service
        service._require_case_record(case_id)
        author_identity = service._require_non_empty_string(
            author_identity,
            "author_identity",
        )
        observed_at = service._require_aware_datetime(observed_at, "observed_at")
        scope_statement = service._require_non_empty_string(
            scope_statement,
            "scope_statement",
        )
        lifecycle_state = service._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        normalized_evidence_ids = self._evidence_linkage_service.normalize_linked_record_ids(
            supporting_evidence_ids,
            "supporting_evidence_ids",
        )
        with service._store.transaction():
            case = service._require_reviewed_operator_case(case_id)
            self._evidence_linkage_service.validate_case_evidence_linkage(
                case=case,
                evidence_ids=normalized_evidence_ids,
                field_name="supporting_evidence_ids",
            )
            resolved_observation_id = service._resolve_new_record_identifier(
                ObservationRecord,
                observation_id,
                "observation_id",
                "observation",
            )
            return service.persist_record(
                ObservationRecord(
                    observation_id=resolved_observation_id,
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    supporting_evidence_ids=normalized_evidence_ids,
                    author_identity=author_identity,
                    observed_at=observed_at,
                    scope_statement=scope_statement,
                    lifecycle_state=lifecycle_state,
                )
            )

    def record_case_lead(
        self,
        *,
        case_id: str,
        triage_owner: str,
        triage_rationale: str,
        observation_id: str | None = None,
        lead_id: str | None = None,
        lifecycle_state: str = "triaged",
    ) -> LeadRecord:
        service = self._service
        triage_owner = service._require_non_empty_string(triage_owner, "triage_owner")
        triage_rationale = service._require_non_empty_string(
            triage_rationale,
            "triage_rationale",
        )
        lifecycle_state = service._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        resolved_observation_id = service._normalize_optional_string(
            observation_id,
            "observation_id",
        )
        with service._store.transaction():
            case = service._require_reviewed_operator_case(case_id)
            if resolved_observation_id is not None:
                observation = service._store.get(
                    ObservationRecord,
                    resolved_observation_id,
                )
                if observation is None:
                    raise LookupError(f"Missing observation {resolved_observation_id!r}")
                if observation.case_id != case.case_id:
                    raise ValueError(
                        f"Observation {resolved_observation_id!r} is not linked to case "
                        f"{case.case_id!r}"
                    )

            resolved_lead_id = service._resolve_new_record_identifier(
                LeadRecord,
                lead_id,
                "lead_id",
                "lead",
            )
            return service.persist_record(
                LeadRecord(
                    lead_id=resolved_lead_id,
                    observation_id=resolved_observation_id,
                    finding_id=case.finding_id,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    triage_owner=triage_owner,
                    triage_rationale=triage_rationale,
                    lifecycle_state=lifecycle_state,
                )
            )

    def record_case_recommendation(
        self,
        *,
        case_id: str,
        review_owner: str,
        intended_outcome: str,
        lead_id: str | None = None,
        recommendation_id: str | None = None,
        lifecycle_state: str = "under_review",
    ) -> RecommendationRecord:
        service = self._service
        review_owner = service._require_non_empty_string(review_owner, "review_owner")
        intended_outcome = service._require_non_empty_string(
            intended_outcome,
            "intended_outcome",
        )
        lifecycle_state = service._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        resolved_lead_id = service._normalize_optional_string(lead_id, "lead_id")
        with service._store.transaction():
            case = service._require_reviewed_operator_case(case_id)
            if resolved_lead_id is not None:
                lead = service._store.get(LeadRecord, resolved_lead_id)
                if lead is None:
                    raise LookupError(f"Missing lead {resolved_lead_id!r}")
                if lead.case_id != case.case_id:
                    raise ValueError(
                        f"Lead {resolved_lead_id!r} is not linked to case {case.case_id!r}"
                    )

            resolved_recommendation_id = service._resolve_new_record_identifier(
                RecommendationRecord,
                recommendation_id,
                "recommendation_id",
                "recommendation",
            )
            return service.persist_record(
                RecommendationRecord(
                    recommendation_id=resolved_recommendation_id,
                    lead_id=resolved_lead_id,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    ai_trace_id=None,
                    review_owner=review_owner,
                    intended_outcome=intended_outcome,
                    lifecycle_state=lifecycle_state,
                    reviewed_context=case.reviewed_context,
                )
            )

    def record_case_handoff(
        self,
        *,
        case_id: str,
        handoff_at: datetime,
        handoff_owner: str,
        handoff_note: str,
        follow_up_evidence_ids: tuple[str, ...] = (),
    ) -> CaseRecord:
        service = self._service
        service._require_case_record(case_id)
        handoff_at = service._require_aware_datetime(handoff_at, "handoff_at")
        handoff_owner = service._require_non_empty_string(
            handoff_owner,
            "handoff_owner",
        )
        handoff_note = service._require_non_empty_string(handoff_note, "handoff_note")
        normalized_evidence_ids = self._evidence_linkage_service.normalize_linked_record_ids(
            follow_up_evidence_ids,
            "follow_up_evidence_ids",
        )
        with service._store.transaction():
            case = service._require_reviewed_operator_case(case_id)
            self._evidence_linkage_service.validate_case_evidence_linkage(
                case=case,
                evidence_ids=normalized_evidence_ids,
                field_name="follow_up_evidence_ids",
            )
            updated_reviewed_context = self._merge_reviewed_context(
                case.reviewed_context,
                {
                    "handoff": {
                        "handoff_at": handoff_at.isoformat(),
                        "handoff_owner": handoff_owner,
                        "note": handoff_note,
                        "follow_up_evidence_ids": normalized_evidence_ids,
                    }
                },
            )
            return service.persist_record(
                replace(
                    case,
                    reviewed_context=updated_reviewed_context,
                )
            )

    def record_case_disposition(
        self,
        *,
        case_id: str,
        disposition: str,
        rationale: str,
        recorded_at: datetime,
    ) -> CaseRecord:
        service = self._service
        service._require_control_plane_change_authority_unfrozen()
        disposition = service._require_non_empty_string(disposition, "disposition")
        rationale = service._require_non_empty_string(rationale, "rationale")
        recorded_at = service._require_aware_datetime(recorded_at, "recorded_at")
        lifecycle_state = service._case_lifecycle_for_disposition(disposition)
        with service._store.transaction():
            case = service._require_reviewed_operator_case(case_id)
            alert = None
            if case.alert_id is not None and lifecycle_state == "closed":
                alert = service._store.get(AlertRecord, case.alert_id)
                if alert is None:
                    raise LookupError(f"Missing alert {case.alert_id!r}")
            updated_reviewed_context = self._merge_reviewed_context(
                case.reviewed_context,
                {
                    "triage": {
                        "disposition": disposition,
                        "closure_rationale": rationale,
                        "recorded_at": recorded_at.isoformat(),
                    }
                },
            )
            updated_case = service.persist_record(
                replace(
                    case,
                    lifecycle_state=lifecycle_state,
                    reviewed_context=updated_reviewed_context,
                ),
                transitioned_at=recorded_at,
            )
            if alert is not None:
                service.persist_record(
                    replace(
                        alert,
                        lifecycle_state="closed",
                        reviewed_context=self._merge_reviewed_context(
                            alert.reviewed_context,
                            {"triage": updated_reviewed_context.get("triage", {})},
                        ),
                    ),
                    transitioned_at=recorded_at,
                )
        return updated_case
