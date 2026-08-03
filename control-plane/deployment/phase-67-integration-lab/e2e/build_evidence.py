#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
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
    ("snapshot", "artifact:workflow-snapshot.json"),
    ("artifact:initial-status.txt",),
    ("wazuh-manifest:native_wazuh_alert_id",),
    ("wazuh-manifest:aegisops_alert_id",),
    ("journey:case_id",),
    ("journey:action_request_id",),
    ("journey:denied_dispatch",),
    (
        "journey:approval_challenge_sha256",
        "artifact:workflow-pre-dispatch.json",
        "journey:execution_id",
    ),
    ("journey:expected_receipt_id",),
    ("journey:reconciliation_id",),
    ("report:sha256",),
    ("wazuh-manifest:duplicate_delivery", "journey:replay_reconciliation_id"),
    ("wazuh-command:negative-boundaries", "journey:measured_negative_probes"),
    ("restart:checked_identifiers", "artifact:restart-status.txt"),
    ("evaluation-record:sha256",),
)

LIMITATION_STATUSES = {
    "phase67-single-host": "accepted",
    "phase67-bounded-connectors": "follow_up_required",
    "phase67-ga-gates-open": "blocking",
}
LIMITATION_IDS = tuple(LIMITATION_STATUSES)
REPORT_RECORD_ID_FIELDS = {
    "alert": "alert_id",
    "case": "case_id",
    "action_request": "action_request_id",
    "approval_decision": "approval_decision_id",
    "action_execution": "action_execution_id",
    "reconciliation": "reconciliation_id",
}


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


def _canonical_json_sha256(path: Path) -> str:
    payload = _read_json(path)
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _status_value(path: Path, key: str) -> str:
    prefix = f"{key}="
    matches = [
        line[len(prefix) :].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(prefix)
    ]
    if len(matches) != 1 or matches[0] == "":
        raise ValueError(f"{path.name} must contain exactly one {key}")
    return matches[0]


def _required_text(value: object, path: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{path} must be a non-empty string")
    return value.strip()


def _validate_trial_report_scope(
    report: Mapping[str, object],
    journey: Mapping[str, object],
) -> None:
    records = _mapping(report.get("records"), "report.records")
    if set(records) != set(REPORT_RECORD_ID_FIELDS):
        raise ValueError("report record families do not match the Phase 67 trial scope")

    expected_ids = {
        "alert": {journey.get("alert_id")},
        "case": {journey.get("case_id")},
        "action_request": {
            journey.get("denied_action_request_id"),
            journey.get("action_request_id"),
        },
        "approval_decision": {
            journey.get("denied_approval_decision_id"),
            journey.get("approval_decision_id"),
        },
        "action_execution": {journey.get("action_execution_id")},
    }
    for family, family_expected_ids in expected_ids.items():
        if not all(
            isinstance(record_id, str) and record_id.strip()
            for record_id in family_expected_ids
        ):
            raise ValueError(f"journey lacks the {family} report scope")
        family_records = records[family]
        if not isinstance(family_records, list):
            raise ValueError(f"report.records.{family} must be an array")
        observed_ids = {
            _required_text(
                _mapping(item, f"report.records.{family}[{index}]").get(
                    REPORT_RECORD_ID_FIELDS[family]
                ),
                f"report.records.{family}[{index}].{REPORT_RECORD_ID_FIELDS[family]}",
            )
            for index, item in enumerate(family_records)
        }
        if observed_ids != family_expected_ids or len(family_records) != len(
            family_expected_ids
        ):
            raise ValueError(f"report.records.{family} is not scoped to this trial")

    reconciliation_records = records["reconciliation"]
    if not isinstance(reconciliation_records, list) or not reconciliation_records:
        raise ValueError("report must retain trial reconciliation records")
    reconciliation_ids: set[str] = set()
    wazuh_reconciliation_ids = journey.get("wazuh_reconciliation_ids")
    if (
        not isinstance(wazuh_reconciliation_ids, list)
        or not wazuh_reconciliation_ids
        or any(
            not isinstance(record_id, str) or not record_id.strip()
            for record_id in wazuh_reconciliation_ids
        )
        or len(set(wazuh_reconciliation_ids)) != len(wazuh_reconciliation_ids)
    ):
        raise ValueError("journey lacks unique Wazuh reconciliation IDs")
    for index, item in enumerate(reconciliation_records):
        record = _mapping(item, f"report.records.reconciliation[{index}]")
        reconciliation_ids.add(
            _required_text(
                record.get("reconciliation_id"),
                f"report.records.reconciliation[{index}].reconciliation_id",
            )
        )
        linked_execution_ids = record.get("linked_execution_run_ids")
        if not isinstance(linked_execution_ids, list):
            raise ValueError(
                f"report.records.reconciliation[{index}].linked_execution_run_ids "
                "must be an array"
            )
        if not (
            record.get("alert_id") == journey.get("alert_id")
            or record.get("finding_id") == journey.get("finding_id")
            or record.get("execution_run_id") == journey.get("execution_id")
            or journey.get("execution_id") in linked_execution_ids
        ):
            raise ValueError(
                "report.records.reconciliation contains a record outside this trial"
            )
    if len(reconciliation_ids) != len(reconciliation_records):
        raise ValueError("report.records.reconciliation contains duplicate IDs")
    expected_reconciliation_ids = {
        *wazuh_reconciliation_ids,
        _required_text(
            journey.get("reconciliation_id"),
            "journey.reconciliation_id",
        ),
    }
    if reconciliation_ids != expected_reconciliation_ids:
        raise ValueError(
            "report.records.reconciliation is not scoped to this trial"
        )


def _load_step_observations(path: Path) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    previous: datetime | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            item = _mapping(json.loads(line), f"observations line {line_number}")
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"observations line {line_number} is not valid JSON"
            ) from exc
        if set(item) != {"step", "name", "observed_at"}:
            raise ValueError(
                f"observations line {line_number} fields do not match the contract"
            )
        expected_step = len(observations) + 1
        if item.get("step") != expected_step:
            raise ValueError("step observations must be ordered 1 through 15")
        expected_name = STEP_NAMES[expected_step - 1]
        if item.get("name") != expected_name:
            raise ValueError(
                f"step observation {expected_step} is not {expected_name!r}"
            )
        observed_at = _required_text(
            item.get("observed_at"),
            f"observations[{expected_step - 1}].observed_at",
        )
        normalized = observed_at[:-1] + "+00:00" if observed_at.endswith("Z") else observed_at
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(
                f"step observation {expected_step} is not RFC3339"
            ) from exc
        if parsed.tzinfo is None:
            raise ValueError(f"step observation {expected_step} lacks a timezone")
        parsed = parsed.astimezone(timezone.utc)
        if previous is not None and parsed <= previous:
            raise ValueError("step observations must be strictly chronological")
        previous = parsed
        observations.append(
            {
                "step": expected_step,
                "name": expected_name,
                "observed_at": observed_at,
            }
        )
    if len(observations) != len(STEP_NAMES):
        raise ValueError("step observations must contain exactly 15 entries")
    return observations


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--wazuh", type=Path, required=True)
    parser.add_argument("--wazuh-output", type=Path, required=True)
    parser.add_argument("--journey", type=Path, required=True)
    parser.add_argument("--restart", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--evaluation-record", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--startup-status", type=Path, required=True)
    parser.add_argument("--initial-status", type=Path, required=True)
    parser.add_argument("--restart-status", type=Path, required=True)
    parser.add_argument("--workflow-snapshot", type=Path, required=True)
    parser.add_argument("--workflow-pre-dispatch", type=Path, required=True)
    parser.add_argument("--reviewed-workflow", type=Path, required=True)
    parser.add_argument("--artifacts-directory-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def build(args: argparse.Namespace) -> dict[str, object]:
    snapshot = _mapping(_read_json(args.snapshot), "snapshot")
    preparation = _mapping(_read_json(args.preparation), "preparation")
    wazuh = _mapping(_read_json(args.wazuh), "wazuh")
    combined_journey = _mapping(_read_json(args.journey), "journey output")
    journey = _mapping(combined_journey.get("journey"), "journey output.journey")
    restart = _mapping(_read_json(args.restart), "restart")
    report = _mapping(_read_json(args.report), "report")
    evaluation_record = _mapping(
        _read_json(args.evaluation_record),
        "evaluation record",
    )
    observations = _load_step_observations(args.observations)
    wazuh_output = args.wazuh_output.read_text(encoding="utf-8")
    evaluation = args.evaluation.read_text(encoding="utf-8")
    if _sha256(args.reviewed_workflow) != snapshot.get(
        "shuffle_reviewed_workflow_sha256"
    ):
        raise ValueError("snapshot reviewed Shuffle workflow digest does not match")
    for workflow_path in (
        args.workflow_snapshot,
        args.workflow_pre_dispatch,
    ):
        workflow = _mapping(_read_json(workflow_path), workflow_path.name)
        if workflow.get("id") != snapshot.get("shuffle_api_workflow_id"):
            raise ValueError(f"{workflow_path.name} uses a different workflow ID")
        if _canonical_json_sha256(workflow_path) != snapshot.get(
            "shuffle_live_workflow_sha256"
        ):
            raise ValueError(
                f"{workflow_path.name} does not match the snapshotted workflow"
            )
    for status_path in (
        args.startup_status,
        args.initial_status,
        args.restart_status,
    ):
        if _status_value(status_path, "repository_commit") != snapshot.get(
            "repository_revision"
        ):
            raise ValueError(f"{status_path.name} uses a different revision")
        if _status_value(status_path, "repository_runtime_state") != "clean":
            raise ValueError(f"{status_path.name} was captured from a dirty runtime")
        if _status_value(
            status_path,
            "repository_runtime_artifact_sha256",
        ) != snapshot.get("runtime_artifact_sha256"):
            raise ValueError(f"{status_path.name} uses different runtime artifacts")
        control_plane_image_id = _status_value(
            status_path,
            "control_plane_container_image_id",
        )
        if re.fullmatch(r"sha256:[0-9a-f]{64}", control_plane_image_id) is None:
            raise ValueError(
                f"{status_path.name} lacks the control-plane image identity"
            )
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
    expected_evaluation = {
        "schema_version": "phase67.4-prerequisite-evaluation-v1",
        "trial_run_id": snapshot.get("trial_run_id"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "repository_revision": snapshot.get("repository_revision"),
        "verdict": "integration_trial_passed_with_owned_limitations",
        "ga_accepted": False,
        "limitation_ids": list(LIMITATION_IDS),
    }
    if set(evaluation_record) != set(expected_evaluation) | {"evaluated_at"}:
        raise ValueError("evaluation record fields do not match the reviewed contract")
    for key, expected in expected_evaluation.items():
        if evaluation_record.get(key) != expected:
            raise ValueError(f"evaluation record {key} does not match this trial")
    _required_text(evaluation_record.get("evaluated_at"), "evaluation.evaluated_at")
    if _sha256(args.schema) != snapshot.get("evidence_schema_sha256"):
        raise ValueError("snapshot evidence schema digest does not match")
    if report.get("export_id") != journey.get("report_id"):
        raise ValueError("report export ID does not match the journey")
    report_sha256 = _sha256(args.report)
    if report_sha256 != journey.get("report_sha256"):
        raise ValueError("report digest does not match the journey")
    if report.get("source_of_truth") != "aegisops_authoritative_records":
        raise ValueError("report is not derived from AegisOps source records")
    _validate_trial_report_scope(report, journey)
    if wazuh.get("aegisops_alert_id") != journey.get("alert_id"):
        raise ValueError("Wazuh admission and case journey use different alerts")
    if wazuh.get("first_delivery", {}).get("finding_id") != journey.get("finding_id"):
        raise ValueError("Wazuh admission and action journey use different findings")
    for key in ("trial_run_id", "action_request_id", "payload_hash"):
        if preparation.get(key) != journey.get(key):
            raise ValueError(f"preparation {key} does not match the journey")
    if preparation.get("requester_identity") != journey.get("requester_identity"):
        raise ValueError("preparation requester does not match the journey")
    if preparation.get("approval_challenge_sha256") != journey.get(
        "approval_challenge_sha256"
    ):
        raise ValueError("interactive approval challenge is not bound to the journey")
    if restart.get("shuffle_execution_count") != journey.get(
        "idempotency_execution_count"
    ):
        raise ValueError("restart changed the Shuffle execution count")
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = _required_text(snapshot.get("snapshot_id"), "snapshot.snapshot_id")
    steps = [
        {
            "step": observation["step"],
            "name": observation["name"],
            "status": "passed",
            "snapshot_id": snapshot_id,
            "observed_at": observation["observed_at"],
            "evidence_refs": list(
                STEP_EVIDENCE_REFS[int(observation["step"]) - 1]
            ),
        }
        for observation in observations
    ]
    first_delivery = _mapping(wazuh.get("first_delivery"), "wazuh.first_delivery")
    duplicate_delivery = _mapping(
        wazuh.get("duplicate_delivery"),
        "wazuh.duplicate_delivery",
    )
    denied = _mapping(journey.get("denied_dispatch"), "journey.denied_dispatch")
    probes = _mapping(journey.get("negative_probes"), "journey.negative_probes")
    negative_boundary = _mapping(
        wazuh.get("negative_boundary"),
        "wazuh.negative_boundary",
    )

    def negative_case(name: str) -> dict[str, object]:
        probe = _mapping(probes.get(name), f"journey.negative_probes.{name}")
        return {
            "status": probe.get("status"),
            "authority_before": probe.get("authority_before"),
            "authority_after": probe.get("authority_after"),
            "authority_delta": probe.get("authority_delta"),
            "measurement_source": probe.get("measurement_source"),
            "evidence_ref": f"journey:negative_probes.{name}:{probe.get('category')}",
        }

    def ingress_negative_case(name: str) -> dict[str, object]:
        return {
            "status": "rejected",
            "authority_before": negative_boundary.get("baseline_alert_count"),
            "authority_after": negative_boundary.get("after_alert_count"),
            "authority_delta": negative_boundary.get(
                "authoritative_alert_delta"
            ),
            "measurement_source": "aegisops_authoritative_alert_count",
            "evidence_ref": f"wazuh-command:{name}=403",
        }

    artifact_paths = {
        "preparation.json": args.preparation,
        "wazuh-manifest.json": args.wazuh,
        "wazuh-output.txt": args.wazuh_output,
        "journey.json": args.journey,
        "restart.json": args.restart,
        "snapshot.json": args.snapshot,
        "images.json": args.images,
        "evaluation-record.json": args.evaluation_record,
        "step-observations.jsonl": args.observations,
        "startup-status.txt": args.startup_status,
        "initial-status.txt": args.initial_status,
        "restart-status.txt": args.restart_status,
        "workflow-snapshot.json": args.workflow_snapshot,
        "workflow-pre-dispatch.json": args.workflow_pre_dispatch,
    }

    return {
        "schema_version": "phase67.4-real-service-e2e-evidence-v2",
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
            "authenticated_approver_identity": journey.get(
                "authenticated_approver_identity"
            ),
            "denied_action_execution_count": denied.get("execution_count"),
            "denied_dispatch_rejected": denied.get("dispatch_rejected"),
            "approval_source": journey.get("approval_source"),
            "approval_method": journey.get("approval_method"),
            "approval_challenge_sha256": journey.get(
                "approval_challenge_sha256"
            ),
            "approval_confirmed_at": journey.get("approval_confirmed_at"),
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
                **ingress_negative_case("invalid_bearer_secret"),
            },
            "proxy_bypass": {
                **ingress_negative_case("proxy_bypass"),
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
        "evaluation": {
            "trial_run_id": evaluation_record.get("trial_run_id"),
            "snapshot_id": evaluation_record.get("snapshot_id"),
            "repository_revision": evaluation_record.get(
                "repository_revision"
            ),
            "evaluated_at": evaluation_record.get("evaluated_at"),
            "verdict": evaluation_record.get("verdict"),
            "ga_accepted": evaluation_record.get("ga_accepted"),
            "sha256": _sha256(args.evaluation_record),
        },
        "artifacts": {
            "retention": "local_mode_0600",
            "directory_name": args.artifacts_directory_name,
            "files": [
                {"name": name, "sha256": _sha256(path)}
                for name, path in artifact_paths.items()
            ],
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
                "status": LIMITATION_STATUSES["phase67-single-host"],
                "description": "Evidence covers one non-production single-host Colima lab.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-bounded-connectors",
                "owner": "AegisOps integration engineering",
                "status": LIMITATION_STATUSES["phase67-bounded-connectors"],
                "description": "Evidence covers one Wazuh rule and one reviewed harmless Shuffle workflow.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-ga-gates-open",
                "owner": "AegisOps release owner",
                "status": LIMITATION_STATUSES["phase67-ga-gates-open"],
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
