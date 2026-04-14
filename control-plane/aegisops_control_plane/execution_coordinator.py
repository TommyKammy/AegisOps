from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Mapping, Protocol

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)


class ExecutionCoordinatorServiceDependencies(Protocol):
    _store: object
    _shuffle: object
    _isolated_executor: object

    def inspect_assistant_context(self, record_family: str, record_id: str) -> object:
        ...

    def render_recommendation_draft(self, record_family: str, record_id: str) -> object:
        ...

    def persist_record(self, record: object) -> object:
        ...

    def _emit_structured_event(
        self,
        level: int,
        event: str,
        **fields: object,
    ) -> None:
        ...

    def _emit_action_execution_delegated_event(
        self,
        execution: ActionExecutionRecord,
    ) -> None:
        ...

    def _require_phase19_case_scoped_advisory_read(self, context_snapshot: object) -> None:
        ...

    def _require_single_recommendation_binding(
        self,
        *,
        record_family: str,
        record_id: str,
        linked_recommendation_ids: tuple[str, ...],
    ) -> str:
        ...

    def _require_single_linked_case_id(self, linked_case_ids: tuple[str, ...]) -> str:
        ...

    def _require_phase19_operator_case(self, case_id: str) -> object:
        ...

    def _resolve_new_record_identifier(
        self,
        record_type: type,
        requested_identifier: str | None,
        field_name: str,
        prefix: str,
    ) -> str:
        ...

    def _require_aware_datetime(self, value: datetime, field_name: str) -> datetime:
        ...

    def _require_non_empty_string(self, value: object, field_name: str) -> str:
        ...

    def _require_mapping(self, value: object, field_name: str) -> dict[str, object]:
        ...

    def _next_identifier(self, prefix: str) -> str:
        ...

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


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
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


class ExecutionCoordinator:
    """Owns approved action request, delegation, and reconciliation flows."""

    def __init__(self, service: ExecutionCoordinatorServiceDependencies) -> None:
        self._service = service

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
            context_snapshot = self._service.inspect_assistant_context(
                record_family,
                record_id,
            )
            self._service._require_phase19_case_scoped_advisory_read(context_snapshot)
            recommendation_draft = self._service.render_recommendation_draft(
                record_family,
                record_id,
            )
            if recommendation_draft.recommendation_draft.get("status") != "ready":
                raise ValueError(
                    "reviewed advisory context is not ready for approval-bound action requests"
                )

            recommendation_id = self._service._require_single_recommendation_binding(
                record_family=record_family,
                record_id=record_id,
                linked_recommendation_ids=recommendation_draft.linked_recommendation_ids,
            )
            case_id = self._service._require_single_linked_case_id(
                recommendation_draft.linked_case_ids
            )
            case = self._service._require_phase19_operator_case(case_id)
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
                {
                    "payload_hash": payload_hash,
                    "record_family": record_family,
                    "record_id": record_id,
                    "requester_identity": requester_identity,
                    "expires_at": expires_at.isoformat(),
                },
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
                        logging.INFO,
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
                )
            )
        self._service._emit_structured_event(
            logging.INFO,
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

    def delegate_approved_action_to_shuffle(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._delegate_approved_action(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
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

    def delegate_approved_action_to_isolated_executor(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._delegate_approved_action(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
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
        compared_at = self._service._require_aware_datetime(compared_at, "compared_at")
        stale_after = self._service._require_aware_datetime(stale_after, "stale_after")
        execution_surface_type = self._service._require_non_empty_string(
            execution_surface_type,
            "execution_surface_type",
        )
        execution_surface_id = self._service._require_non_empty_string(
            execution_surface_id,
            "execution_surface_id",
        )
        action_request = self._service._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        if action_request.lifecycle_state != "approved":
            raise ValueError(
                f"Action request {action_request_id!r} is not approved "
                f"(state={action_request.lifecycle_state!r})"
            )

        require_binding_identifiers = (
            execution_surface_type == "automation_substrate"
            and execution_surface_id == "shuffle"
        )
        normalized_executions = self._normalize_observed_executions(
            observed_executions,
            require_binding_identifiers=require_binding_identifiers,
        )
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
            evidence_ids = self._service._merge_linked_ids(
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
            observed_approval_decision_id = latest_execution.get("approval_decision_id")
            observed_delegation_id = latest_execution.get("delegation_id")
            observed_payload_hash = latest_execution.get("payload_hash")
            expected_execution_run_id = (
                None
                if authoritative_execution is None
                else authoritative_execution.execution_run_id
            )
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
            elif (
                expected_execution_run_id is not None
                and execution_run_id != expected_execution_run_id
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "execution run identity mismatch between authoritative action execution "
                    "and observed downstream execution"
                )
            elif (
                authoritative_execution is not None
                and authoritative_execution.execution_surface_type == "automation_substrate"
                and authoritative_execution.execution_surface_id == "shuffle"
                and (
                    observed_approval_decision_id
                    != authoritative_execution.approval_decision_id
                    or observed_delegation_id != authoritative_execution.delegation_id
                    or observed_payload_hash != authoritative_execution.payload_hash
                )
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "approved binding mismatch between authoritative action execution "
                    "and observed downstream execution"
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
                authoritative_execution = self._service.persist_record(
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

        reconciliation = self._service.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._service._next_identifier("reconciliation"),
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
        self._service._emit_structured_event(
            logging.INFO,
            "action_execution_reconciled",
            reconciliation_id=reconciliation.reconciliation_id,
            action_request_id=action_request.action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            ingest_disposition=reconciliation.ingest_disposition,
            lifecycle_state=reconciliation.lifecycle_state,
            execution_run_id=reconciliation.execution_run_id,
        )
        return reconciliation

    def _delegate_approved_action(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...],
        execution_surface_type: str,
        execution_surface_id: str,
        invalid_execution_surface_type_message: str,
        invalid_execution_surface_id_message: str,
        delegation_label: str,
    ) -> ActionExecutionRecord:
        delegated_at = self._service._require_aware_datetime(delegated_at, "delegated_at")
        action_request_id = self._service._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        delegation_issuer = self._service._require_non_empty_string(
            delegation_issuer,
            "delegation_issuer",
        )
        normalized_payload = self._service._require_mapping(
            approved_payload,
            "approved_payload",
        )
        adapter = (
            self._service._shuffle
            if execution_surface_id == "shuffle"
            else self._service._isolated_executor
        )
        predispatch_execution: ActionExecutionRecord
        action_request: ActionRequestRecord
        approval_decision: ApprovalDecisionRecord
        approval_decision_id: str
        with self._service._store.transaction():
            action_request, approval_decision = self._load_approved_delegation_context(
                action_request_id=action_request_id,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
                execution_surface_type=execution_surface_type,
                execution_surface_id=execution_surface_id,
                invalid_execution_surface_type_message=(
                    invalid_execution_surface_type_message
                ),
                invalid_execution_surface_id_message=(
                    invalid_execution_surface_id_message
                ),
                delegation_label=delegation_label,
            )
            approval_decision_id = approval_decision.approval_decision_id
            for existing in self._service._store.list(ActionExecutionRecord):
                if (
                    existing.action_request_id == action_request.action_request_id
                    and existing.execution_surface_type == execution_surface_type
                    and existing.execution_surface_id == execution_surface_id
                    and existing.idempotency_key == action_request.idempotency_key
                ):
                    if existing.lifecycle_state == "dispatching":
                        raise RuntimeError(
                            "approved action delegation is already dispatching"
                        )
                    return existing
            if execution_surface_id == "shuffle":
                self._require_reviewed_phase20_shuffle_payload(normalized_payload)

            delegation_id = self._service._next_identifier("delegation")
            predispatch_execution = self._service.persist_record(
                ActionExecutionRecord(
                    action_execution_id=self._service._next_identifier("action-execution"),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval_decision_id,
                    delegation_id=delegation_id,
                    execution_surface_type=execution_surface_type,
                    execution_surface_id=execution_surface_id,
                    execution_run_id=self._pending_dispatch_execution_run_id(
                        delegation_id
                    ),
                    idempotency_key=action_request.idempotency_key,
                    target_scope=action_request.target_scope,
                    approved_payload=normalized_payload,
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=action_request.expires_at,
                    provenance={
                        "delegation_issuer": delegation_issuer,
                        "evidence_ids": evidence_ids,
                    },
                    lifecycle_state="dispatching",
                )
            )
        receipt = None
        try:
            receipt = adapter.dispatch_approved_action(
                delegation_id=delegation_id,
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval_decision_id,
                payload_hash=action_request.payload_hash,
                idempotency_key=action_request.idempotency_key,
                approved_payload=normalized_payload,
                delegated_at=delegated_at,
            )
            self._require_exact_adapter_receipt_binding(
                receipt=receipt,
                action_request=action_request,
                approval_decision_id=approval_decision_id,
                delegation_id=delegation_id,
                execution_surface_type=execution_surface_type,
                execution_surface_id=execution_surface_id,
            )
        except Exception as exc:
            self._mark_dispatch_failure(
                execution=predispatch_execution,
                error=exc,
                receipt=receipt,
            )
            raise

        with self._service._store.transaction():
            stored_execution = self._service._store.get(
                ActionExecutionRecord,
                predispatch_execution.action_execution_id,
            )
            if stored_execution is None:
                raise LookupError(
                    "missing pre-dispatch action execution record during delegation finalization"
                )
            execution = self._service.persist_record(
                replace(
                    stored_execution,
                    execution_run_id=receipt.execution_run_id,
                    provenance=self._finalized_execution_provenance(
                        execution=stored_execution,
                        receipt=receipt,
                        execution_surface_id=execution_surface_id,
                    ),
                    lifecycle_state="queued",
                )
            )
        self._service._emit_action_execution_delegated_event(execution)
        return execution

    @staticmethod
    def _pending_dispatch_execution_run_id(delegation_id: str) -> str:
        return f"pending-dispatch-{delegation_id}"

    def _require_reviewed_phase20_shuffle_payload(
        self,
        approved_payload: Mapping[str, object],
    ) -> None:
        action_type = approved_payload.get("action_type")
        if action_type != "notify_identity_owner":
            raise ValueError(
                "approved action is outside the reviewed Phase 20 Shuffle delegation scope"
            )

        for field_name in (
            "recipient_identity",
            "message_intent",
            "escalation_reason",
        ):
            value = approved_payload.get(field_name)
            if not isinstance(value, str) or value.strip() == "":
                raise ValueError(
                    "approved action is outside the reviewed Phase 20 Shuffle delegation scope"
                )

    def _require_exact_adapter_receipt_binding(
        self,
        *,
        receipt: object,
        action_request: ActionRequestRecord,
        approval_decision_id: str,
        delegation_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
    ) -> None:
        if getattr(receipt, "execution_surface_type", None) != execution_surface_type:
            raise ValueError("adapter receipt does not match approved execution surface")
        if getattr(receipt, "execution_surface_id", None) != execution_surface_id:
            raise ValueError("adapter receipt does not match approved execution surface")
        if execution_surface_id == "shuffle" and any(
            (
                getattr(receipt, "approval_decision_id", None) != approval_decision_id,
                getattr(receipt, "delegation_id", None) != delegation_id,
                getattr(receipt, "payload_hash", None) != action_request.payload_hash,
            )
        ):
            raise ValueError(
                "shuffle receipt does not match approved delegation binding"
            )

    def _finalized_execution_provenance(
        self,
        *,
        execution: ActionExecutionRecord,
        receipt: object,
        execution_surface_id: str,
    ) -> dict[str, object]:
        provenance = dict(execution.provenance)
        provenance["adapter"] = getattr(receipt, "adapter")
        base_url = getattr(receipt, "base_url", "")
        if isinstance(base_url, str) and base_url.strip() and base_url != "<set-me>":
            provenance["adapter_base_url"] = base_url
        if execution_surface_id == "shuffle":
            provenance["downstream_binding"] = {
                "approval_decision_id": getattr(receipt, "approval_decision_id"),
                "delegation_id": getattr(receipt, "delegation_id"),
                "payload_hash": getattr(receipt, "payload_hash"),
            }
        return provenance

    def _mark_dispatch_failure(
        self,
        *,
        execution: ActionExecutionRecord,
        error: Exception,
        receipt: object | None,
    ) -> None:
        failure_provenance = dict(execution.provenance)
        dispatch_failure = {
            "error": str(error),
            "error_type": type(error).__name__,
        }
        if receipt is not None:
            adapter = getattr(receipt, "adapter", None)
            if isinstance(adapter, str) and adapter.strip():
                failure_provenance["adapter"] = adapter
            base_url = getattr(receipt, "base_url", None)
            if isinstance(base_url, str) and base_url.strip() and base_url != "<set-me>":
                failure_provenance["adapter_base_url"] = base_url
            observed_surface_type = getattr(receipt, "execution_surface_type", None)
            observed_surface_id = getattr(receipt, "execution_surface_id", None)
            if isinstance(observed_surface_type, str) and observed_surface_type.strip():
                dispatch_failure["observed_execution_surface_type"] = (
                    observed_surface_type
                )
            if isinstance(observed_surface_id, str) and observed_surface_id.strip():
                dispatch_failure["observed_execution_surface_id"] = observed_surface_id

        failure_provenance["dispatch_failure"] = dispatch_failure
        with self._service._store.transaction():
            current_execution = self._service._store.get(
                ActionExecutionRecord,
                execution.action_execution_id,
            )
            if current_execution is None or current_execution.lifecycle_state != "dispatching":
                return
            self._service.persist_record(
                replace(
                    current_execution,
                    provenance=failure_provenance,
                    lifecycle_state="failed",
                )
            )

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
            for execution in self._service._store.list(ActionExecutionRecord)
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

    def _normalize_observed_executions(
        self,
        observed_executions: tuple[Mapping[str, object], ...],
        *,
        require_binding_identifiers: bool = False,
    ) -> tuple[dict[str, object], ...]:
        normalized: list[dict[str, object]] = []
        for execution in observed_executions:
            execution_run_id = execution.get("execution_run_id")
            execution_surface_id = execution.get("execution_surface_id")
            idempotency_key = execution.get("idempotency_key")
            observed_at = execution.get("observed_at")
            approval_decision_id = execution.get("approval_decision_id")
            delegation_id = execution.get("delegation_id")
            payload_hash = execution.get("payload_hash")
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
            observed_at = self._service._require_aware_datetime(observed_at, "observed_at")
            if require_binding_identifiers:
                if not isinstance(approval_decision_id, str):
                    raise ValueError(
                        "observed execution must include string approval_decision_id"
                    )
                if not isinstance(delegation_id, str):
                    raise ValueError("observed execution must include string delegation_id")
                if not isinstance(payload_hash, str):
                    raise ValueError("observed execution must include string payload_hash")
            normalized.append(
                {
                    "execution_run_id": execution_run_id,
                    "execution_surface_id": execution_surface_id,
                    "idempotency_key": idempotency_key,
                    "observed_at": observed_at,
                    "approval_decision_id": approval_decision_id,
                    "delegation_id": delegation_id,
                    "payload_hash": payload_hash,
                    "status": execution.get("status"),
                }
            )

        normalized.sort(key=lambda execution: execution["observed_at"])
        return tuple(normalized)

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
        action_request = self._service._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        if action_request.lifecycle_state != "approved":
            raise ValueError(
                f"Action request {action_request_id!r} is not approved "
                f"(state={action_request.lifecycle_state!r})"
            )
        approval_decision_id = self._service._require_non_empty_string(
            action_request.approval_decision_id,
            "action_request.approval_decision_id",
        )
        approval_decision = self._service._store.get(
            ApprovalDecisionRecord,
            approval_decision_id,
        )
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

    def _require_exact_approved_expiry_binding(
        self,
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

    def _require_exact_approved_payload_binding(
        self,
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
