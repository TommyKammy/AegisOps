from __future__ import annotations

from dataclasses import replace
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
    BoundedEnrichmentEvidencePack,
)
from aegisops.control_plane.evidence.evidence_freshness_provenance_projection import (  # noqa: E402
    EvidenceFreshnessProvenanceProjectionInput,
    project_evidence_freshness_provenance,
)
from aegisops.control_plane.evidence.evidence_source_registry import (  # noqa: E402
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
)
from aegisops.control_plane.evidence.reviewed_evidence_requests import (  # noqa: E402
    ReviewedEvidenceRequestRecord,
)


class Phase635EvidenceFreshnessProvenanceProjectionTests(unittest.TestCase):
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
    ) -> ReviewedEvidenceRequestRecord:
        requested_at = now or datetime.now(timezone.utc)
        return ReviewedEvidenceRequestRecord(
            evidence_request_id="evidence-request-enrichment-001",
            case_id="case-001",
            requester_identity="analyst-001",
            requester_role="security_analyst",
            target={
                "target_class": "reviewed_file_hash",
                "file_hash": "a" * 64,
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

    def _response(self) -> dict[str, object]:
        return {
            "query_status": "ok",
            "sha256_hash": "a" * 64,
            "signature": "example-family",
            "first_seen": "2026-05-29T00:00:00Z",
            "last_seen": "2026-05-30T00:00:00Z",
        }

    def _pack(
        self,
        *,
        now: datetime | None = None,
        looked_up_at: datetime | None = None,
        response: dict[str, object] | None = None,
        adapter_state: str = "available",
    ) -> BoundedEnrichmentEvidencePack:
        timestamp = now or datetime.now(timezone.utc)
        lookup_time = looked_up_at or timestamp
        selected_response = (
            response
            if response is not None
            else ({} if adapter_state == "unavailable" else self._response())
        )
        request = self._reviewed_request(
            now=min(timestamp, lookup_time) - timedelta(minutes=5)
        ).with_updates(expires_at=timestamp + timedelta(hours=2))
        custody = {
            "reviewed_file_hash": "a" * 64,
            "enrichment_request_id": "enrichment-request-001",
            "collection_timestamp": lookup_time.isoformat(),
            "response_digest": self._response_digest(selected_response),
            "aegisops_evidence_record_id": "evidence-enrichment-001",
        }
        return BoundedEnrichmentAdapter().build_evidence_pack(
            BoundedEnrichmentAdapterInput(
                request=request,
                file_hash="a" * 64,
                looked_up_at=lookup_time,
                response=selected_response,
                custody=custody,
                adapter_state=adapter_state,
            ),
            now=timestamp,
        )

    def _projection_input(
        self,
        pack: BoundedEnrichmentEvidencePack,
        **updates: object,
    ) -> EvidenceFreshnessProvenanceProjectionInput:
        values: dict[str, object] = {
            "evidence_pack": pack,
            "consumer": "case_workbench",
            "expected_source_id": "malwarebazaar_hash_reputation",
            "expected_case_id": "case-001",
            "requested_workflow_authority": "none",
        }
        values.update(updates)
        return EvidenceFreshnessProvenanceProjectionInput(**values)

    def test_fresh_projection_for_case_workbench_is_subordinate(self) -> None:
        pack = self._pack()

        projection = project_evidence_freshness_provenance(
            self._projection_input(pack)
        )

        self.assertEqual(projection.consumer, "case_workbench")
        self.assertEqual(projection.freshness_state, "fresh")
        self.assertEqual(projection.custody_state, "complete")
        self.assertEqual(projection.confidence_state, "present")
        self.assertEqual(projection.provenance_state, "bound")
        self.assertEqual(projection.conflict_state, "none")
        self.assertEqual(projection.source_state, "available")
        self.assertEqual(projection.uncertainty_label, "related_entity_not_authoritative")
        self.assertFalse(projection.authoritative_workflow_truth)
        self.assertEqual(projection.workflow_authority, "none")

    def test_projection_returns_normalized_consumer_name(self) -> None:
        pack = self._pack()

        projection = project_evidence_freshness_provenance(
            self._projection_input(pack, consumer=" case_workbench ")
        )

        self.assertEqual(projection.consumer, "case_workbench")

    def test_stale_projection_preserves_uncertainty_without_truth_promotion(self) -> None:
        now = datetime.now(timezone.utc)
        pack = self._pack(now=now, looked_up_at=now - timedelta(hours=7))

        projection = project_evidence_freshness_provenance(
            self._projection_input(pack, consumer="ai_grounding")
        )

        self.assertEqual(projection.consumer, "ai_grounding")
        self.assertEqual(projection.freshness_state, "stale")
        self.assertEqual(projection.status, "degraded")
        self.assertIn("stale_reputation", projection.degraded_reasons)
        self.assertEqual(projection.uncertainty_label, "stale_review_required")
        self.assertFalse(projection.authoritative_workflow_truth)

    def test_projection_recomputes_freshness_for_aged_persisted_pack(self) -> None:
        built_at = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
        pack = self._pack(now=built_at, looked_up_at=built_at)
        persisted_pack = BoundedEnrichmentEvidencePack(**pack.as_dict())

        projection = project_evidence_freshness_provenance(
            self._projection_input(
                persisted_pack,
                projected_at=built_at + timedelta(hours=7),
            )
        )

        self.assertEqual(projection.freshness_state, "stale")
        self.assertEqual(projection.status, "degraded")
        self.assertIn("stale_reputation", projection.degraded_reasons)
        self.assertEqual(projection.confidence["freshness"], "stale")
        self.assertEqual(projection.uncertainty_label, "stale_review_required")
        self.assertFalse(projection.authoritative_workflow_truth)

    def test_conflicting_projection_is_unresolved_not_case_truth(self) -> None:
        response = {
            **self._response(),
            "conflict_marker": {
                "state": "conflict",
                "reason": "hash reputation conflicts with reviewed context",
            },
        }
        pack = self._pack(response=response)

        projection = project_evidence_freshness_provenance(
            self._projection_input(pack)
        )

        self.assertEqual(projection.status, "degraded")
        self.assertEqual(projection.conflict_state, "conflicting")
        self.assertEqual(projection.uncertainty_label, "unresolved_conflict")
        self.assertEqual(projection.confidence["ambiguity_badge"], "unresolved")
        self.assertFalse(projection.authoritative_workflow_truth)

    def test_unavailable_source_projects_prerequisite_failure(self) -> None:
        pack = self._pack(adapter_state="unavailable")

        projection = project_evidence_freshness_provenance(
            self._projection_input(pack)
        )

        self.assertEqual(projection.status, "unavailable")
        self.assertEqual(projection.source_state, "unavailable")
        self.assertIn("source_unavailable", projection.unavailable_reasons)
        self.assertEqual(projection.uncertainty_label, "source_unavailable")

    def test_missing_custody_confidence_provenance_or_uncertainty_fails_closed(self) -> None:
        pack = self._pack()
        malformed_cases = (
            ("custody", {"custody": {}}, "missing_projection_custody"),
            ("confidence", {"confidence": {}}, "missing_projection_confidence"),
            ("provenance", {"provenance": {}}, "missing_projection_provenance"),
            (
                "uncertainty",
                {"confidence": {"posture": "external_hash_reputation_subordinate_context"}},
                "missing_projection_uncertainty",
            ),
        )

        for label, pack_updates, expected_error in malformed_cases:
            with self.subTest(label=label):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{**pack.as_dict(), **pack_updates, "looked_up_at": pack.looked_up_at}
                )
                with self.assertRaisesRegex(ValueError, expected_error):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_provenance_bindings_must_match_pack_authority_fields(self) -> None:
        pack = self._pack()
        mismatch_cases = (
            ("request_binding", "evidence-request-other"),
            ("case_binding", "case-other"),
            ("target_binding", "b" * 64),
            ("source_id", "osquery_host_state"),
            ("enrichment_request_id", "enrichment-request-other"),
            (
                "collection_timestamp",
                (pack.looked_up_at + timedelta(minutes=1)).isoformat(),
            ),
            ("response_digest", "sha256:" + "b" * 64),
        )

        for field_name, field_value in mismatch_cases:
            with self.subTest(field_name=field_name):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{
                        **pack.as_dict(),
                        "looked_up_at": pack.looked_up_at,
                        "provenance": {
                            **dict(pack.provenance),
                            field_name: field_value,
                        },
                    }
                )
                with self.assertRaisesRegex(ValueError, "provenance_binding_mismatch"):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_custody_bindings_must_match_pack_hash_and_lookup_time(self) -> None:
        pack = self._pack()
        mismatch_cases = (
            ("reviewed_file_hash", "b" * 64),
            (
                "collection_timestamp",
                (pack.looked_up_at + timedelta(minutes=1)).isoformat(),
            ),
        )

        for field_name, field_value in mismatch_cases:
            with self.subTest(field_name=field_name):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{
                        **pack.as_dict(),
                        "looked_up_at": pack.looked_up_at,
                        "custody": {
                            **dict(pack.custody),
                            field_name: field_value,
                        },
                    }
                )
                with self.assertRaisesRegex(ValueError, "custody_binding_mismatch"):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_response_digest_must_match_packed_reputation_response(self) -> None:
        pack = self._pack()
        other_digest = self._response_digest(
            {
                **self._response(),
                "signature": "other-family",
            }
        )
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "custody": {
                    **dict(pack.custody),
                    "response_digest": other_digest,
                },
                "provenance": {
                    **dict(pack.provenance),
                    "response_digest": other_digest,
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "response_digest_mismatch"):
            project_evidence_freshness_provenance(
                self._projection_input(malformed_pack)
            )

    def test_packed_reputation_hash_must_match_reviewed_hash(self) -> None:
        pack = self._pack()
        other_response = {
            **self._response(),
            "sha256_hash": "b" * 64,
            "signature": "other-family",
        }
        other_digest = self._response_digest(other_response)
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "custody": {
                    **dict(pack.custody),
                    "response_digest": other_digest,
                },
                "provenance": {
                    **dict(pack.provenance),
                    "response_digest": other_digest,
                },
                "content": {
                    **dict(pack.content),
                    "reputation": other_response,
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "response_digest_mismatch"):
            project_evidence_freshness_provenance(
                self._projection_input(malformed_pack)
            )

    def test_confidence_posture_must_match_source_registry(self) -> None:
        pack = self._pack()
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "confidence": {
                    **dict(pack.confidence),
                    "posture": "case_truth_authority",
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "confidence_posture_mismatch"):
            project_evidence_freshness_provenance(
                self._projection_input(malformed_pack)
            )

    def test_conflicting_projection_requires_unresolved_confidence_badge(self) -> None:
        response = {
            **self._response(),
            "conflict_marker": {
                "state": "conflict",
                "reason": "hash reputation conflicts with reviewed context",
            },
        }
        pack = self._pack(response=response)
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "confidence": {
                    **dict(pack.confidence),
                    "ambiguity_badge": "related-entity",
                },
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            "confidence_ambiguity_badge_mismatch",
        ):
            project_evidence_freshness_provenance(
                self._projection_input(malformed_pack)
            )

    def test_unexpected_pack_status_fails_closed(self) -> None:
        pack = self._pack()
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "status": "case_truth",
            }
        )

        with self.assertRaisesRegex(ValueError, "unexpected_projection_status"):
            project_evidence_freshness_provenance(
                self._projection_input(malformed_pack)
            )

    def test_projection_status_requires_matching_reason(self) -> None:
        pack = self._pack()
        malformed_cases = (
            ("degraded", "degraded_reasons"),
            ("unavailable", "unavailable_reasons"),
        )

        for status, reason_field in malformed_cases:
            with self.subTest(status=status):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{
                        **pack.as_dict(),
                        "looked_up_at": pack.looked_up_at,
                        "status": status,
                        reason_field: (),
                    }
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "projection_status_requires_reason",
                ):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_unknown_projection_reason_codes_fail_closed(self) -> None:
        pack = self._pack()
        malformed_cases = (
            ("degraded_reasons", ("case_truth",)),
            ("unavailable_reasons", ("approval_truth",)),
        )

        for field_name, reason_codes in malformed_cases:
            with self.subTest(field_name=field_name):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{
                        **pack.as_dict(),
                        "looked_up_at": pack.looked_up_at,
                        field_name: reason_codes,
                    }
                )
                with self.assertRaisesRegex(ValueError, "unexpected_projection_reason"):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_projection_metadata_maps_cannot_claim_authority(self) -> None:
        pack = self._pack()
        malformed_cases = (
            (
                "custody_extra_authority_key",
                {
                    "custody": {
                        **dict(pack.custody),
                        "workflow_authority": "close_case",
                    },
                },
                "unexpected_projection_metadata",
            ),
            (
                "provenance_authority_value",
                {
                    "provenance": {
                        **dict(pack.provenance),
                        "custody_reference": "approval_truth",
                    },
                },
                "projection metadata cannot claim workflow authority",
            ),
            (
                "bound_provenance_authority_value",
                {
                    "provenance": {
                        **dict(pack.provenance),
                        "request_binding": "approval_truth",
                    },
                },
                "projection metadata cannot claim workflow authority",
            ),
        )

        for label, pack_updates, expected_error in malformed_cases:
            with self.subTest(label=label):
                malformed_pack = BoundedEnrichmentEvidencePack(
                    **{
                        **pack.as_dict(),
                        "looked_up_at": pack.looked_up_at,
                        **pack_updates,
                    }
                )
                with self.assertRaisesRegex(ValueError, expected_error):
                    project_evidence_freshness_provenance(
                        self._projection_input(malformed_pack)
                    )

    def test_projection_rejects_non_bounded_enrichment_sources(self) -> None:
        pack = self._pack()
        malformed_pack = BoundedEnrichmentEvidencePack(
            **{
                **pack.as_dict(),
                "looked_up_at": pack.looked_up_at,
                "source_id": "osquery_host_state",
                "provenance": {
                    **dict(pack.provenance),
                    "source_id": "osquery_host_state",
                },
                "confidence": {
                    **dict(pack.confidence),
                    "posture": (
                        "observed_host_state_subordinate_context"
                    ),
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "unsupported_projection_source"):
            project_evidence_freshness_provenance(
                self._projection_input(
                    malformed_pack,
                    expected_source_id="osquery_host_state",
                )
            )

    def test_projection_rechecks_current_source_registry_status(self) -> None:
        pack = self._pack()
        source_id = "malwarebazaar_hash_reputation"
        original_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id]
        try:
            PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id] = replace(
                original_entry,
                status="disabled",
            )
            disabled_projection = project_evidence_freshness_provenance(
                self._projection_input(pack)
            )

            self.assertEqual(disabled_projection.status, "unavailable")
            self.assertEqual(disabled_projection.source_state, "unavailable")
            self.assertIn("source_denied", disabled_projection.unavailable_reasons)
            self.assertEqual(
                disabled_projection.uncertainty_label,
                "source_unavailable",
            )

            PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id] = replace(
                original_entry,
                status="degraded",
            )
            degraded_projection = project_evidence_freshness_provenance(
                self._projection_input(pack)
            )

            self.assertEqual(degraded_projection.status, "degraded")
            self.assertEqual(degraded_projection.source_state, "degraded")
            self.assertIn("source_stale", degraded_projection.degraded_reasons)
            self.assertEqual(
                degraded_projection.uncertainty_label,
                "stale_review_required",
            )

            PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id] = replace(
                original_entry,
                status="case_truth",
            )
            with self.assertRaisesRegex(ValueError, "unexpected_source_status"):
                project_evidence_freshness_provenance(
                    self._projection_input(pack)
                )
        finally:
            PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id] = original_entry

    def test_source_or_case_mismatch_fails_closed(self) -> None:
        pack = self._pack()

        with self.assertRaisesRegex(ValueError, "source_mismatch"):
            project_evidence_freshness_provenance(
                self._projection_input(pack, expected_source_id="osquery_host_state")
            )

        with self.assertRaisesRegex(ValueError, "case_mismatch"):
            project_evidence_freshness_provenance(
                self._projection_input(pack, expected_case_id="case-other")
            )

    def test_projection_cannot_drive_case_closure_reconciliation_or_approval(self) -> None:
        pack = self._pack()

        for requested_authority in (
            "close_case",
            "reconcile_action",
            "approve_action",
        ):
            with self.subTest(requested_authority=requested_authority):
                with self.assertRaisesRegex(
                    ValueError,
                    "projection cannot drive workflow authority",
                ):
                    project_evidence_freshness_provenance(
                        self._projection_input(
                            pack,
                            requested_workflow_authority=requested_authority,
                        )
                    )


if __name__ == "__main__":
    unittest.main()
