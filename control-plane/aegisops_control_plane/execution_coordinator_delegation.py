from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Mapping

from .action_receipt_validation import (
    MissingReceiptValueError,
    require_receipt_https_url_value,
    require_receipt_string_value,
)
from .execution_coordinator import (
    ExecutionCoordinatorServiceDependencies,
    _PHASE26_REVIEWED_COORDINATION_TARGET_TYPES,
    _approved_payload_binding_hash,
)
from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
)


class ApprovedActionDelegationCoordinator:
    def __init__(self, service: ExecutionCoordinatorServiceDependencies) -> None:
        self._service = service

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
                self._require_reviewed_shuffle_payload(normalized_payload)

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
                ),
                transitioned_at=delegated_at,
            )
        receipt = None
        execution_run_id: str
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
            execution_run_id = self._require_receipt_string_attribute(
                receipt,
                "execution_run_id",
            )
        except Exception as exc:
            self._mark_dispatch_failure(
                execution=predispatch_execution,
                error=exc,
                receipt=receipt,
            )
            raise

        try:
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
                        execution_run_id=execution_run_id,
                        provenance=self._finalized_execution_provenance(
                            execution=stored_execution,
                            receipt=receipt,
                            execution_surface_id=execution_surface_id,
                        ),
                        lifecycle_state="queued",
                    ),
                    transitioned_at=delegated_at,
                )
        except Exception as exc:
            self._mark_dispatch_failure(
                execution=predispatch_execution,
                error=exc,
                receipt=receipt,
            )
            raise
        self._service._emit_action_execution_delegated_event(execution)
        return execution

    @staticmethod
    def _pending_dispatch_execution_run_id(delegation_id: str) -> str:
        return f"pending-dispatch-{delegation_id}"

    def _require_reviewed_shuffle_payload(
        self,
        approved_payload: Mapping[str, object],
    ) -> None:
        action_type = approved_payload.get("action_type")
        if action_type == "notify_identity_owner":
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
            return
        if action_type == "create_tracking_ticket":
            for field_name in (
                "case_id",
                "coordination_reference_id",
                "coordination_target_type",
                "ticket_title",
                "ticket_description",
            ):
                value = approved_payload.get(field_name)
                if not isinstance(value, str) or value.strip() == "":
                    raise ValueError(
                        "approved action is outside the reviewed Phase 26 Shuffle delegation scope"
                    )
            coordination_target_type = approved_payload.get("coordination_target_type")
            if (
                not isinstance(coordination_target_type, str)
                or coordination_target_type
                not in _PHASE26_REVIEWED_COORDINATION_TARGET_TYPES
            ):
                raise ValueError(
                    "approved action is outside the reviewed Phase 26 Shuffle delegation scope"
                )
            return
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
        if (
            execution_surface_id == "shuffle"
            and action_request.requested_payload.get("action_type")
            == "create_tracking_ticket"
        ):
            approved_coordination_reference_id = self._service._require_non_empty_string(
                action_request.target_scope.get("coordination_reference_id"),
                "action_request.target_scope.coordination_reference_id",
            )
            approved_coordination_target_type = self._service._require_non_empty_string(
                action_request.target_scope.get("coordination_target_type"),
                "action_request.target_scope.coordination_target_type",
            )
            if any(
                (
                    self._require_receipt_string_attribute(
                        receipt,
                        "coordination_reference_id",
                    )
                    != approved_coordination_reference_id,
                    self._require_receipt_string_attribute(
                        receipt,
                        "coordination_target_type",
                    )
                    != approved_coordination_target_type,
                )
            ):
                raise ValueError(
                    "shuffle receipt does not match approved delegation binding"
                )
            self._require_receipt_string_attribute(receipt, "external_receipt_id")
            self._require_receipt_string_attribute(receipt, "coordination_target_id")
            self._require_receipt_https_url_attribute(receipt, "ticket_reference_url")

    def _finalized_execution_provenance(
        self,
        *,
        execution: ActionExecutionRecord,
        receipt: object,
        execution_surface_id: str,
    ) -> dict[str, object]:
        provenance = dict(execution.provenance)
        provenance["adapter"] = self._require_receipt_string_attribute(
            receipt,
            "adapter",
        )
        base_url = getattr(receipt, "base_url", "")
        if isinstance(base_url, str) and base_url.strip() and base_url != "<set-me>":
            provenance["adapter_base_url"] = base_url
        if execution_surface_id == "shuffle":
            provenance["downstream_binding"] = {
                "approval_decision_id": self._require_receipt_string_attribute(
                    receipt,
                    "approval_decision_id",
                ),
                "delegation_id": self._require_receipt_string_attribute(
                    receipt,
                    "delegation_id",
                ),
                "payload_hash": self._require_receipt_string_attribute(
                    receipt,
                    "payload_hash",
                ),
            }
            if execution.approved_payload.get("action_type") == "create_tracking_ticket":
                provenance["downstream_binding"].update(
                    {
                        "coordination_reference_id": self._require_receipt_string_attribute(
                            receipt,
                            "coordination_reference_id",
                        ),
                        "coordination_target_type": self._require_receipt_string_attribute(
                            receipt,
                            "coordination_target_type",
                        ),
                        "external_receipt_id": self._require_receipt_string_attribute(
                            receipt,
                            "external_receipt_id",
                        ),
                        "coordination_target_id": self._require_receipt_string_attribute(
                            receipt,
                            "coordination_target_id",
                        ),
                        "ticket_reference_url": self._require_receipt_https_url_attribute(
                            receipt,
                            "ticket_reference_url",
                        ),
                    }
                )
        return provenance

    @staticmethod
    def _require_receipt_string_attribute(receipt: object, field_name: str) -> str:
        try:
            return require_receipt_string_value(
                getattr(receipt, field_name, None),
                field_name,
            )
        except MissingReceiptValueError as exc:
            raise ValueError(str(exc)) from exc

    @staticmethod
    def _require_receipt_https_url_attribute(receipt: object, field_name: str) -> str:
        try:
            return require_receipt_https_url_value(
                getattr(receipt, field_name, None),
                field_name,
            )
        except MissingReceiptValueError as exc:
            raise ValueError(str(exc)) from exc

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
        failure_at = datetime.now(timezone.utc)
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
                ),
                transitioned_at=failure_at,
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
