from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib import error


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.adapters.shuffle_real import (
    RealShuffleActionAdapter,
    ShuffleReceiptPollingClient,
    ShuffleTransportFailure,
    UrllibShuffleJsonTransport,
)
from aegisops.control_plane.config import RuntimeConfig


API_WORKFLOW_ID = "67f30000-0000-4000-8000-000000000001"
REAL_EXECUTION_ID = "67f30000-0000-4000-8000-000000000002"
SECOND_REAL_EXECUTION_ID = "67f30000-0000-4000-8000-000000000003"
EVIDENCE_VALIDATOR = (
    CONTROL_PLANE_ROOT
    / "deployment"
    / "phase-67-integration-lab"
    / "shuffle"
    / "validate_evidence_manifest.py"
)


class _QueueTransport:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request_json(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _binding() -> dict[str, object]:
    return {
        "workflow_id": "notify_identity_owner",
        "workflow_version_id": "notify_identity_owner-v1-reviewed-2026-05-03",
        "correlation_id": "phase67-correlation-001",
        "expected_execution_receipt_id": "phase67-receipt-001",
        "requested_scope": {
            "recipient_identity": "local-test-sink",
        },
    }


def _payload() -> dict[str, object]:
    return {
        "action_type": "notify_identity_owner",
        "recipient_identity": "local-test-sink",
        "message_intent": "Write one harmless local lab notification.",
        "escalation_reason": "Phase 67.3 real transport proof.",
        "shuffle_delegation_binding": _binding(),
    }


def _adapter(transport: _QueueTransport) -> RealShuffleActionAdapter:
    return RealShuffleActionAdapter(
        base_url="https://proxy:8443/shuffle-api",
        api_key="fixture-api-key",
        api_workflow_id=API_WORKFLOW_ID,
        transport=transport,
        timeout_seconds=2,
        max_attempts=2,
    )


def _dispatch(adapter: RealShuffleActionAdapter):
    return adapter.dispatch_approved_action(
        delegation_id="delegation-001",
        action_request_id="action-request-001",
        approval_decision_id="approval-001",
        payload_hash="payload-hash-001",
        idempotency_key="idempotency-001",
        approved_payload=_payload(),
        delegated_at=datetime(2026, 7, 29, tzinfo=timezone.utc),
    )


class RealShuffleTransportTests(unittest.TestCase):
    def test_adapter_representations_redact_credentials_and_require_ca(self) -> None:
        adapter = _adapter(_QueueTransport())
        polling_client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="polling-secret",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(),
        )

        self.assertNotIn("fixture-api-key", repr(adapter))
        self.assertNotIn("polling-secret", repr(polling_client))
        with self.assertRaisesRegex(ValueError, "requires an explicit CA file"):
            UrllibShuffleJsonTransport(ca_file="")
        self.assertEqual(
            UrllibShuffleJsonTransport(ca_file=" /fixture/ca.pem ").ca_file,
            "/fixture/ca.pem",
        )

    def test_bounded_retry_returns_one_real_execution_identity(self) -> None:
        transport = _QueueTransport(
            ShuffleTransportFailure("connection_failure", retryable=True),
            {"success": True, "execution_id": REAL_EXECUTION_ID},
        )

        receipt = _dispatch(_adapter(transport))

        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(receipt.execution_run_id, REAL_EXECUTION_ID)
        self.assertEqual(receipt.external_receipt_id, "phase67-receipt-001")
        self.assertEqual(receipt.adapter, "shuffle_real_http")
        first_payload = transport.calls[0]["payload"]
        second_payload = transport.calls[1]["payload"]
        self.assertEqual(first_payload, second_payload)
        self.assertNotIn("fixture-api-key", repr(first_payload))

    def test_timeout_fails_closed_without_ambiguous_post_retry(self) -> None:
        transport = _QueueTransport(ShuffleTransportFailure("timeout"))

        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "Shuffle transport failed: timeout",
        ):
            _dispatch(_adapter(transport))

        self.assertEqual(len(transport.calls), 1)

    def test_authentication_failure_is_not_retried(self) -> None:
        transport = _QueueTransport(
            ShuffleTransportFailure("authentication_rejected")
        )

        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "authentication_rejected",
        ):
            _dispatch(_adapter(transport))

        self.assertEqual(len(transport.calls), 1)

    def test_real_adapter_rejects_synthetic_expected_receipt(self) -> None:
        payload = _payload()
        payload["shuffle_delegation_binding"] = {
            **_binding(),
            "expected_execution_receipt_id": "shuffle-receipt-fixture",
        }
        transport = _QueueTransport(
            {"success": True, "execution_id": REAL_EXECUTION_ID}
        )

        with self.assertRaisesRegex(ValueError, "must be a real identifier"):
            _adapter(transport).dispatch_approved_action(
                delegation_id="delegation-001",
                action_request_id="action-request-001",
                approval_decision_id="approval-001",
                payload_hash="payload-hash-001",
                idempotency_key="idempotency-001",
                approved_payload=payload,
                delegated_at=datetime(2026, 7, 29, tzinfo=timezone.utc),
            )

        self.assertEqual(transport.calls, [])

    def test_real_adapter_requires_tls_and_canonical_workflow_uuid(self) -> None:
        transport = _QueueTransport()
        with self.assertRaisesRegex(ValueError, "requires an HTTPS base URL"):
            RealShuffleActionAdapter(
                base_url="http://shuffle-backend:5001",
                api_key="fixture-api-key",
                api_workflow_id=API_WORKFLOW_ID,
                transport=transport,
            )
        with self.assertRaisesRegex(ValueError, "must be a UUID"):
            RealShuffleActionAdapter(
                base_url="https://proxy:8443/shuffle-api",
                api_key="fixture-api-key",
                api_workflow_id="notify_identity_owner",
                transport=transport,
            )
        with self.assertRaisesRegex(ValueError, "must not contain userinfo"):
            RealShuffleActionAdapter(
                base_url="https://user:password@proxy:8443/shuffle-api",
                api_key="fixture-api-key",
                api_workflow_id=API_WORKFLOW_ID,
                transport=transport,
            )
        with self.assertRaisesRegex(ValueError, "execution id must be a UUID"):
            _dispatch(
                _adapter(
                    _QueueTransport(
                        {"success": True, "execution_id": "real-but-not-a-uuid"}
                    )
                )
            )

    def test_http_transport_only_retries_proven_preconnect_failure(self) -> None:
        transport = UrllibShuffleJsonTransport(ca_file="/fixture/ca.pem")
        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.urlopen",
                side_effect=error.URLError(ConnectionRefusedError()),
            ),
        ):
            with self.assertRaises(ShuffleTransportFailure) as raised:
                transport.request_json(
                    method="POST",
                    url="https://proxy:8443/shuffle-api/api/v1/workflows/id/execute",
                    api_key="fixture-api-key",
                    payload={"fixture": True},
                    timeout_seconds=2,
                )
        self.assertEqual(raised.exception.category, "connection_not_established")
        self.assertTrue(raised.exception.retryable)

        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.urlopen",
                side_effect=error.HTTPError(
                    "https://proxy:8443/shuffle-api/api/v1/workflows/id/execute",
                    503,
                    "unavailable",
                    {},
                    None,
                ),
            ),
        ):
            with self.assertRaises(ShuffleTransportFailure) as raised:
                transport.request_json(
                    method="POST",
                    url="https://proxy:8443/shuffle-api/api/v1/workflows/id/execute",
                    api_key="fixture-api-key",
                    payload={"fixture": True},
                    timeout_seconds=2,
                )
        self.assertEqual(raised.exception.category, "http_503")
        self.assertFalse(raised.exception.retryable)

    def test_authenticated_poll_normalizes_bound_receipt(self) -> None:
        argument = {
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "delegation_id": "delegation-001",
            "payload_hash": "payload-hash-001",
            "idempotency_key": "idempotency-001",
            **_binding(),
        }
        transport = _QueueTransport(
            {
                "executions": [
                    {
                        "execution_id": REAL_EXECUTION_ID,
                        "execution_argument": argument,
                        "status": "FINISHED",
                        "authorization": "must-not-be-persisted",
                    }
                ]
            }
        )
        client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=transport,
        )

        receipt = client.poll_normalized_receipt(
            execution_id=REAL_EXECUTION_ID,
            idempotency_key="idempotency-001",
            expected_binding=argument,
            observed_at=datetime(2026, 7, 29, tzinfo=timezone.utc),
        )

        self.assertEqual(receipt["status"], "success")
        self.assertEqual(receipt["execution_run_id"], REAL_EXECUTION_ID)
        self.assertEqual(
            receipt["expected_execution_receipt_id"],
            "phase67-receipt-001",
        )
        self.assertNotIn("authorization", receipt)
        self.assertEqual(
            receipt["requested_scope"],
            {"recipient_identity": "local-test-sink"},
        )
        self.assertEqual(receipt["idempotency_execution_count"], 1)
        self.assertEqual(
            transport.calls[0]["api_key"],
            "fixture-api-key",
        )

    def test_poll_rejects_correlation_mismatch_and_duplicate_receipt(self) -> None:
        expected = {
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "delegation_id": "delegation-001",
            "payload_hash": "payload-hash-001",
            "idempotency_key": "idempotency-001",
            **_binding(),
        }
        mismatched = {**expected, "payload_hash": "different"}
        client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": mismatched,
                            "status": "FINISHED",
                        }
                    ]
                }
            ),
        )
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "payload_hash_mismatch",
        ):
            client.poll_normalized_receipt(
                execution_id=REAL_EXECUTION_ID,
                idempotency_key="idempotency-001",
                expected_binding=expected,
                observed_at=datetime.now(timezone.utc),
            )

        duplicate_client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(
                [
                    {"execution_id": REAL_EXECUTION_ID},
                    {"execution_id": REAL_EXECUTION_ID},
                ]
            ),
        )
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "duplicate_receipt",
        ):
            duplicate_client.poll_normalized_receipt(
                execution_id=REAL_EXECUTION_ID,
                idempotency_key="idempotency-001",
                expected_binding=expected,
                observed_at=datetime.now(timezone.utc),
            )

        duplicate_idempotency_client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": expected,
                            "status": "FINISHED",
                        },
                        {
                            "execution_id": SECOND_REAL_EXECUTION_ID,
                            "execution_argument": expected,
                            "status": "FINISHED",
                        },
                    ]
                }
            ),
        )
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "duplicate_idempotency_execution",
        ):
            duplicate_idempotency_client.poll_normalized_receipt(
                execution_id=REAL_EXECUTION_ID,
                idempotency_key="idempotency-001",
                expected_binding=expected,
                observed_at=datetime.now(timezone.utc),
            )

    def test_poll_fails_closed_for_missing_malformed_and_failed_receipts(self) -> None:
        expected = {
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "delegation_id": "delegation-001",
            "payload_hash": "payload-hash-001",
            "idempotency_key": "idempotency-001",
            **_binding(),
        }
        for response, category in (
            ({"executions": []}, "missing_receipt"),
            (
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": "{not-json",
                            "status": "FINISHED",
                        }
                    ]
                },
                "malformed_receipt",
            ),
        ):
            with self.subTest(category=category):
                client = ShuffleReceiptPollingClient(
                    base_url="https://proxy:8443/shuffle-api",
                    api_key="fixture-api-key",
                    api_workflow_id=API_WORKFLOW_ID,
                    transport=_QueueTransport(response),
                )
                with self.assertRaisesRegex(ShuffleTransportFailure, category):
                    client.poll_normalized_receipt(
                        execution_id=REAL_EXECUTION_ID,
                        idempotency_key="idempotency-001",
                        expected_binding=expected,
                        observed_at=datetime.now(timezone.utc),
                    )

        failed_client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": expected,
                            "status": "FAILED",
                        }
                    ]
                }
            ),
        )
        receipt = failed_client.poll_normalized_receipt(
            execution_id=REAL_EXECUTION_ID,
            idempotency_key="idempotency-001",
            expected_binding=expected,
            observed_at=datetime.now(timezone.utc),
        )
        self.assertEqual(receipt["status"], "failed")

    def test_runtime_config_loads_file_backed_real_transport_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api_key_file = pathlib.Path(temp_dir) / "shuffle-api-key"
            api_key_file.write_text("real-file-backed-key\n", encoding="utf-8")

            config = RuntimeConfig.from_env(
                {
                    "AEGISOPS_CONTROL_PLANE_SHUFFLE_TRANSPORT_MODE": "real_http",
                    "AEGISOPS_CONTROL_PLANE_SHUFFLE_API_KEY_FILE": str(
                        api_key_file
                    ),
                    "AEGISOPS_CONTROL_PLANE_SHUFFLE_API_WORKFLOW_ID": (
                        API_WORKFLOW_ID
                    ),
                    "AEGISOPS_CONTROL_PLANE_SHUFFLE_CA_FILE": (
                        "/run/secrets/phase67-proxy-ca"
                    ),
                }
            )

        self.assertEqual(config.shuffle_transport_mode, "real_http")
        self.assertEqual(config.shuffle_api_key, "real-file-backed-key")
        self.assertNotIn("real-file-backed-key", repr(config))

    def test_evidence_validator_rejects_nonterminal_and_noninteger_proof(
        self,
    ) -> None:
        manifest = {
            "schema_version": "phase67.3-real-shuffle-trial-v1",
            "source_mode": "real_shuffle",
            "workflow_api_id": API_WORKFLOW_ID,
            "execution_id": REAL_EXECUTION_ID,
            "idempotency_key": "idempotency-001",
            "idempotency_execution_count": 1,
            "requested_scope": {
                "record_family": "phase67_lab_trial",
                "recipient_identity": "local-test-sink",
            },
            "payload_hash": "a" * 64,
            "expected_execution_receipt_id": "phase67-receipt-001",
            "normalized_receipt_sha256": "b" * 64,
            "reconciliation_id": "reconciliation-001",
            "replay_reconciliation_id": "reconciliation-001",
            "execution_lifecycle_state": "succeeded",
            "reconciliation_disposition": "matched",
            "authority_posture": "aegisops_reconciliation_remains_authoritative",
            "limitations": ("isolated_non-production_lab",),
        }

        def validate(candidate: dict[str, object]) -> subprocess.CompletedProcess[str]:
            with tempfile.TemporaryDirectory() as temp_dir:
                manifest_path = pathlib.Path(temp_dir) / "manifest.json"
                manifest_path.write_text(
                    json.dumps(candidate),
                    encoding="utf-8",
                )
                return subprocess.run(
                    [sys.executable, str(EVIDENCE_VALIDATOR), str(manifest_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )

        self.assertEqual(validate(manifest).returncode, 0)
        for field_name, invalid_value, expected_error in (
            (
                "execution_lifecycle_state",
                "failed",
                "execution lifecycle is not succeeded",
            ),
            (
                "reconciliation_disposition",
                "mismatch",
                "reconciliation disposition is not matched",
            ),
            (
                "idempotency_execution_count",
                True,
                "did not resolve to integer one execution",
            ),
            (
                "idempotency_execution_count",
                1.0,
                "did not resolve to integer one execution",
            ),
        ):
            with self.subTest(field_name=field_name, invalid_value=invalid_value):
                result = validate({**manifest, field_name: invalid_value})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)


if __name__ == "__main__":
    unittest.main()
