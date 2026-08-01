from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import pathlib
import sys
import time
from uuid import uuid4

CONTROL_PLANE_ROOT = pathlib.Path(
    os.environ.get(
        "AEGISOPS_CONTROL_PLANE_SOURCE_ROOT",
        "/opt/aegisops/control-plane",
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
    ApprovalDecisionRecord,
    ReconciliationRecord,
)
from aegisops.control_plane.service import AegisOpsControlPlaneService

REVIEWED_SHUFFLE_APP_IMAGE = "frikky/shuffle:shuffle-tools_1.2.0"
REVIEWED_SHUFFLE_APP_IMAGE_DIGEST = (
    "sha256:fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8"
)
REVIEWED_SHUFFLE_APP_IMAGE_IMMUTABLE_REF = (
    "frikky/shuffle@" + REVIEWED_SHUFFLE_APP_IMAGE_DIGEST
)


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


def main() -> int:
    config = RuntimeConfig.from_env()
    if config.deployment_profile != "phase67-integration-lab":
        raise RuntimeError("real Shuffle trial requires the Phase 67 lab profile")
    if config.shuffle_transport_mode != "real_http":
        raise RuntimeError("real Shuffle transport is not enabled")
    shuffle_app_image = os.environ.get("AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE", "")
    shuffle_app_image_digest = os.environ.get(
        "AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST",
        "",
    )
    shuffle_app_image_immutable_ref = os.environ.get(
        "AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_IMMUTABLE_REF",
        "",
    )
    if (
        shuffle_app_image != REVIEWED_SHUFFLE_APP_IMAGE
        or shuffle_app_image_digest != REVIEWED_SHUFFLE_APP_IMAGE_DIGEST
        or shuffle_app_image_immutable_ref
        != REVIEWED_SHUFFLE_APP_IMAGE_IMMUTABLE_REF
    ):
        raise RuntimeError("Shuffle trial app image is not the reviewed artifact")

    now = datetime.now(timezone.utc) - timedelta(seconds=5)
    trial_id = str(uuid4())
    action_request_id = f"phase67-action-{trial_id}"
    approval_decision_id = f"phase67-approval-{trial_id}"
    correlation_id = f"phase67-correlation-{trial_id}"
    expected_receipt_id = f"phase67-receipt-{trial_id}"
    idempotency_key = f"phase67-idempotency-{trial_id}"
    finding_id = f"phase67-finding-{trial_id}"
    target_scope = {
        "record_family": "phase67_lab_trial",
        "record_id": trial_id,
        "finding_id": finding_id,
        "recipient_identity": "local-test-sink",
    }
    binding = {
        "workflow_id": "notify_identity_owner",
        "workflow_version_id": (
            "notify_identity_owner-v1-reviewed-2026-05-03"
        ),
        "correlation_id": correlation_id,
        "expected_execution_receipt_id": expected_receipt_id,
        "requested_scope": target_scope,
    }
    approved_payload = {
        "action_type": "notify_identity_owner",
        "recipient_identity": "local-test-sink",
        "message_intent": "Write one harmless local Shuffle echo.",
        "escalation_reason": "Phase 67.3 real integration trial.",
        "shuffle_delegation_binding": binding,
    }
    payload_hash = _approved_binding_hash(
        target_scope=target_scope,
        approved_payload=approved_payload,
    )
    service = AegisOpsControlPlaneService(config)
    action_request = service.persist_record(
        ActionRequestRecord(
            action_request_id=action_request_id,
            approval_decision_id=None,
            case_id=None,
            alert_id=None,
            finding_id=finding_id,
            idempotency_key=idempotency_key,
            target_scope=target_scope,
            payload_hash=payload_hash,
            requested_at=now,
            expires_at=now + timedelta(minutes=30),
            lifecycle_state="pending_approval",
            requester_identity="phase67-lab-operator",
            requested_payload=approved_payload,
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
        transitioned_at=now,
    )
    approval = service.persist_record(
        ApprovalDecisionRecord(
            approval_decision_id=approval_decision_id,
            action_request_id=action_request_id,
            approver_identities=("phase67-lab-operator",),
            target_snapshot=target_scope,
            payload_hash=payload_hash,
            decided_at=now + timedelta(seconds=1),
            lifecycle_state="approved",
            decision_rationale="Reviewed harmless Phase 67.3 local echo.",
            approved_expires_at=action_request.expires_at,
        ),
        transitioned_at=now + timedelta(seconds=1),
    )
    service.persist_record(
        replace(
            action_request,
            approval_decision_id=approval.approval_decision_id,
            lifecycle_state="approved",
        ),
        transitioned_at=now + timedelta(seconds=1),
    )

    execution = service.delegate_approved_action_to_shuffle(
        action_request_id=action_request_id,
        approved_payload=approved_payload,
        delegated_at=now + timedelta(seconds=2),
        delegation_issuer="phase67-lab-operator",
        evidence_ids=("phase67-3-real-shuffle-trial",),
    )
    if execution.execution_run_id.startswith("shuffle-run-"):
        raise RuntimeError("synthetic execution id cannot be live evidence")

    polling_client = ShuffleReceiptPollingClient(
        base_url=config.shuffle_base_url,
        api_key=config.shuffle_api_key,
        api_workflow_id=config.shuffle_api_workflow_id,
        transport=UrllibShuffleJsonTransport(config.shuffle_ca_file),
    )
    expected_binding = {
        "action_request_id": action_request_id,
        "approval_decision_id": approval_decision_id,
        "delegation_id": execution.delegation_id,
        "payload_hash": payload_hash,
        **binding,
        "delegated_at": execution.delegated_at.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "action": {
            "action_type": approved_payload["action_type"],
            "recipient_identity": approved_payload["recipient_identity"],
            "message_intent": approved_payload["message_intent"],
            "escalation_reason": approved_payload["escalation_reason"],
        },
    }
    normalized_receipt = None
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            candidate = polling_client.poll_normalized_receipt(
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
        if candidate["status"] == "running":
            time.sleep(2)
            continue
        normalized_receipt = candidate
        break
    if normalized_receipt is None:
        raise RuntimeError("Shuffle receipt polling timed out")

    compared_at = datetime.now(timezone.utc)
    reconciliation = service.reconcile_action_execution(
        action_request_id=action_request_id,
        execution_surface_type="automation_substrate",
        execution_surface_id="shuffle",
        observed_executions=(normalized_receipt,),
        compared_at=compared_at,
        stale_after=compared_at + timedelta(minutes=5),
    )
    replay = service.reconcile_action_execution(
        action_request_id=action_request_id,
        execution_surface_type="automation_substrate",
        execution_surface_id="shuffle",
        observed_executions=(normalized_receipt,),
        compared_at=compared_at + timedelta(seconds=1),
        stale_after=compared_at + timedelta(minutes=5),
    )
    stored_execution = service.get_record(
        ActionExecutionRecord,
        execution.action_execution_id,
    )
    if stored_execution is None:
        raise RuntimeError("persisted action execution is missing")
    if replay.reconciliation_id != reconciliation.reconciliation_id:
        raise RuntimeError("duplicate receipt created a second reconciliation")
    if normalized_receipt["status"] == "failed":
        raise RuntimeError("Shuffle execution failed and remains unresolved")
    if reconciliation.ingest_disposition != "matched":
        raise RuntimeError("normalized receipt did not match authoritative binding")

    output = {
        "schema_version": "phase67.3-real-shuffle-trial-v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_mode": "real_shuffle",
        "workflow_api_id": config.shuffle_api_workflow_id,
        "reviewed_template_id": binding["workflow_id"],
        "reviewed_template_version": binding["workflow_version_id"],
        "shuffle_app_image": shuffle_app_image,
        "shuffle_app_image_digest": shuffle_app_image_digest,
        "shuffle_app_image_immutable_ref": shuffle_app_image_immutable_ref,
        "action_request_id": action_request_id,
        "approval_decision_id": approval_decision_id,
        "delegation_id": execution.delegation_id,
        "execution_id": execution.execution_run_id,
        "idempotency_key": idempotency_key,
        "idempotency_execution_count": normalized_receipt[
            "idempotency_execution_count"
        ],
        "correlation_id": correlation_id,
        "requested_scope": target_scope,
        "payload_hash": payload_hash,
        "expected_execution_receipt_id": expected_receipt_id,
        "action_execution_id": execution.action_execution_id,
        "normalized_receipt_sha256": stored_execution.provenance[
            "normalized_receipt"
        ]["sha256"],
        "reconciliation_id": reconciliation.reconciliation_id,
        "replay_reconciliation_id": replay.reconciliation_id,
        "execution_lifecycle_state": stored_execution.lifecycle_state,
        "reconciliation_disposition": reconciliation.ingest_disposition,
        "authority_posture": "aegisops_reconciliation_remains_authoritative",
        "limitations": [
            "isolated_non-production_lab",
            "harmless_local_echo_only",
            "single_reviewed_workflow",
        ],
    }
    json.dump(output, sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    os.environ.setdefault(
        "AEGISOPS_CONTROL_PLANE_DEPLOYMENT_PROFILE",
        "phase67-integration-lab",
    )
    raise SystemExit(main())
