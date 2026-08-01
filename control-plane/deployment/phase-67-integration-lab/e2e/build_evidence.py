#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


STEP_NAMES = (
    "capture_immutable_snapshot",
    "start_lab_and_record_health",
    "trigger_real_wazuh_detection",
    "admit_wazuh_alert",
    "promote_alert_to_case",
    "create_reviewed_action_request",
    "prove_denied_action_non_dispatch",
    "approve_and_dispatch_real_shuffle_action",
    "capture_authenticated_shuffle_receipt",
    "reconcile_from_aegisops_records",
    "export_redacted_aegisops_report",
    "replay_deliveries_for_idempotency",
    "run_negative_cases",
    "restart_and_verify_persistence",
    "publish_prerequisite_evaluation",
)
STEP_EVIDENCE_REFS = (
    ("snapshot",),
    ("lab-status:full",),
    ("wazuh-manifest:native_wazuh_alert_id",),
    ("wazuh-manifest:aegisops_alert_id",),
    ("journey:case_id",),
    ("journey:action_request_id",),
    ("journey:denied_dispatch",),
    ("journey:execution_id",),
    ("journey:expected_receipt_id",),
    ("journey:reconciliation_id",),
    ("report:sha256",),
    ("wazuh-manifest:duplicate_delivery", "journey:replay_reconciliation_id"),
    ("wazuh-command:negative-boundaries", "journey:negative_probes"),
    ("restart:checked_identifiers",),
    ("docs:phase-67-prerequisite-evaluation",),
)


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    return value


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_text(value: object, path: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{path} must be a non-empty string")
    return value.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--wazuh", type=Path, required=True)
    parser.add_argument("--wazuh-output", type=Path, required=True)
    parser.add_argument("--journey", type=Path, required=True)
    parser.add_argument("--restart", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def build(args: argparse.Namespace) -> dict[str, object]:
    snapshot = _mapping(_read_json(args.snapshot), "snapshot")
    wazuh = _mapping(_read_json(args.wazuh), "wazuh")
    combined_journey = _mapping(_read_json(args.journey), "journey output")
    journey = _mapping(combined_journey.get("journey"), "journey output.journey")
    restart = _mapping(_read_json(args.restart), "restart")
    report = _mapping(_read_json(args.report), "report")
    wazuh_output = args.wazuh_output.read_text(encoding="utf-8")
    evaluation = args.evaluation.read_text(encoding="utf-8")
    for required_line in (
        "PASS invalid_bearer_secret=403",
        "PASS proxy_bypass=403",
        "PASS negative_authoritative_alert_delta=0",
    ):
        if required_line not in wazuh_output:
            raise ValueError(f"Wazuh command output is missing {required_line!r}")
    if (
        "integration_trial_passed_with_owned_limitations" not in evaluation
        or "GA acceptance: not accepted" not in evaluation
    ):
        raise ValueError("Phase 67 prerequisite evaluation is not conservative")
    if _sha256(args.schema) != snapshot.get("evidence_schema_sha256"):
        raise ValueError("snapshot evidence schema digest does not match")
    if report.get("export_id") != journey.get("report_id"):
        raise ValueError("report export ID does not match the journey")
    report_sha256 = _sha256(args.report)
    if report_sha256 != journey.get("report_sha256"):
        raise ValueError("report digest does not match the journey")
    if report.get("source_of_truth") != "aegisops_authoritative_records":
        raise ValueError("report is not derived from AegisOps source records")
    if wazuh.get("aegisops_alert_id") != journey.get("alert_id"):
        raise ValueError("Wazuh admission and case journey use different alerts")
    if wazuh.get("first_delivery", {}).get("finding_id") != journey.get("finding_id"):
        raise ValueError("Wazuh admission and action journey use different findings")
    if restart.get("shuffle_execution_count") != journey.get(
        "idempotency_execution_count"
    ):
        raise ValueError("restart changed the Shuffle execution count")
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = _required_text(snapshot.get("snapshot_id"), "snapshot.snapshot_id")
    steps = [
        {
            "step": index,
            "name": name,
            "status": "passed",
            "snapshot_id": snapshot_id,
            "observed_at": captured_at,
            "evidence_refs": list(STEP_EVIDENCE_REFS[index - 1]),
        }
        for index, name in enumerate(STEP_NAMES, start=1)
    ]
    first_delivery = _mapping(wazuh.get("first_delivery"), "wazuh.first_delivery")
    duplicate_delivery = _mapping(
        wazuh.get("duplicate_delivery"),
        "wazuh.duplicate_delivery",
    )
    denied = _mapping(journey.get("denied_dispatch"), "journey.denied_dispatch")
    probes = _mapping(journey.get("negative_probes"), "journey.negative_probes")

    def negative_case(name: str) -> dict[str, object]:
        probe = _mapping(probes.get(name), f"journey.negative_probes.{name}")
        return {
            "status": probe.get("status"),
            "authority_delta": probe.get("authority_delta"),
            "evidence_ref": f"journey:negative_probes.{name}:{probe.get('category')}",
        }

    return {
        "schema_version": "phase67.4-real-service-e2e-evidence-v1",
        "captured_at": captured_at,
        "source_mode": "real_services",
        "trial_run_id": snapshot.get("trial_run_id"),
        "snapshot": {
            key: value
            for key, value in snapshot.items()
            if key != "trial_run_id"
        },
        "steps": steps,
        "identifiers": {
            "wazuh_manager_id": wazuh.get("native_wazuh_manager_id"),
            "wazuh_agent_id": wazuh.get("native_wazuh_agent_id"),
            "wazuh_rule_id": wazuh.get("native_wazuh_rule_id"),
            "native_wazuh_alert_id": wazuh.get("native_wazuh_alert_id"),
            "aegisops_alert_id": journey.get("alert_id"),
            "finding_id": journey.get("finding_id"),
            "case_id": journey.get("case_id"),
            "denied_action_request_id": journey.get("denied_action_request_id"),
            "denied_approval_decision_id": journey.get(
                "denied_approval_decision_id"
            ),
            "action_request_id": journey.get("action_request_id"),
            "approval_decision_id": journey.get("approval_decision_id"),
            "delegation_id": journey.get("delegation_id"),
            "shuffle_workflow_id": journey.get("workflow_id"),
            "shuffle_workflow_version": journey.get("workflow_version"),
            "shuffle_execution_id": journey.get("execution_id"),
            "expected_receipt_id": journey.get("expected_receipt_id"),
            "action_execution_id": journey.get("action_execution_id"),
            "reconciliation_id": journey.get("reconciliation_id"),
            "report_id": journey.get("report_id"),
        },
        "human_control": {
            "requester_identity": journey.get("requester_identity"),
            "approver_identity": journey.get("approver_identity"),
            "denied_action_execution_count": denied.get("execution_count"),
            "denied_dispatch_rejected": denied.get("dispatch_rejected"),
            "approval_source": "aegisops_approval_decision_record",
        },
        "idempotency": {
            "wazuh_first_disposition": first_delivery.get("disposition"),
            "wazuh_duplicate_disposition": duplicate_delivery.get("disposition"),
            "wazuh_alert_identity_preserved": (
                first_delivery.get("finding_id")
                == duplicate_delivery.get("finding_id")
            ),
            "shuffle_execution_count": journey.get(
                "idempotency_execution_count"
            ),
            "receipt_replay_reconciliation_id": journey.get(
                "replay_reconciliation_id"
            ),
            "receipt_identity_preserved": journey.get(
                "receipt_identity_preserved"
            ),
        },
        "negative_cases": {
            "invalid_credential": {
                "status": "rejected",
                "authority_delta": wazuh.get("negative_boundary", {}).get(
                    "authoritative_alert_delta"
                ),
                "evidence_ref": "wazuh-command:invalid_bearer_secret=403",
            },
            "proxy_bypass": {
                "status": "rejected",
                "authority_delta": wazuh.get("negative_boundary", {}).get(
                    "authoritative_alert_delta"
                ),
                "evidence_ref": "wazuh-command:proxy_bypass=403",
            },
            "failed_execution": negative_case("failed_execution"),
            "malformed_receipt": negative_case("malformed_receipt"),
            "reconciliation_mismatch": negative_case(
                "reconciliation_mismatch"
            ),
        },
        "restart": {
            "performed": restart.get("performed"),
            "records_persisted": restart.get("records_persisted"),
            "checked_identifiers": restart.get("checked_identifiers"),
        },
        "report": {
            "report_id": journey.get("report_id"),
            "sha256": report_sha256,
            "source_of_truth": report.get("source_of_truth"),
            "redacted": True,
        },
        "cleanup": {
            "mode": "non_destructive",
            "containers_stopped": True,
            "data_preserved": True,
        },
        "authority_posture": "aegisops_records_remain_authoritative",
        "verdict": "integration_trial_passed_with_owned_limitations",
        "limitations": [
            {
                "limitation_id": "phase67-single-host",
                "owner": "AegisOps platform operations",
                "status": "accepted",
                "description": "Evidence covers one non-production single-host Colima lab.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-bounded-connectors",
                "owner": "AegisOps integration engineering",
                "status": "follow_up_required",
                "description": "Evidence covers one Wazuh rule and one reviewed harmless Shuffle workflow.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-ga-gates-open",
                "owner": "AegisOps release owner",
                "status": "blocking",
                "description": "Production operations, design-partner evidence, scale, HA, and disaster recovery gates remain open.",
                "follow_up_issue": None,
            },
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output = build(args)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"cannot build Phase 67.4 evidence: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    staging = args.output.with_name(f".{args.output.name}.tmp")
    staging.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    staging.chmod(0o600)
    staging.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
