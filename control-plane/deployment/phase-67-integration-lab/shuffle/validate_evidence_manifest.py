from __future__ import annotations

import json
import pathlib
import re
import sys
from uuid import UUID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    require(len(sys.argv) == 2, "usage: validate_evidence_manifest.py <manifest>")
    path = pathlib.Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "manifest must be a JSON object")
    require(
        payload.get("schema_version") == "phase67.3-real-shuffle-trial-v1",
        "unexpected schema_version",
    )
    require(payload.get("source_mode") == "real_shuffle", "source_mode is not real")
    workflow_id = payload.get("workflow_api_id")
    require(isinstance(workflow_id, str), "workflow_api_id is missing")
    UUID(workflow_id)
    execution_id = payload.get("execution_id")
    receipt_id = payload.get("expected_execution_receipt_id")
    require(
        isinstance(execution_id, str)
        and execution_id
        and not execution_id.startswith("shuffle-run-"),
        "execution_id is synthetic or missing",
    )
    UUID(execution_id)
    require(
        isinstance(payload.get("idempotency_key"), str)
        and payload["idempotency_key"],
        "idempotency_key is missing",
    )
    idempotency_execution_count = payload.get("idempotency_execution_count")
    require(
        isinstance(idempotency_execution_count, int)
        and not isinstance(idempotency_execution_count, bool)
        and idempotency_execution_count == 1,
        "idempotency key did not resolve to integer one execution",
    )
    requested_scope = payload.get("requested_scope")
    require(
        isinstance(requested_scope, dict)
        and requested_scope.get("record_family") == "phase67_lab_trial"
        and requested_scope.get("recipient_identity") == "local-test-sink",
        "requested_scope is invalid",
    )
    require(
        isinstance(receipt_id, str)
        and receipt_id
        and not receipt_id.startswith("shuffle-receipt-"),
        "receipt id is synthetic or missing",
    )
    for digest_field in ("payload_hash", "normalized_receipt_sha256"):
        require(
            isinstance(payload.get(digest_field), str)
            and re.fullmatch(r"[0-9a-f]{64}", payload[digest_field]) is not None,
            f"{digest_field} is invalid",
        )
    require(
        payload.get("reconciliation_id")
        == payload.get("replay_reconciliation_id"),
        "receipt replay was not idempotent",
    )
    require(
        payload.get("execution_lifecycle_state") == "succeeded",
        "execution lifecycle is not succeeded",
    )
    require(
        payload.get("reconciliation_disposition") == "matched",
        "reconciliation disposition is not matched",
    )
    require(
        payload.get("authority_posture")
        == "aegisops_reconciliation_remains_authoritative",
        "Shuffle state was promoted beyond its authority boundary",
    )
    require(
        "isolated_non-production_lab" in payload.get("limitations", []),
        "non-production limitation is missing",
    )
    print("PASS: Phase 67.3 real Shuffle evidence is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
