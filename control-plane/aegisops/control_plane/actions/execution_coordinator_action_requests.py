from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from .execution_coordinator import (
    ExecutionCoordinatorServiceDependencies,
    _PHASE26_REVIEWED_COORDINATION_TARGET_TYPES,
    _approved_payload_binding_hash,
    _json_ready,
)
from ..models import ActionRequestRecord


_PHASE26_REVIEWED_TICKET_SEVERITIES = frozenset(("low", "medium"))


class ReviewedActionRequestCoordinator:
    def __init__(self, service: ExecutionCoordinatorServiceDependencies) -> None:
        self._service = service

    @staticmethod
    def _require_single_linked_case_id(linked_case_ids: tuple[str, ...]) -> str:
        if len(linked_case_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one case before creating an action request"
            )
        return linked_case_ids[0]

    @staticmethod
    def _require_single_recommendation_binding(
        *,
        record_family: str,
        record_id: str,
        linked_recommendation_ids: tuple[str, ...],
    ) -> str:
        recommendation_ids = linked_recommendation_ids
        if record_family == "recommendation":
            recommendation_ids = (record_id,)
        if len(recommendation_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one recommendation before creating an action request"
            )
        return recommendation_ids[0]

    def create_reviewed_action_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        recipient_identity: str,
        message_intent: str,
        escalation_reason: str,
        expires_at: datetime,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        requester_identity = self._service._require_non_empty_string(
            requester_identity,
            "requester_identity",
        )
        recipient_identity = self._service._require_non_empty_string(
            recipient_identity,
            "recipient_identity",
        )
        message_intent = self._service._require_non_empty_string(
            message_intent,
            "message_intent",
        )
        escalation_reason = self._service._require_non_empty_string(
            escalation_reason,
            "escalation_reason",
        )
        expires_at = self._service._require_aware_datetime(expires_at, "expires_at")

        with self._service._store.transaction():
            context_snapshot = (
                self._service._assistant_context_assembler.inspect_assistant_context(
                    record_family,
                    record_id,
                )
            )
            self._service._require_reviewed_case_scoped_advisory_read(context_snapshot)
            recommendation_draft = (
                self._service._assistant_advisory_coordinator.render_recommendation_draft(
                    record_family,
                    record_id,
                )
            )
            if recommendation_draft.recommendation_draft.get("status") != "ready":
                raise ValueError(
                    "reviewed advisory context is not ready for approval-bound action requests"
                )

            recommendation_id = self._require_single_recommendation_binding(
                record_family=record_family,
                record_id=record_id,
                linked_recommendation_ids=recommendation_draft.linked_recommendation_ids,
            )
            case_id = self._require_single_linked_case_id(
                recommendation_draft.linked_case_ids
            )
            case = self._service._require_reviewed_operator_case(case_id)
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("expires_at must be in the future")

            requested_payload = {
                "action_type": "notify_identity_owner",
                "recipient_identity": recipient_identity,
                "message_intent": message_intent,
                "escalation_reason": escalation_reason,
                "source_record_family": record_family,
                "source_record_id": record_id,
                "recommendation_id": recommendation_id,
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "linked_evidence_ids": recommendation_draft.linked_evidence_ids,
            }
            target_scope = {
                "record_family": record_family,
                "record_id": record_id,
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "recipient_identity": recipient_identity,
            }
            payload_hash = _approved_payload_binding_hash(
                target_scope=target_scope,
                approved_payload=requested_payload,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            )
            requested_at = datetime.now(timezone.utc)
            if expires_at <= requested_at:
                raise ValueError("expires_at must be after requested_at")

            idempotency_material = json.dumps(
                _json_ready(
                    {
                        "payload_hash": payload_hash,
                        "record_family": record_family,
                        "record_id": record_id,
                        "requester_identity": requester_identity,
                        "expires_at": expires_at,
                    }
                ),
                sort_keys=True,
                separators=(",", ":"),
            )
            idempotency_key = (
                "notify-identity-owner:"
                + hashlib.sha256(idempotency_material.encode("utf-8")).hexdigest()
            )
            for existing in self._service._store.list(ActionRequestRecord):
                if existing.idempotency_key == idempotency_key:
                    self._service._emit_structured_event(
                        20,
                        "action_request_reused",
                        action_request_id=existing.action_request_id,
                        action_type=existing.requested_payload.get("action_type"),
                        lifecycle_state=existing.lifecycle_state,
                        case_id=existing.case_id,
                    )
                    return existing

            normalized_action_request_id = self._service._resolve_new_record_identifier(
                ActionRequestRecord,
                action_request_id,
                "action_request_id",
                "action-request",
            )
            created_request = self._service.persist_record(
                ActionRequestRecord(
                    action_request_id=normalized_action_request_id,
                    approval_decision_id=None,
                    case_id=case.case_id,
                    alert_id=case.alert_id,
                    finding_id=case.finding_id,
                    idempotency_key=idempotency_key,
                    target_scope=target_scope,
                    payload_hash=payload_hash,
                    requested_at=requested_at,
                    expires_at=expires_at,
                    lifecycle_state="pending_approval",
                    requester_identity=requester_identity,
                    requested_payload=requested_payload,
                    policy_basis={
                        "severity": "low",
                        "target_scope": "single_identity",
                        "action_reversibility": "reversible",
                        "asset_criticality": "standard",
                        "identity_criticality": "standard",
                        "blast_radius": "single_target",
                        "execution_constraint": "routine_allowed",
                    },
                    policy_evaluation={
                        "approval_requirement": "human_required",
                        "approval_requirement_override": "human_required",
                        "routing_target": "approval",
                        "execution_surface_type": "automation_substrate",
                        "execution_surface_id": "shuffle",
                    },
                ),
                transitioned_at=requested_at,
            )
        self._service._emit_structured_event(
            20,
            "action_request_created",
            action_request_id=created_request.action_request_id,
            action_type=created_request.requested_payload.get("action_type"),
            requester_identity=created_request.requester_identity,
            case_id=created_request.case_id,
            alert_id=created_request.alert_id,
            lifecycle_state=created_request.lifecycle_state,
            expires_at=created_request.expires_at.isoformat()
            if created_request.expires_at is not None
            else None,
        )
        return created_request

    def create_reviewed_tracking_ticket_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        coordination_reference_id: str,
        coordination_target_type: str,
        ticket_title: str,
        ticket_description: str,
        expires_at: datetime,
        ticket_severity: str = "medium",
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        requester_identity = self._service._require_non_empty_string(
            requester_identity,
            "requester_identity",
        )
        coordination_reference_id = self._service._require_non_empty_string(
            coordination_reference_id,
            "coordination_reference_id",
        )
        coordination_target_type = self._service._require_non_empty_string(
            coordination_target_type,
            "coordination_target_type",
        )
        if coordination_target_type not in _PHASE26_REVIEWED_COORDINATION_TARGET_TYPES:
            raise ValueError(
                "coordination_target_type is outside the reviewed tracking-ticket scope"
            )
        ticket_title = self._service._require_non_empty_string(
            ticket_title,
            "ticket_title",
        )
        ticket_description = self._service._require_non_empty_string(
            ticket_description,
            "ticket_description",
        )
        ticket_severity = self._service._require_non_empty_string(
            ticket_severity,
            "ticket_severity",
        )
        if ticket_severity not in _PHASE26_REVIEWED_TICKET_SEVERITIES:
            raise ValueError(
                "ticket_severity is outside the reviewed tracking-ticket scope"
            )
        expires_at = self._service._require_aware_datetime(expires_at, "expires_at")

        with self._service._store.transaction():
            context_snapshot = (
                self._service._assistant_context_assembler.inspect_assistant_context(
                    record_family,
                    record_id,
                )
            )
            self._service._require_reviewed_case_scoped_advisory_read(context_snapshot)
            recommendation_draft = (
                self._service._assistant_advisory_coordinator.render_recommendation_draft(
                    record_family,
                    record_id,
                )
            )
            if recommendation_draft.recommendation_draft.get("status") != "ready":
                raise ValueError(
                    "reviewed advisory context is not ready for approval-bound action requests"
                )

            recommendation_id = self._require_single_recommendation_binding(
                record_family=record_family,
                record_id=record_id,
                linked_recommendation_ids=recommendation_draft.linked_recommendation_ids,
            )
            case_id = self._require_single_linked_case_id(
                recommendation_draft.linked_case_ids
            )
            case = self._service._require_reviewed_operator_case(case_id)
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("expires_at must be in the future")

            requested_payload = {
                "action_type": "create_tracking_ticket",
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "coordination_reference_id": coordination_reference_id,
                "coordination_target_type": coordination_target_type,
                "ticket_title": ticket_title,
                "ticket_description": ticket_description,
                "ticket_severity": ticket_severity,
                "source_record_family": record_family,
                "source_record_id": record_id,
                "recommendation_id": recommendation_id,
                "linked_evidence_ids": recommendation_draft.linked_evidence_ids,
            }
            target_scope = {
                "record_family": record_family,
                "record_id": record_id,
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "coordination_reference_id": coordination_reference_id,
                "coordination_target_type": coordination_target_type,
            }
            payload_hash = _approved_payload_binding_hash(
                target_scope=target_scope,
                approved_payload=requested_payload,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            )
            requested_at = datetime.now(timezone.utc)
            if expires_at <= requested_at:
                raise ValueError("expires_at must be after requested_at")

            idempotency_material = json.dumps(
                _json_ready(
                    {
                        "payload_hash": payload_hash,
                        "record_family": record_family,
                        "record_id": record_id,
                        "requester_identity": requester_identity,
                        "expires_at": expires_at,
                    }
                ),
                sort_keys=True,
                separators=(",", ":"),
            )
            idempotency_key = (
                "create-tracking-ticket:"
                + hashlib.sha256(idempotency_material.encode("utf-8")).hexdigest()
            )
            for existing in self._service._store.list(ActionRequestRecord):
                if existing.idempotency_key == idempotency_key:
                    self._service._emit_structured_event(
                        20,
                        "action_request_reused",
                        action_request_id=existing.action_request_id,
                        action_type=existing.requested_payload.get("action_type"),
                        lifecycle_state=existing.lifecycle_state,
                        case_id=existing.case_id,
                    )
                    return existing

            normalized_action_request_id = self._service._resolve_new_record_identifier(
                ActionRequestRecord,
                action_request_id,
                "action_request_id",
                "action-request",
            )
            created_request = self._service.persist_record(
                ActionRequestRecord(
                    action_request_id=normalized_action_request_id,
                    approval_decision_id=None,
                    case_id=case.case_id,
                    alert_id=case.alert_id,
                    finding_id=case.finding_id,
                    idempotency_key=idempotency_key,
                    target_scope=target_scope,
                    payload_hash=payload_hash,
                    requested_at=requested_at,
                    expires_at=expires_at,
                    lifecycle_state="pending_approval",
                    requester_identity=requester_identity,
                    requested_payload=requested_payload,
                    policy_basis={
                        "severity": "low",
                        "target_scope": "single_asset",
                        "action_reversibility": "bounded_reversible",
                        "asset_criticality": "standard",
                        "identity_criticality": "standard",
                        "blast_radius": "single_target",
                        "execution_constraint": "routine_allowed",
                    },
                    policy_evaluation={
                        "approval_requirement": "human_required",
                        "approval_requirement_override": "human_required",
                        "routing_target": "approval",
                        "execution_surface_type": "automation_substrate",
                        "execution_surface_id": "shuffle",
                    },
                ),
                transitioned_at=requested_at,
            )
        self._service._emit_structured_event(
            20,
            "action_request_created",
            action_request_id=created_request.action_request_id,
            action_type=created_request.requested_payload.get("action_type"),
            requester_identity=created_request.requester_identity,
            case_id=created_request.case_id,
            alert_id=created_request.alert_id,
            lifecycle_state=created_request.lifecycle_state,
            expires_at=created_request.expires_at.isoformat()
            if created_request.expires_at is not None
            else None,
        )
        return created_request
