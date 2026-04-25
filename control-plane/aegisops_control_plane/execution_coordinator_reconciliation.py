from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import logging
from typing import Mapping

from .action_receipt_validation import (
    MissingReceiptValueError,
    require_receipt_https_url_value,
    require_receipt_string_value,
)
from .execution_coordinator import ExecutionCoordinatorServiceDependencies
from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ReconciliationRecord,
)


class ActionExecutionReconciliationCoordinator:
    def __init__(self, service: ExecutionCoordinatorServiceDependencies) -> None:
        self._service = service

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
        require_coordination_receipt_identifiers = (
            require_binding_identifiers
            and action_request.requested_payload.get("action_type")
            == "create_tracking_ticket"
        )
        normalized_executions = self._normalize_observed_executions(
            observed_executions,
            require_binding_identifiers=require_binding_identifiers,
            require_coordination_receipt_identifiers=(
                require_coordination_receipt_identifiers
            ),
        )
        linked_execution_run_ids = tuple(
            execution["execution_run_id"] for execution in normalized_executions
        )
        unique_execution_run_ids = tuple(dict.fromkeys(linked_execution_run_ids))
        has_duplicate_observations = len(linked_execution_run_ids) != len(
            unique_execution_run_ids
        )
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
            observed_coordination_reference_id = latest_execution.get(
                "coordination_reference_id"
            )
            observed_coordination_target_type = latest_execution.get(
                "coordination_target_type"
            )
            observed_external_receipt_id = latest_execution.get("external_receipt_id")
            observed_coordination_target_id = latest_execution.get(
                "coordination_target_id"
            )
            observed_ticket_reference_url = latest_execution.get("ticket_reference_url")
            expected_execution_run_id = (
                None
                if authoritative_execution is None
                else authoritative_execution.execution_run_id
            )
            if last_seen_at < stale_after and compared_at >= stale_after:
                ingest_disposition = "stale"
                lifecycle_state = "stale"
                mismatch_summary = "stale downstream execution observation requires refresh"
            elif has_duplicate_observations and require_coordination_receipt_identifiers:
                ingest_disposition = "duplicate"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "duplicate coordination receipts observed for one approved request"
                )
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
            elif (
                require_coordination_receipt_identifiers
                and authoritative_execution is None
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "coordination receipt mismatch between authoritative action execution "
                    "and observed downstream execution"
                )
            elif (
                authoritative_execution is not None
                and authoritative_execution.approved_payload.get("action_type")
                == "create_tracking_ticket"
                and authoritative_execution.execution_surface_type
                == "automation_substrate"
                and authoritative_execution.execution_surface_id == "shuffle"
                and (
                    observed_coordination_reference_id
                    != authoritative_execution.provenance.get(
                        "downstream_binding",
                        {},
                    ).get("coordination_reference_id")
                    or observed_coordination_target_type
                    != authoritative_execution.provenance.get(
                        "downstream_binding",
                        {},
                    ).get("coordination_target_type")
                    or observed_external_receipt_id
                    != authoritative_execution.provenance.get(
                        "downstream_binding",
                        {},
                    ).get("external_receipt_id")
                    or observed_coordination_target_id
                    != authoritative_execution.provenance.get(
                        "downstream_binding",
                        {},
                    ).get("coordination_target_id")
                    or observed_ticket_reference_url
                    != authoritative_execution.provenance.get(
                        "downstream_binding",
                        {},
                    ).get("ticket_reference_url")
                )
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "coordination receipt mismatch between authoritative action execution "
                    "and observed downstream execution"
                )
            else:
                ingest_disposition = "matched"
                lifecycle_state = "matched"
                mismatch_summary = (
                    "matched approved action request to reviewed execution run"
                )

        with self._service._store.transaction():
            if authoritative_execution is not None:
                stored_execution = self._service._store.get(
                    ActionExecutionRecord,
                    authoritative_execution.action_execution_id,
                )
                if stored_execution is None:
                    raise LookupError(
                        "missing authoritative action execution during reconciliation"
                    )
                authoritative_execution = stored_execution

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
                        replace(
                            authoritative_execution,
                            lifecycle_state=reconciled_lifecycle_state,
                        ),
                        transitioned_at=latest_execution["observed_at"],
                    )
            if (
                authoritative_execution is not None
                and authoritative_execution.approved_payload.get("action_type")
                == "create_tracking_ticket"
            ):
                downstream_binding = authoritative_execution.provenance.get(
                    "downstream_binding",
                    {},
                )
                if isinstance(downstream_binding, Mapping):
                    if isinstance(downstream_binding.get("coordination_reference_id"), str):
                        subject_linkage["coordination_reference_ids"] = (
                            downstream_binding["coordination_reference_id"],
                        )
                    if isinstance(downstream_binding.get("coordination_target_type"), str):
                        subject_linkage["coordination_target_types"] = (
                            downstream_binding["coordination_target_type"],
                        )
                    if isinstance(downstream_binding.get("external_receipt_id"), str):
                        subject_linkage["external_receipt_ids"] = (
                            downstream_binding["external_receipt_id"],
                        )
                    if isinstance(downstream_binding.get("coordination_target_id"), str):
                        subject_linkage["coordination_target_ids"] = (
                            downstream_binding["coordination_target_id"],
                        )
                    if isinstance(downstream_binding.get("ticket_reference_url"), str):
                        subject_linkage["ticket_reference_urls"] = (
                            downstream_binding["ticket_reference_url"],
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
                ),
                transitioned_at=compared_at,
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

    @staticmethod
    def _action_execution_lifecycle_from_status(
        status: object,
        current_lifecycle_state: str,
    ) -> str:
        if not isinstance(status, str):
            return current_lifecycle_state

        normalized_status = status.strip().lower()
        observed_state = {
            "queued": "queued",
            "pending": "queued",
            "running": "running",
            "in_progress": "running",
            "success": "succeeded",
            "succeeded": "succeeded",
            "completed": "succeeded",
            "failed": "failed",
            "error": "failed",
            "canceled": "canceled",
            "cancelled": "canceled",
        }.get(normalized_status)
        if observed_state is None:
            return current_lifecycle_state

        normalized_current_lifecycle_state = current_lifecycle_state.strip().lower()
        if normalized_current_lifecycle_state in {"succeeded", "failed", "canceled"}:
            return current_lifecycle_state

        lifecycle_rank = {
            "dispatching": 0,
            "queued": 1,
            "running": 2,
            "succeeded": 3,
            "failed": 3,
            "canceled": 3,
        }
        if lifecycle_rank[observed_state] >= lifecycle_rank.get(
            normalized_current_lifecycle_state,
            -1,
        ):
            return observed_state
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
        require_coordination_receipt_identifiers: bool = False,
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
            coordination_reference_id = execution.get("coordination_reference_id")
            coordination_target_type = execution.get("coordination_target_type")
            external_receipt_id = execution.get("external_receipt_id")
            coordination_target_id = execution.get("coordination_target_id")
            ticket_reference_url = execution.get("ticket_reference_url")
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
            if require_coordination_receipt_identifiers:
                try:
                    coordination_reference_id = require_receipt_string_value(
                        coordination_reference_id,
                        "coordination_reference_id",
                    )
                    coordination_target_type = require_receipt_string_value(
                        coordination_target_type,
                        "coordination_target_type",
                    )
                    external_receipt_id = require_receipt_string_value(
                        external_receipt_id,
                        "external_receipt_id",
                    )
                    coordination_target_id = require_receipt_string_value(
                        coordination_target_id,
                        "coordination_target_id",
                    )
                    ticket_reference_url = require_receipt_https_url_value(
                        ticket_reference_url,
                        "ticket_reference_url",
                    )
                except MissingReceiptValueError as exc:
                    raise ValueError(
                        f"observed execution must include string {exc.field_name}"
                    ) from exc
            normalized.append(
                {
                    "execution_run_id": execution_run_id,
                    "execution_surface_id": execution_surface_id,
                    "idempotency_key": idempotency_key,
                    "observed_at": observed_at,
                    "approval_decision_id": approval_decision_id,
                    "delegation_id": delegation_id,
                    "payload_hash": payload_hash,
                    "coordination_reference_id": coordination_reference_id,
                    "coordination_target_type": coordination_target_type,
                    "external_receipt_id": external_receipt_id,
                    "coordination_target_id": coordination_target_id,
                    "ticket_reference_url": ticket_reference_url,
                    "status": execution.get("status"),
                }
            )

        normalized.sort(key=lambda execution: execution["observed_at"])
        return tuple(normalized)
