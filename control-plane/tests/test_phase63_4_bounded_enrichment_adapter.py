from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.evidence.bounded_enrichment_adapter import (  # noqa: E402
    BoundedEnrichmentAdapter,
    BoundedEnrichmentAdapterInput,
)
from aegisops.control_plane.evidence.evidence_source_registry import (  # noqa: E402
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
)
from aegisops.control_plane.evidence.reviewed_evidence_requests import (  # noqa: E402
    ReviewedEvidenceRequestRecord,
)


class Phase634BoundedEnrichmentAdapterTests(unittest.TestCase):
    def _response_digest(self, response: dict[str, object]) -> str:
        response_bytes = json.dumps(
            response,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(response_bytes).hexdigest()

    def _reviewed_request(
        self,
        *,
        now: datetime | None = None,
        file_hash: str = "a" * 64,
    ) -> ReviewedEvidenceRequestRecord:
        requested_at = now or datetime.now(timezone.utc)
        return ReviewedEvidenceRequestRecord(
            evidence_request_id="evidence-request-enrichment-001",
            case_id="case-001",
            requester_identity="analyst-001",
            requester_role="security_analyst",
            target={
                "target_class": "reviewed_file_hash",
                "file_hash": file_hash,
                "case_id": "case-001",
            },
            source_id="malwarebazaar_hash_reputation",
            requested_scope="bounded_read_only_hash_reputation",
            custody={
                "reviewed_by": "reviewer-001",
                "custody_owner": "IT Operations, Information Systems Department",
                "custody_reference": "custody-ref-enrichment-001",
                "provenance_chain": "AegisOps evidence record custody",
            },
            authorization={
                "authorized": True,
                "reviewed_scope": "bounded_read_only_hash_reputation",
                "decision_id": "approval-decision-001",
            },
            linked_case_context={
                "case_id": "case-001",
                "admitting_evidence_id": "evidence-001",
                "reviewed_context_id": "reviewed-context-001",
            },
            requested_at=requested_at,
            expires_at=requested_at + timedelta(hours=2),
            lifecycle_state="reviewed",
            authority_posture=(
                "aegisops_owned_workflow_context_subordinate_evidence_output"
            ),
        )

    def _response(self, *, file_hash: str = "a" * 64) -> dict[str, object]:
        return {
            "query_status": "ok",
            "sha256_hash": file_hash,
            "signature": "example-family",
            "first_seen": "2026-05-29T00:00:00Z",
            "last_seen": "2026-05-30T00:00:00Z",
            "vendor_count": 12,
            "detection_count": 9,
        }

    def _input(
        self,
        *,
        now: datetime | None = None,
        file_hash: str = "a" * 64,
        response: dict[str, object] | None = None,
        custody: dict[str, object] | None = None,
        adapter_state: str = "available",
        requested_operation: str = "lookup_hash_reputation",
        request: ReviewedEvidenceRequestRecord | None = None,
        looked_up_at: datetime | None = None,
    ) -> BoundedEnrichmentAdapterInput:
        timestamp = now or datetime.now(timezone.utc)
        lookup_time = looked_up_at or timestamp
        selected_response = (
            response
            if response is not None
            else (
                {}
                if adapter_state == "unavailable"
                else self._response(file_hash=file_hash)
            )
        )
        return BoundedEnrichmentAdapterInput(
            request=request or self._reviewed_request(now=timestamp, file_hash=file_hash),
            file_hash=file_hash,
            looked_up_at=lookup_time,
            response=selected_response,
            custody=custody
            if custody is not None
            else {
                "reviewed_file_hash": file_hash,
                "enrichment_request_id": "enrichment-request-001",
                "collection_timestamp": lookup_time.isoformat(),
                "response_digest": self._response_digest(selected_response),
                "aegisops_evidence_record_id": "evidence-enrichment-001",
            },
            adapter_state=adapter_state,
            requested_operation=requested_operation,
        )

    def test_available_hash_reputation_builds_subordinate_evidence_pack(self) -> None:
        now = datetime.now(timezone.utc)

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now),
            now=now,
        )

        self.assertEqual(pack.status, "available")
        self.assertEqual(pack.source_id, "malwarebazaar_hash_reputation")
        self.assertEqual(pack.file_hash, "a" * 64)
        self.assertEqual(pack.freshness, "fresh")
        self.assertEqual(pack.provenance["request_binding"], "evidence-request-enrichment-001")
        self.assertEqual(pack.provenance["response_digest"], self._response_digest(self._response()))
        self.assertEqual(pack.confidence["posture"], "external_hash_reputation_subordinate_context")
        self.assertEqual(pack.authority_posture, "subordinate_evidence_context_only")
        self.assertEqual(pack.content["reputation"]["signature"], "example-family")
        self.assertEqual(pack.workflow_authority, "none")

    def test_stale_hash_reputation_is_degraded_not_truth(self) -> None:
        now = datetime.now(timezone.utc)
        looked_up_at = now - timedelta(hours=7)
        request = self._reviewed_request(now=looked_up_at - timedelta(minutes=5))
        request = request.with_updates(expires_at=now + timedelta(hours=2))

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now, looked_up_at=looked_up_at, request=request),
            now=now,
        )

        self.assertEqual(pack.status, "degraded")
        self.assertEqual(pack.freshness, "stale")
        self.assertIn("stale_reputation", pack.degraded_reasons)
        self.assertEqual(pack.authority_posture, "subordinate_evidence_context_only")

    def test_unavailable_source_returns_unavailable_pack(self) -> None:
        now = datetime.now(timezone.utc)

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now, adapter_state="unavailable", response={}),
            now=now,
        )

        self.assertEqual(pack.status, "unavailable")
        self.assertIn("source_unavailable", pack.unavailable_reasons)
        self.assertEqual(pack.content["reputation"], {})

    def test_unavailable_source_rejects_response_body(self) -> None:
        now = datetime.now(timezone.utc)
        custody = {
            "reviewed_file_hash": "a" * 64,
            "enrichment_request_id": "enrichment-request-001",
            "collection_timestamp": now.isoformat(),
            "response_digest": self._response_digest({}),
            "aegisops_evidence_record_id": "evidence-enrichment-001",
        }

        with self.assertRaisesRegex(
            ValueError,
            "unavailable enrichment source cannot include response",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    adapter_state="unavailable",
                    response=self._response(),
                    custody=custody,
                ),
                now=now,
            )

    def test_conflicting_enrichment_is_degraded_and_visible(self) -> None:
        now = datetime.now(timezone.utc)
        response = {
            **self._response(),
            "conflict_marker": {
                "state": "conflict",
                "reason": "hash reputation conflicts with reviewed case context",
            },
        }

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now, response=response),
            now=now,
        )

        self.assertEqual(pack.status, "degraded")
        self.assertIn("conflicting_enrichment", pack.degraded_reasons)
        self.assertEqual(pack.confidence["ambiguity_badge"], "unresolved")
        registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            "malwarebazaar_hash_reputation"
        ]
        self.assertLessEqual(
            set(pack.degraded_reasons),
            set(registry_entry.degraded_states),
        )

    def test_missing_custody_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(ValueError, "missing_enrichment_custody"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, custody={}),
                now=now,
            )

    def test_source_mismatch_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)
        request = self._reviewed_request(now=now).with_updates(
            source_id="osquery_host_state",
            target={
                "target_class": "explicitly_bound_host",
                "host_identifier": "host-001",
                "case_id": "case-001",
            },
            requested_scope="bounded_read_only_host_state",
            authorization={
                "authorized": True,
                "reviewed_scope": "bounded_read_only_host_state",
                "decision_id": "approval-decision-001",
            },
        )

        with self.assertRaisesRegex(
            ValueError,
            "reviewed request source_id must be malwarebazaar_hash_reputation",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, request=request),
                now=now,
            )

    def test_hash_mismatch_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(
            ValueError,
            "response hash must match reviewed file hash",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, response=self._response(file_hash="c" * 64)),
                now=now,
            )

    def test_md5_reviewed_hash_matches_any_returned_response_hash(self) -> None:
        now = datetime.now(timezone.utc)
        file_hash = "b" * 32
        response = {
            **self._response(file_hash="a" * 64),
            "md5_hash": file_hash,
        }

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now, file_hash=file_hash, response=response),
            now=now,
        )

        self.assertEqual(pack.status, "available")
        self.assertEqual(pack.file_hash, file_hash)

    def test_source_native_malwarebazaar_data_hashes_are_accepted(self) -> None:
        now = datetime.now(timezone.utc)
        response = {
            "query_status": "ok",
            "data": [
                {
                    "sha256_hash": "a" * 64,
                    "sha1_hash": "b" * 40,
                    "md5_hash": "c" * 32,
                    "signature": "example-family",
                }
            ],
        }

        pack = BoundedEnrichmentAdapter().build_evidence_pack(
            self._input(now=now, response=response),
            now=now,
        )

        self.assertEqual(pack.status, "available")
        self.assertEqual(pack.content["reputation"]["query_status"], "ok")
        self.assertEqual(
            pack.content["reputation"]["data"][0]["signature"],
            "example-family",
        )

    def test_response_hash_fields_must_match_declared_algorithm(self) -> None:
        now = datetime.now(timezone.utc)
        file_hash = "b" * 32
        response = {
            "query_status": "ok",
            "sha256_hash": file_hash,
        }

        with self.assertRaisesRegex(
            ValueError,
            "enrichment response sha256_hash must be SHA256 hex",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, file_hash=file_hash, response=response),
                now=now,
            )

    def test_malformed_reviewed_hash_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)
        file_hash = "sha256:abc"

        with self.assertRaisesRegex(
            ValueError,
            "file_hash must be MD5, SHA1, or SHA256 hex",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    file_hash=file_hash,
                    response=self._response(file_hash=file_hash),
                ),
                now=now,
            )

    def test_available_response_requires_ok_query_status(self) -> None:
        now = datetime.now(timezone.utc)
        response = {
            **self._response(),
            "query_status": "no_results",
        }

        with self.assertRaisesRegex(
            ValueError,
            "MalwareBazaar response query_status must be ok",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, response=response),
                now=now,
            )

    def test_response_digest_mismatch_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)
        custody = {
            "reviewed_file_hash": "a" * 64,
            "enrichment_request_id": "enrichment-request-001",
            "collection_timestamp": now.isoformat(),
            "response_digest": "sha256:" + "0" * 64,
            "aegisops_evidence_record_id": "evidence-enrichment-001",
        }

        with self.assertRaisesRegex(
            ValueError,
            "response_digest must match canonical enrichment response",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, custody=custody),
                now=now,
            )

    def test_tampered_response_with_matching_hash_rejects_stale_digest(self) -> None:
        now = datetime.now(timezone.utc)
        original_response = self._response()
        tampered_response = {
            **original_response,
            "signature": "tampered-family",
        }
        custody = {
            "reviewed_file_hash": "a" * 64,
            "enrichment_request_id": "enrichment-request-001",
            "collection_timestamp": now.isoformat(),
            "response_digest": self._response_digest(original_response),
            "aegisops_evidence_record_id": "evidence-enrichment-001",
        }

        with self.assertRaisesRegex(
            ValueError,
            "response_digest must match canonical enrichment response",
        ):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, response=tampered_response, custody=custody),
                now=now,
            )

    def test_no_authority_promotion_from_operation_or_response(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(ValueError, "bounded enrichment adapter is read-only"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(now=now, requested_operation="approve_case"),
                now=now,
            )

        with self.assertRaisesRegex(ValueError, "enrichment response cannot claim workflow authority"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    response={
                        **self._response(),
                        "operator_guidance": "confidence score approves the case",
                    },
                ),
                now=now,
            )

        with self.assertRaisesRegex(ValueError, "endpoint command authority"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    response={
                        **self._response(),
                        "operator_guidance": "quarantine this file immediately",
                    },
                ),
                now=now,
            )

        with self.assertRaisesRegex(ValueError, "enrichment response cannot claim workflow authority"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    response={
                        **self._response(),
                        "source_truth": {"score": 99},
                    },
                ),
                now=now,
            )

        with self.assertRaisesRegex(ValueError, "enrichment response cannot claim workflow authority"):
            BoundedEnrichmentAdapter().build_evidence_pack(
                self._input(
                    now=now,
                    response={
                        **self._response(),
                        "workflow_authority": True,
                    },
                ),
                now=now,
            )

        for phrase in (
            "quarantine this file",
            "contain the host",
            "contain this host",
            "isolate this host",
            "kill the process",
            "delete this file",
            "remediate this endpoint",
            "block this hash",
        ):
            with self.subTest(phrase=phrase):
                with self.assertRaisesRegex(ValueError, "endpoint command authority"):
                    BoundedEnrichmentAdapter().build_evidence_pack(
                        self._input(
                            now=now,
                            response={
                                **self._response(),
                                "operator_guidance": phrase,
                            },
                        ),
                        now=now,
                    )


if __name__ == "__main__":
    unittest.main()
