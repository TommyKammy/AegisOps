#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import pathlib
import sys
import time
from typing import Mapping, Sequence


container_control_plane_root = pathlib.Path("/opt/aegisops/control-plane")
default_control_plane_root = (
    container_control_plane_root
    if container_control_plane_root.is_dir()
    else pathlib.Path(__file__).resolve().parents[3]
)
CONTROL_PLANE_ROOT = pathlib.Path(
    os.environ.get(
        "AEGISOPS_CONTROL_PLANE_SOURCE_ROOT",
        str(default_control_plane_root),
    )
)
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.adapters.shuffle_real import (
    ShuffleReceiptPollingClient,
    ShuffleTransportFailure,
    UrllibShuffleJsonTransport,
)
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ReconciliationRecord,
)
from aegisops.control_plane.reporting.audit_export import (
    export_audit_retention_baseline,
)
from aegisops.control_plane.service import AegisOpsControlPlaneService


REVIEWED_SHUFFLE_APP_IMAGE = "frikky/shuffle:shuffle-tools_1.2.0"
REVIEWED_SHUFFLE_APP_IMAGE_DIGEST = (
    "sha256:fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8"
)
REVIEWED_SHUFFLE_APP_IMAGE_IMMUTABLE_REF = (
    "frikky/shuffle@" + REVIEWED_SHUFFLE_APP_IMAGE_DIGEST
)
REQUESTER_IDENTITY = "phase67-lab-requester"
APPROVER_IDENTITY = "phase67-lab-approver"
REVIEWED_ACTION_ID = "phase67-harmless-local-log-action"
REVIEWED_ACTION_NAME = "Harmless local log"
RESTART_RECORD_TYPES = {
    "aegisops_alert_id": AlertRecord,
    "case_id": CaseRecord,
    "denied_action_request_id": ActionRequestRecord,
    "denied_approval_decision_id": ApprovalDecisionRecord,
    "action_request_id": ActionRequestRecord,
    "approval_decision_id": ApprovalDecisionRecord,
    "action_execution_id": ActionExecutionRecord,
    "reconciliation_id": ReconciliationRecord,
}


class _StaticTransport:
    def __init__(self, response: object) -> None:
        self.response = response

    def request_json(self, **_kwargs: object) -> object:
        return self.response


def _approved_binding_hash(
    *,
    target_scope: object,
    approved_payload: object,
) -> str:
    encoded = json.dumps(
        {
            "approved_payload": approved_payload,
            "execution_surface_id": "shuffle",
            "execution_surface_type": "automation_substrate",
            "target_scope": target_scope,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_lab_config() -> RuntimeConfig:
    config = RuntimeConfig.from_env()
    if config.deployment_profile != "phase67-integration-lab":
        raise RuntimeError("real E2E journey requires the Phase 67 lab profile")
    if config.shuffle_transport_mode != "real_http":
        raise RuntimeError("real Shuffle transport is not enabled")
    expected = {
        "AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE": REVIEWED_SHUFFLE_APP_IMAGE,
        "AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST": (
            REVIEWED_SHUFFLE_APP_IMAGE_DIGEST
        ),
        "AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_IMMUTABLE_REF": (
            REVIEWED_SHUFFLE_APP_IMAGE_IMMUTABLE_REF
        ),
    }
    for name, expected_value in expected.items():
        if os.environ.get(name) != expected_value:
            raise RuntimeError(f"{name} is not the reviewed Shuffle artifact")
    return config


def _identifiers_for_trial(trial_id: str) -> dict[str, str]:
    suffix = hashlib.sha256(trial_id.encode("utf-8")).hexdigest()[:20]
    return {
        "case_id": f"phase67-case-{suffix}",
        "denied_action_request_id": f"phase67-denied-action-{suffix}",
        "denied_approval_decision_id": f"phase67-denied-approval-{suffix}",
        "action_request_id": f"phase67-action-{suffix}",
        "approval_decision_id": f"phase67-approval-{suffix}",
        "correlation_id": f"phase67-correlation-{suffix}",
        "expected_receipt_id": f"phase67-receipt-{suffix}",
        "idempotency_key": f"phase67-idempotency-{suffix}",
        "report_id": f"phase67-report-{suffix}",
    }


def _binding_and_payload(
    *,
    correlation_id: str,
    expected_receipt_id: str,
    target_scope: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    binding: dict[str, object] = {
        "workflow_id": "notify_identity_owner",
        "workflow_version_id": "notify_identity_owner-v1-reviewed-2026-05-03",
        "correlation_id": correlation_id,
        "expected_execution_receipt_id": expected_receipt_id,
        "requested_scope": dict(target_scope),
    }
    payload: dict[str, object] = {
        "action_type": "notify_identity_owner",
        "recipient_identity": "local-test-sink",
        "message_intent": "Write one harmless local Shuffle echo.",
        "escalation_reason": "Phase 67.4 real-service E2E trial.",
        "shuffle_delegation_binding": binding,
    }
    return binding, payload


def _persist_action_request(
    service: AegisOpsControlPlaneService,
    *,
    action_request_id: str,
    case: CaseRecord,
    idempotency_key: str,
    target_scope: Mapping[str, object],
    payload: Mapping[str, object],
    payload_hash: str,
    requested_at: datetime,
) -> ActionRequestRecord:
    return service.persist_record(
        ActionRequestRecord(
            action_request_id=action_request_id,
            approval_decision_id=None,
            case_id=case.case_id,
            alert_id=case.alert_id,
            finding_id=case.finding_id,
            idempotency_key=idempotency_key,
            target_scope=target_scope,
            payload_hash=payload_hash,
            requested_at=requested_at,
            expires_at=requested_at + timedelta(minutes=30),
            lifecycle_state="pending_approval",
            requester_identity=REQUESTER_IDENTITY,
            requested_payload=payload,
            policy_basis={
                "scope": "harmless_local_echo_only",
                "authority_posture": "human_approval_required",
            },
            policy_evaluation={
                "policy_decision": "allowed",
                "approval_requirement": "human_required",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        ),
        transitioned_at=requested_at,
    )


def _prove_denied_action_non_dispatch(
    service: AegisOpsControlPlaneService,
    *,
    identifiers: Mapping[str, str],
    case: CaseRecord,
    target_scope: Mapping[str, object],
    requested_at: datetime,
) -> dict[str, object]:
    binding, payload = _binding_and_payload(
        correlation_id=f"denied-{identifiers['correlation_id']}",
        expected_receipt_id=f"denied-{identifiers['expected_receipt_id']}",
        target_scope=target_scope,
    )
    payload_hash = _approved_binding_hash(
        target_scope=target_scope,
        approved_payload=payload,
    )
    action = _persist_action_request(
        service,
        action_request_id=identifiers["denied_action_request_id"],
        case=case,
        idempotency_key=f"denied-{identifiers['idempotency_key']}",
        target_scope=target_scope,
        payload=payload,
        payload_hash=payload_hash,
        requested_at=requested_at,
    )
    decision = service.persist_record(
        ApprovalDecisionRecord(
            approval_decision_id=identifiers["denied_approval_decision_id"],
            action_request_id=action.action_request_id,
            approver_identities=(APPROVER_IDENTITY,),
            target_snapshot=target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at + timedelta(seconds=1),
            lifecycle_state="rejected",
            decision_rationale="Denied control action for Phase 67.4 proof.",
            approved_expires_at=None,
        ),
        transitioned_at=requested_at + timedelta(seconds=1),
    )
    service.persist_record(
        replace(
            action,
            approval_decision_id=decision.approval_decision_id,
            lifecycle_state="rejected",
        ),
        transitioned_at=requested_at + timedelta(seconds=1),
    )
    rejected = False
    try:
        service.delegate_approved_action_to_shuffle(
            action_request_id=action.action_request_id,
            approved_payload=payload,
            delegated_at=requested_at + timedelta(seconds=2),
            delegation_issuer=REQUESTER_IDENTITY,
            evidence_ids=("phase67-4-denied-action-proof",),
        )
    except ValueError as exc:
        if "is not approved" not in str(exc):
            raise
        rejected = True
    execution_count = sum(
        record.action_request_id == action.action_request_id
        for record in service._store.list(ActionExecutionRecord)
    )
    if not rejected or execution_count != 0:
        raise RuntimeError("denied action reached the execution surface")
    return {
        "binding_reviewed": binding["workflow_id"] == "notify_identity_owner",
        "dispatch_rejected": rejected,
        "execution_count": execution_count,
    }


def _poll_real_receipt(
    *,
    config: RuntimeConfig,
    execution: ActionExecutionRecord,
    idempotency_key: str,
    expected_binding: Mapping[str, object],
) -> Mapping[str, object]:
    client = ShuffleReceiptPollingClient(
        base_url=config.shuffle_base_url,
        api_key=config.shuffle_api_key,
        api_workflow_id=config.shuffle_api_workflow_id,
        transport=UrllibShuffleJsonTransport(config.shuffle_ca_file),
    )
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            receipt = client.poll_normalized_receipt(
                execution_id=execution.execution_run_id,
                idempotency_key=idempotency_key,
                expected_binding=expected_binding,
                observed_at=datetime.now(timezone.utc),
            )
        except ShuffleTransportFailure as exc:
            if exc.category != "missing_receipt" and not exc.transient:
                raise
            time.sleep(2)
            continue
        if receipt["status"] == "running":
            time.sleep(2)
            continue
        return receipt
    raise RuntimeError("Shuffle receipt polling timed out")


def _run_receipt_negative_probes(
    *,
    config: RuntimeConfig,
    execution_id: str,
    idempotency_key: str,
    expected_binding: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    argument = {**expected_binding, "idempotency_key": idempotency_key}

    def probe(response: object) -> tuple[str, str]:
        client = ShuffleReceiptPollingClient(
            base_url=config.shuffle_base_url,
            api_key=config.shuffle_api_key,
            api_workflow_id=config.shuffle_api_workflow_id,
            transport=_StaticTransport(response),
        )
        try:
            receipt = client.poll_normalized_receipt(
                execution_id=execution_id,
                idempotency_key=idempotency_key,
                expected_binding=expected_binding,
                observed_at=datetime.now(timezone.utc),
            )
        except ShuffleTransportFailure as exc:
            return "rejected", exc.category
        if receipt["status"] == "failed":
            return "contained", "failed_receipt_not_reconciled"
        raise RuntimeError("negative receipt probe unexpectedly succeeded")

    failed_response = {
        "executions": [
            {
                "execution_id": execution_id,
                "execution_argument": argument,
                "status": "FAILED",
                "results": [],
            }
        ]
    }
    malformed_response = {
        "executions": [
            {
                "execution_id": execution_id,
                "execution_argument": "{",
                "status": "FINISHED",
                "results": [],
            }
        ]
    }
    mismatched_argument = dict(argument)
    mismatched_argument["payload_hash"] = "0" * 64
    mismatch_response = {
        "executions": [
            {
                "execution_id": execution_id,
                "execution_argument": mismatched_argument,
                "status": "FINISHED",
                "results": [
                    {
                        "action": {
                            "id": REVIEWED_ACTION_ID,
                            "name": REVIEWED_ACTION_NAME,
                        },
                        "status": "SUCCESS",
                    }
                ],
            }
        ]
    }
    result: dict[str, dict[str, object]] = {}
    for name, response in (
        ("failed_execution", failed_response),
        ("malformed_receipt", malformed_response),
        ("reconciliation_mismatch", mismatch_response),
    ):
        status, category = probe(response)
        result[name] = {
            "status": status,
            "category": category,
            "authority_delta": 0,
        }
    return result


def _execute(args: argparse.Namespace) -> dict[str, object]:
    config = _require_lab_config()
    service = AegisOpsControlPlaneService(config)
    alert = service.get_record(AlertRecord, args.alert_id)
    if alert is None:
        raise RuntimeError(f"admitted AegisOps alert {args.alert_id!r} is missing")
    identifiers = _identifiers_for_trial(args.trial_id)
    case = service.promote_alert_to_case(
        alert.alert_id,
        case_id=identifiers["case_id"],
    )
    now = datetime.now(timezone.utc) - timedelta(seconds=5)
    target_scope = {
        "record_family": "case",
        "record_id": case.case_id,
        "finding_id": case.finding_id,
        "recipient_identity": "local-test-sink",
    }
    denied = _prove_denied_action_non_dispatch(
        service,
        identifiers=identifiers,
        case=case,
        target_scope=target_scope,
        requested_at=now,
    )
    binding, payload = _binding_and_payload(
        correlation_id=identifiers["correlation_id"],
        expected_receipt_id=identifiers["expected_receipt_id"],
        target_scope=target_scope,
    )
    payload_hash = _approved_binding_hash(
        target_scope=target_scope,
        approved_payload=payload,
    )
    action = _persist_action_request(
        service,
        action_request_id=identifiers["action_request_id"],
        case=case,
        idempotency_key=identifiers["idempotency_key"],
        target_scope=target_scope,
        payload=payload,
        payload_hash=payload_hash,
        requested_at=now + timedelta(seconds=3),
    )
    approval = service.persist_record(
        ApprovalDecisionRecord(
            approval_decision_id=identifiers["approval_decision_id"],
            action_request_id=action.action_request_id,
            approver_identities=(APPROVER_IDENTITY,),
            target_snapshot=target_scope,
            payload_hash=payload_hash,
            decided_at=now + timedelta(seconds=4),
            lifecycle_state="approved",
            decision_rationale="Reviewed harmless Phase 67.4 local echo.",
            approved_expires_at=action.expires_at,
        ),
        transitioned_at=now + timedelta(seconds=4),
    )
    service.persist_record(
        replace(
            action,
            approval_decision_id=approval.approval_decision_id,
            lifecycle_state="approved",
        ),
        transitioned_at=now + timedelta(seconds=4),
    )
    execution = service.delegate_approved_action_to_shuffle(
        action_request_id=action.action_request_id,
        approved_payload=payload,
        delegated_at=now + timedelta(seconds=5),
        delegation_issuer=REQUESTER_IDENTITY,
        evidence_ids=("phase67-4-real-service-e2e",),
    )
    if execution.execution_run_id.startswith("shuffle-run-"):
        raise RuntimeError("synthetic execution ID cannot be live evidence")
    expected_binding = {
        "action_request_id": action.action_request_id,
        "approval_decision_id": approval.approval_decision_id,
        "delegation_id": execution.delegation_id,
        "payload_hash": payload_hash,
        **binding,
        "delegated_at": execution.delegated_at.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "action": {
            "action_type": payload["action_type"],
            "recipient_identity": payload["recipient_identity"],
            "message_intent": payload["message_intent"],
            "escalation_reason": payload["escalation_reason"],
        },
    }
    receipt = _poll_real_receipt(
        config=config,
        execution=execution,
        idempotency_key=action.idempotency_key,
        expected_binding=expected_binding,
    )
    compared_at = datetime.now(timezone.utc)
    reconciliation = service.reconcile_action_execution(
        action_request_id=action.action_request_id,
        execution_surface_type="automation_substrate",
        execution_surface_id="shuffle",
        observed_executions=(receipt,),
        compared_at=compared_at,
        stale_after=compared_at + timedelta(minutes=5),
    )
    replay = service.reconcile_action_execution(
        action_request_id=action.action_request_id,
        execution_surface_type="automation_substrate",
        execution_surface_id="shuffle",
        observed_executions=(receipt,),
        compared_at=compared_at + timedelta(seconds=1),
        stale_after=compared_at + timedelta(minutes=5),
    )
    stored_execution = service.get_record(
        ActionExecutionRecord,
        execution.action_execution_id,
    )
    if stored_execution is None:
        raise RuntimeError("persisted action execution is missing")
    if receipt["status"] == "failed":
        raise RuntimeError("real Shuffle execution failed")
    if reconciliation.ingest_disposition != "matched":
        raise RuntimeError("real Shuffle receipt did not match AegisOps binding")
    if replay.reconciliation_id != reconciliation.reconciliation_id:
        raise RuntimeError("receipt replay created a second reconciliation")
    negatives = _run_receipt_negative_probes(
        config=config,
        execution_id=execution.execution_run_id,
        idempotency_key=action.idempotency_key,
        expected_binding=expected_binding,
    )
    report = export_audit_retention_baseline(
        store=service._store,
        record_types=(
            AlertRecord,
            CaseRecord,
            ActionRequestRecord,
            ApprovalDecisionRecord,
            ActionExecutionRecord,
            ReconciliationRecord,
        ),
        export_id=identifiers["report_id"],
        exported_at=datetime.now(timezone.utc),
    )
    report_payload = json.dumps(report, separators=(",", ":"), sort_keys=True)
    return {
        "journey": {
            "trial_run_id": args.trial_id,
            "alert_id": alert.alert_id,
            "finding_id": alert.finding_id,
            "case_id": case.case_id,
            "requester_identity": REQUESTER_IDENTITY,
            "approver_identity": APPROVER_IDENTITY,
            "denied_action_request_id": identifiers["denied_action_request_id"],
            "denied_approval_decision_id": identifiers[
                "denied_approval_decision_id"
            ],
            "denied_dispatch": denied,
            "action_request_id": action.action_request_id,
            "approval_decision_id": approval.approval_decision_id,
            "delegation_id": execution.delegation_id,
            "workflow_id": config.shuffle_api_workflow_id,
            "workflow_version": binding["workflow_version_id"],
            "execution_id": execution.execution_run_id,
            "expected_receipt_id": identifiers["expected_receipt_id"],
            "action_execution_id": execution.action_execution_id,
            "reconciliation_id": reconciliation.reconciliation_id,
            "replay_reconciliation_id": replay.reconciliation_id,
            "idempotency_execution_count": receipt[
                "idempotency_execution_count"
            ],
            "receipt_identity_preserved": (
                receipt["external_receipt_id"]
                == identifiers["expected_receipt_id"]
            ),
            "reconciliation_disposition": reconciliation.ingest_disposition,
            "negative_probes": negatives,
            "report_id": identifiers["report_id"],
            "report_sha256": hashlib.sha256(
                report_payload.encode("utf-8")
            ).hexdigest(),
        },
        "report": report,
    }


def _verify_restart(args: argparse.Namespace) -> dict[str, object]:
    config = _require_lab_config()
    service = AegisOpsControlPlaneService(config)
    payload = json.load(sys.stdin)
    if not isinstance(payload, Mapping):
        raise RuntimeError("restart input must be a journey object")
    checked: list[str] = []
    for field_name, record_type in RESTART_RECORD_TYPES.items():
        value = payload.get(field_name)
        if not isinstance(value, str) or value.strip() == "":
            raise RuntimeError(f"restart input is missing {field_name}")
        if service.get_record(record_type, value) is None:
            raise RuntimeError(f"restart lost {field_name}={value}")
        checked.append(field_name)
    action_request_id = payload["action_request_id"]
    execution_count = sum(
        record.action_request_id == action_request_id
        for record in service._store.list(ActionExecutionRecord)
    )
    if execution_count != 1:
        raise RuntimeError("restart changed the idempotent execution count")
    return {
        "performed": True,
        "records_persisted": True,
        "checked_identifiers": checked,
        "shuffle_execution_count": execution_count,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--trial-id", required=True)
    execute.add_argument("--alert-id", required=True)
    subparsers.add_parser("verify-restart")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    output = _execute(args) if args.command == "execute" else _verify_restart(args)
    json.dump(output, sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    os.environ.setdefault(
        "AEGISOPS_CONTROL_PLANE_DEPLOYMENT_PROFILE",
        "phase67-integration-lab",
    )
    raise SystemExit(main())
