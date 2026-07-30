from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import client as http_client
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

from aegisops.control_plane.adapters.executor import IsolatedExecutorAdapter
from aegisops.control_plane.adapters.shuffle import ShuffleActionAdapter
from aegisops.control_plane.adapters.shuffle_real import (
    RealShuffleActionAdapter,
    ShuffleReceiptPollingClient,
    ShuffleTransportFailure,
    UrllibShuffleJsonTransport,
    _RejectRedirectHandler,
)
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.service_composition import (
    build_control_plane_service_composition,
)


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
WORKFLOW_TEMPLATE = (
    CONTROL_PLANE_ROOT
    / "deployment"
    / "phase-67-integration-lab"
    / "shuffle"
    / "harmless-local-log-workflow.json"
)
WORKFLOW_VALIDATOR = WORKFLOW_TEMPLATE.with_name(
    "validate_preserved_workflow.py"
)
LAB_ROOT = WORKFLOW_TEMPLATE.parents[1]
BOOTSTRAP_SHUFFLE = LAB_ROOT / "bootstrap-shuffle.sh"
RUN_REAL_TRIAL = WORKFLOW_TEMPLATE.with_name("run_real_trial.py")


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


def _execution_argument(
    *,
    requested_scope: dict[str, object] | None = None,
) -> dict[str, object]:
    binding = _binding()
    if requested_scope is not None:
        binding["requested_scope"] = requested_scope
    return {
        "action_request_id": "action-request-001",
        "approval_decision_id": "approval-001",
        "delegation_id": "delegation-001",
        "payload_hash": "payload-hash-001",
        "idempotency_key": "idempotency-001",
        **binding,
        "delegated_at": "2026-07-29T00:00:00Z",
        "action": {
            "action_type": "notify_identity_owner",
            "recipient_identity": "local-test-sink",
            "message_intent": "Write one harmless local lab notification.",
            "escalation_reason": "Phase 67.3 real transport proof.",
        },
    }


def _reviewed_action_result(status: str = "SUCCESS") -> dict[str, object]:
    return {
        "action": {
            "id": "67f30000-0000-4000-8000-000000000011",
            "name": "repeat_back_to_me",
        },
        "status": status,
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

    def test_deterministic_adapters_recover_the_claimed_execution_identity(
        self,
    ) -> None:
        delegation = {
            "delegation_id": "delegation-001",
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "payload_hash": "payload-hash-001",
            "idempotency_key": "idempotency-001",
            "approved_payload": _payload(),
            "delegated_at": datetime(2026, 7, 29, tzinfo=timezone.utc),
        }
        shuffle = ShuffleActionAdapter(
            base_url="https://shuffle.example.test"
        )
        isolated_executor = IsolatedExecutorAdapter(
            base_url="https://executor.example.test"
        )

        self.assertEqual(
            shuffle.recover_interrupted_dispatch(**delegation),
            shuffle.dispatch_approved_action(**delegation),
        )
        self.assertEqual(
            isolated_executor.recover_interrupted_dispatch(**delegation),
            isolated_executor.dispatch_approved_action(**delegation),
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

    def test_interrupted_dispatch_recovers_exact_existing_execution_without_post(
        self,
    ) -> None:
        delegated_at = datetime(2026, 7, 29, tzinfo=timezone.utc)
        execution_argument = {
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "delegation_id": "delegation-001",
            "payload_hash": "payload-hash-001",
            "idempotency_key": "idempotency-001",
            **_binding(),
            "delegated_at": "2026-07-29T00:00:00Z",
            "action": {
                "action_type": "notify_identity_owner",
                "recipient_identity": "local-test-sink",
                "message_intent": "Write one harmless local lab notification.",
                "escalation_reason": "Phase 67.3 real transport proof.",
            },
        }
        transport = _QueueTransport(
            {
                "executions": [
                    {
                        "execution_id": REAL_EXECUTION_ID,
                        "execution_argument": json.dumps(execution_argument),
                        "status": "EXECUTING",
                    }
                ]
            }
        )

        receipt = _adapter(transport).recover_interrupted_dispatch(
            delegation_id="delegation-001",
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            payload_hash="payload-hash-001",
            idempotency_key="idempotency-001",
            approved_payload=_payload(),
            delegated_at=delegated_at.astimezone(timezone(timedelta(hours=9))),
        )

        self.assertEqual(receipt.execution_run_id, REAL_EXECUTION_ID)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0]["method"], "GET")
        self.assertIsNone(transport.calls[0]["payload"])

    def test_dispatch_canonicalizes_delegated_timestamp_to_utc(self) -> None:
        transport = _QueueTransport(
            {"success": True, "execution_id": REAL_EXECUTION_ID}
        )
        delegated_at = datetime(
            2026,
            7,
            30,
            6,
            15,
            tzinfo=timezone(timedelta(hours=9)),
        )

        _adapter(transport).dispatch_approved_action(
            delegation_id="delegation-001",
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            payload_hash="payload-hash-001",
            idempotency_key="idempotency-001",
            approved_payload=_payload(),
            delegated_at=delegated_at,
        )

        payload = transport.calls[0]["payload"]
        self.assertIsInstance(payload, dict)
        execution_argument = json.loads(payload["execution_argument"])
        self.assertEqual(
            execution_argument["delegated_at"],
            "2026-07-29T21:15:00Z",
        )

    def test_interrupted_dispatch_recovery_fails_closed_on_missing_or_drift(
        self,
    ) -> None:
        delegated_at = datetime(2026, 7, 29, tzinfo=timezone.utc)
        for response, category in (
            ({"executions": []}, "interrupted_dispatch_not_observed"),
            (
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": json.dumps(
                                {
                                    "idempotency_key": "idempotency-001",
                                    "delegation_id": "different",
                                }
                            ),
                        }
                    ]
                },
                "interrupted_dispatch_binding_mismatch",
            ),
        ):
            with self.subTest(category=category):
                adapter = _adapter(_QueueTransport(response))
                with self.assertRaisesRegex(ShuffleTransportFailure, category):
                    adapter.recover_interrupted_dispatch(
                        delegation_id="delegation-001",
                        action_request_id="action-request-001",
                        approval_decision_id="approval-001",
                        payload_hash="payload-hash-001",
                        idempotency_key="idempotency-001",
                        approved_payload=_payload(),
                        delegated_at=delegated_at,
                    )

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
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "malformed_dispatch_response",
        ):
            _dispatch(
                _adapter(
                    _QueueTransport(
                        {"success": True, "execution_id": "real-but-not-a-uuid"}
                    )
                )
            )

    def test_http_transport_only_retries_proven_preconnect_failure(self) -> None:
        transport = UrllibShuffleJsonTransport(ca_file="/fixture/ca.pem")
        preconnect_opener = mock.Mock()
        preconnect_opener.open.side_effect = error.URLError(
            ConnectionRefusedError()
        )
        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.build_opener",
                return_value=preconnect_opener,
            ) as build_preconnect_opener,
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
        self.assertTrue(raised.exception.transient)
        self.assertFalse(raised.exception.outcome_unknown)
        self.assertTrue(
            any(
                isinstance(handler, _RejectRedirectHandler)
                for handler in build_preconnect_opener.call_args.args
            )
        )

        gateway_opener = mock.Mock()
        gateway_opener.open.side_effect = error.HTTPError(
            "https://proxy:8443/shuffle-api/api/v1/workflows/id/execute",
            503,
            "unavailable",
            {},
            None,
        )
        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.build_opener",
                return_value=gateway_opener,
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
        self.assertTrue(raised.exception.transient)
        self.assertTrue(raised.exception.outcome_unknown)

        redirect_opener = mock.Mock()
        redirect_opener.open.side_effect = error.HTTPError(
            "https://proxy:8443/shuffle-api/api/v1/workflows/id/execute",
            302,
            "found",
            {"Location": "https://other.example.test/execution"},
            None,
        )
        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.build_opener",
                return_value=redirect_opener,
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
        self.assertEqual(raised.exception.category, "redirect_rejected")
        self.assertFalse(raised.exception.retryable)
        self.assertFalse(raised.exception.transient)
        self.assertTrue(raised.exception.outcome_unknown)

        framing_response = mock.MagicMock()
        opened_response = framing_response.__enter__.return_value
        opened_response.headers.get_content_type.return_value = "application/json"
        opened_response.read.side_effect = http_client.IncompleteRead(b"{", 1)
        framing_opener = mock.Mock()
        framing_opener.open.return_value = framing_response
        with (
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.ssl.create_default_context",
                return_value=object(),
            ),
            mock.patch(
                "aegisops.control_plane.adapters.shuffle_real.request.build_opener",
                return_value=framing_opener,
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
        self.assertEqual(raised.exception.category, "invalid_http_response")
        self.assertFalse(raised.exception.retryable)
        self.assertTrue(raised.exception.transient)
        self.assertTrue(raised.exception.outcome_unknown)

    def test_authenticated_poll_normalizes_bound_receipt(self) -> None:
        argument = _execution_argument()
        transport = _QueueTransport(
            {
                "executions": [
                    {
                        "execution_id": REAL_EXECUTION_ID.upper(),
                        "execution_argument": argument,
                        "status": "FINISHED",
                        "results": [_reviewed_action_result()],
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
        expected = _execution_argument()
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

        typed_expected = {
            **expected,
            "requested_scope": {"recipient_identity": "local-test-sink", "risk": 1},
        }
        typed_observed = {
            **typed_expected,
            "requested_scope": {
                "recipient_identity": "local-test-sink",
                "risk": True,
            },
        }
        type_drift_client = ShuffleReceiptPollingClient(
            base_url="https://proxy:8443/shuffle-api",
            api_key="fixture-api-key",
            api_workflow_id=API_WORKFLOW_ID,
            transport=_QueueTransport(
                {
                    "executions": [
                        {
                            "execution_id": REAL_EXECUTION_ID,
                            "execution_argument": typed_observed,
                            "status": "FINISHED",
                        }
                    ]
                }
            ),
        )
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "requested_scope_mismatch",
        ):
            type_drift_client.poll_normalized_receipt(
                execution_id=REAL_EXECUTION_ID,
                idempotency_key="idempotency-001",
                expected_binding=typed_expected,
                observed_at=datetime.now(timezone.utc),
            )

        for field_name, drifted_value in (
            (
                "action",
                {
                    **expected["action"],
                    "recipient_identity": "different-recipient",
                },
            ),
            ("delegated_at", "2026-07-29T00:00:01Z"),
        ):
            with self.subTest(field_name=field_name):
                drifted_argument = {**expected, field_name: drifted_value}
                drift_client = ShuffleReceiptPollingClient(
                    base_url="https://proxy:8443/shuffle-api",
                    api_key="fixture-api-key",
                    api_workflow_id=API_WORKFLOW_ID,
                    transport=_QueueTransport(
                        {
                            "executions": [
                                {
                                    "execution_id": REAL_EXECUTION_ID,
                                    "execution_argument": drifted_argument,
                                    "status": "FINISHED",
                                }
                            ]
                        }
                    ),
                )
                with self.assertRaisesRegex(
                    ShuffleTransportFailure,
                    "execution_argument_mismatch",
                ):
                    drift_client.poll_normalized_receipt(
                        execution_id=REAL_EXECUTION_ID,
                        idempotency_key="idempotency-001",
                        expected_binding=expected,
                        observed_at=datetime.now(timezone.utc),
                    )

    def test_poll_fails_closed_for_missing_malformed_and_failed_receipts(self) -> None:
        expected = _execution_argument()
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

        failed_action_client = ShuffleReceiptPollingClient(
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
                            "results": [_reviewed_action_result("FAILURE")],
                        }
                    ]
                }
            ),
        )
        receipt = failed_action_client.poll_normalized_receipt(
            execution_id=REAL_EXECUTION_ID,
            idempotency_key="idempotency-001",
            expected_binding=expected,
            observed_at=datetime.now(timezone.utc),
        )
        self.assertEqual(receipt["status"], "failed")

        missing_result_client = ShuffleReceiptPollingClient(
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
                        }
                    ]
                }
            ),
        )
        with self.assertRaisesRegex(
            ShuffleTransportFailure,
            "malformed_reviewed_action_result",
        ):
            missing_result_client.poll_normalized_receipt(
                execution_id=REAL_EXECUTION_ID,
                idempotency_key="idempotency-001",
                expected_binding=expected,
                observed_at=datetime.now(timezone.utc),
            )

    def test_lab_scripts_retry_transient_gets_and_hide_bearer_from_argv(
        self,
    ) -> None:
        trial_source = RUN_REAL_TRIAL.read_text(encoding="utf-8")
        bootstrap_source = BOOTSTRAP_SHUFFLE.read_text(encoding="utf-8")

        self.assertIn(
            'exc.category != "missing_receipt" and not exc.transient',
            trial_source,
        )
        self.assertIn('-H "@${auth_header_path}"', bootstrap_source)
        self.assertNotIn('-H "${auth_header}"', bootstrap_source)
        self.assertIn("unset api_key", bootstrap_source)
        self.assertIn('--rawfile password "${admin_password_path}"', bootstrap_source)
        self.assertIn("--data-binary @-", bootstrap_source)
        self.assertNotIn("--arg password", bootstrap_source)
        self.assertNotIn('--data-binary "${registration_payload}"', bootstrap_source)

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

    def test_real_transport_is_restricted_to_phase67_lab_composition(
        self,
    ) -> None:
        config = RuntimeConfig(
            shuffle_transport_mode="real_http",
            deployment_profile="single-customer",
        )

        with self.assertRaisesRegex(
            ValueError,
            "restricted to the Phase 67 integration lab",
        ):
            build_control_plane_service_composition(
                service=object(),
                config=config,
                store=object(),
                dependencies=mock.Mock(),
            )

    def test_evidence_validator_rejects_nonterminal_and_noninteger_proof(
        self,
    ) -> None:
        manifest = {
            "schema_version": "phase67.3-real-shuffle-trial-v1",
            "captured_at": "2026-07-29T00:00:00Z",
            "source_mode": "real_shuffle",
            "workflow_api_id": API_WORKFLOW_ID,
            "reviewed_template_id": "notify_identity_owner",
            "reviewed_template_version": (
                "notify_identity_owner-v1-reviewed-2026-05-03"
            ),
            "action_request_id": "action-request-001",
            "approval_decision_id": "approval-001",
            "delegation_id": "delegation-001",
            "execution_id": REAL_EXECUTION_ID,
            "idempotency_key": "idempotency-001",
            "idempotency_execution_count": 1,
            "correlation_id": "correlation-001",
            "requested_scope": {
                "record_family": "phase67_lab_trial",
                "record_id": SECOND_REAL_EXECUTION_ID,
                "finding_id": "finding-001",
                "recipient_identity": "local-test-sink",
            },
            "payload_hash": "a" * 64,
            "expected_execution_receipt_id": "phase67-receipt-001",
            "action_execution_id": "action-execution-001",
            "normalized_receipt_sha256": "b" * 64,
            "reconciliation_id": "reconciliation-001",
            "replay_reconciliation_id": "reconciliation-001",
            "execution_lifecycle_state": "succeeded",
            "reconciliation_disposition": "matched",
            "authority_posture": "aegisops_reconciliation_remains_authoritative",
            "limitations": (
                "isolated_non-production_lab",
                "harmless_local_echo_only",
                "no_production_integrations",
            ),
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
                "captured_at",
                None,
                "expected string",
            ),
            (
                "execution_lifecycle_state",
                "failed",
                "$.execution_lifecycle_state: value does not match const",
            ),
            (
                "reconciliation_disposition",
                "mismatch",
                "$.reconciliation_disposition: value does not match const",
            ),
            (
                "idempotency_execution_count",
                True,
                "$.idempotency_execution_count: value does not match const",
            ),
            (
                "idempotency_execution_count",
                1.0,
                "$.idempotency_execution_count: value does not match const",
            ),
        ):
            with self.subTest(field_name=field_name, invalid_value=invalid_value):
                result = validate({**manifest, field_name: invalid_value})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)

        missing_required = dict(manifest)
        missing_required.pop("action_execution_id")
        result = validate(missing_required)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required property 'action_execution_id'", result.stderr)
        result = validate({**manifest, "unexpected": "not-reviewed"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected properties", result.stderr)

    def test_preserved_workflow_validator_rejects_semantic_drift(self) -> None:
        workflow_id = API_WORKFLOW_ID
        observed = json.loads(WORKFLOW_TEMPLATE.read_text(encoding="utf-8"))
        observed["id"] = workflow_id

        def validate(candidate: dict[str, object]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable,
                    str(WORKFLOW_VALIDATOR),
                    str(WORKFLOW_TEMPLATE),
                    workflow_id,
                ],
                input=json.dumps(candidate),
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(validate(observed).returncode, 0)
        drifted_action = json.loads(json.dumps(observed))
        drifted_action["actions"][0]["name"] = "send_email"
        result = validate(drifted_action)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewed value changed", result.stderr)
        extra_action = json.loads(json.dumps(observed))
        extra_action["actions"].append(extra_action["actions"][0])
        result = validate(extra_action)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewed array length changed", result.stderr)
        extra_property = json.loads(json.dumps(observed))
        extra_property["actions"][0]["is_skipped"] = True
        result = validate(extra_property)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unreviewed properties", result.stderr)
        changed_server_default = json.loads(json.dumps(observed))
        changed_server_default["actions"][0]["execution_delay"] = 1
        result = validate(changed_server_default)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Shuffle server default changed", result.stderr)
        nested_type_drift = json.loads(json.dumps(observed))
        nested_type_drift["configuration"] = {
            "exit_on_error": 0,
            "skip_notifications": False,
            "start_from_top": False,
        }
        result = validate(nested_type_drift)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Shuffle server default changed", result.stderr)


if __name__ == "__main__":
    unittest.main()
