from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import ServicePersistenceTestBase
from aegisops_control_plane.models import AlertRecord, AnalyticSignalRecord, CaseRecord

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class IngestCaseLifecyclePersistenceTests(ServicePersistenceTestBase):
    def test_service_merges_reviewed_context_for_existing_alert_updates(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-001",
            },
        }
        reviewed_context_update = {
            "asset": {
                "criticality": "high",
            },
            "identity": {
                "owner": "identity-operations",
            },
        }
        materially_new_reviewed_context = {
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            }
        }
        merged_reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        created = service.ingest_finding_alert(
            finding_id="finding-merge-001",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-merge-001",
                source_record_id="substrate-detection-merge-001",
                alert_id=created.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)
        context_updated = service.ingest_finding_alert(
            finding_id="finding-merge-001",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_update,
        )
        materially_updated = service.ingest_finding_alert(
            finding_id="finding-merge-002",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-002",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            materially_new_work=True,
            reviewed_context=materially_new_reviewed_context,
        )

        self.assertEqual(context_updated.disposition, "updated")
        self.assertEqual(materially_updated.disposition, "updated")
        self.assertEqual(context_updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(materially_updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(context_updated.alert.case_id, promoted_case.case_id)
        self.assertEqual(materially_updated.alert.case_id, promoted_case.case_id)
        self.assertEqual(context_updated.alert.reviewed_context, {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
        })
        self.assertEqual(materially_updated.alert.reviewed_context, merged_reviewed_context)
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            merged_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, created.alert.analytic_signal_id).reviewed_context,
            service.get_record(AlertRecord, created.alert.alert_id).reviewed_context,
        )

    def test_service_preserves_reviewed_context_when_native_detection_links_existing_case(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-001",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
            },
        }
        reviewed_context_update = {
            "asset": {
                "criticality": "high",
            },
            "identity": {
                "owner": "identity-operations",
            },
        }
        reviewed_context_followup = {
            "privilege": {
                "delegated_authority": "reviewed",
            },
        }
        merged_reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-native-link-001",
                source_record_id="substrate-detection-native-link-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        updated_result = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_update,
        )
        followup_result = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_followup,
        )
        native_record = NativeDetectionRecord(
            substrate_key="wazuh",
            native_record_id="native-detection-001",
            record_kind="alert",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            metadata={},
        )

        linked = service._attach_native_detection_context(
            record=native_record,
            ingest_result=updated_result,
            substrate_detection_record_id="substrate-detection-native-link-001",
        )
        relinked = service._attach_native_detection_context(
            record=native_record,
            ingest_result=followup_result,
            substrate_detection_record_id="substrate-detection-native-link-001",
        )

        self.assertEqual(linked.alert.case_id, promoted_case.case_id)
        self.assertEqual(relinked.alert.case_id, promoted_case.case_id)
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            merged_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            merged_reviewed_context,
        )

    def test_service_extends_promoted_wazuh_alert_with_existing_case_linkage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)

        restated_payload = _load_wazuh_fixture("agent-origin-alert.json")
        restated_payload["id"] = "1731595888.5000001"
        restated_payload["timestamp"] = "2026-04-05T12:15:00+00:00"
        restated = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(restated_payload),
        )

        restated_signal = service.get_record(
            AnalyticSignalRecord,
            restated.reconciliation.analytic_signal_id,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )

        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, promoted_case.case_id)
        self.assertEqual(restated.alert.lifecycle_state, "escalated_to_case")
        self.assertIsNotNone(restated_signal)
        self.assertEqual(restated_signal.case_ids, (promoted_case.case_id,))
        self.assertIsNotNone(reconciliation)
        self.assertEqual(
            reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )

        persisted_case = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(persisted_case)
        self.assertEqual(persisted_case.alert_id, created.alert.alert_id)
        self.assertEqual(persisted_case.finding_id, created.alert.finding_id)
        self.assertEqual(persisted_case.lifecycle_state, "open")
        evidence_records = sorted(
            (
                evidence
                for evidence in store.list(EvidenceRecord)
                if evidence.alert_id == created.alert.alert_id
            ),
            key=lambda evidence: evidence.evidence_id,
        )
        self.assertEqual(len(evidence_records), 2)
        self.assertEqual(
            sorted(evidence.evidence_id for evidence in evidence_records),
            sorted(persisted_case.evidence_ids),
        )
        self.assertEqual(
            tuple(evidence.case_id for evidence in evidence_records),
            (promoted_case.case_id, promoted_case.case_id),
        )

    def test_service_keeps_distinct_wazuh_incidents_separate_when_native_context_differs(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        first_payload = _load_wazuh_fixture("agent-origin-alert.json")
        second_payload = _load_wazuh_fixture("agent-origin-alert.json")
        second_payload["id"] = "1731595888.5000001"
        second_payload["timestamp"] = "2026-04-05T12:15:00+00:00"
        second_payload["location"] = "/var/log/secure"
        second_payload["data"] = {
            "srcip": "203.0.113.77",
            "srcuser": "invalid-user",
        }

        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(first_payload),
        )
        distinct = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(second_payload),
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(distinct.disposition, "created")
        self.assertNotEqual(distinct.alert.alert_id, created.alert.alert_id)

        alerts = store.list(AlertRecord)
        self.assertEqual(len(alerts), 2)

        first_reconciliation = service.get_record(
            ReconciliationRecord,
            created.reconciliation.reconciliation_id,
        )
        second_reconciliation = service.get_record(
            ReconciliationRecord,
            distinct.reconciliation.reconciliation_id,
        )

        self.assertIsNotNone(first_reconciliation)
        self.assertIsNotNone(second_reconciliation)
        self.assertEqual(
            first_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            second_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731595888.5000001",),
        )

    def test_service_keeps_github_audit_repository_identity_separate_when_stable_ids_differ(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        first_payload = _load_wazuh_fixture("github-audit-alert.json")
        second_payload = _load_wazuh_fixture("github-audit-alert.json")
        second_payload["data"]["organization"]["id"] = "org-999"
        second_payload["data"]["repository"]["id"] = "repo-999"

        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(first_payload),
        )
        distinct = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(second_payload),
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(distinct.disposition, "created")
        self.assertNotEqual(distinct.alert.alert_id, created.alert.alert_id)
        self.assertNotEqual(
            created.reconciliation.correlation_key,
            distinct.reconciliation.correlation_key,
        )

        alerts = store.list(AlertRecord)
        self.assertEqual(len(alerts), 2)

        first_reconciliation = service.get_record(
            ReconciliationRecord,
            created.reconciliation.reconciliation_id,
        )
        second_reconciliation = service.get_record(
            ReconciliationRecord,
            distinct.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            first_reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-001",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-001",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )
        self.assertEqual(
            second_reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-999",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-999",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )

    def test_service_admits_github_audit_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("github-audit-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "github_audit",
                "accountable_source_identity": "manager:wazuh-manager-github-1",
                "delivery_path": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "octocat",
                    "display_name": "octocat",
                },
                "target": {
                    "identity_type": "team",
                    "identity_id": "security-reviews",
                    "display_name": "security-reviews",
                },
            },
            "asset": {
                "organization": {
                    "organization_id": "org-001",
                    "organization_name": "TommyKammy",
                },
                "repository": {
                    "repository_id": "repo-001",
                    "repository_name": "AegisOps",
                    "repository_full_name": "TommyKammy/AegisOps",
                },
            },
            "privilege": {
                "change_type": "membership_change",
                "scope": "repository_admin",
                "permission": "admin",
                "role": "maintainer",
            },
            "provenance": {
                "audit_action": "member.added",
                "request_id": "GH-REQ-0001",
                "rule_id": "github-audit-privilege-change",
                "rule_level": 8,
                "rule_description": "GitHub audit repository privilege change",
                "decoder_name": "github_audit",
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["accountable_source_identities"],
            ("manager:wazuh-manager-github-1",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-001",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-001",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )

    def test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance(
        self,
    ) -> None:
        replay_store, _ = make_store()
        replay_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=replay_store,
        )
        live_store, _ = make_store()
        live_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=live_store,
        )
        adapter = WazuhAlertAdapter()
        payload = _load_wazuh_fixture("github-audit-alert.json")

        replay_result = replay_service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(payload),
        )
        live_result = live_service.ingest_wazuh_alert(
            raw_alert=payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )

        self.assertEqual(
            replay_result.alert.reviewed_context["provenance"]["admission_channel"],
            "fixture_replay",
        )
        self.assertEqual(
            replay_result.alert.reviewed_context["provenance"]["admission_kind"],
            "replay",
        )
        self.assertEqual(
            live_result.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            live_result.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        self.assertEqual(
            replay_service.get_record(
                ReconciliationRecord,
                replay_result.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_channel": "fixture_replay",
                "admission_kind": "replay",
            },
        )
        self.assertEqual(
            live_service.get_record(
                ReconciliationRecord,
                live_result.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

    def test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        payload = _load_wazuh_fixture("github-audit-alert.json")

        created = service.ingest_wazuh_alert(
            raw_alert=payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)

        restated_payload = _load_wazuh_fixture("github-audit-alert.json")
        restated_payload["id"] = "1731595300.7654321"
        restated_payload["timestamp"] = "2026-04-05T12:25:00+00:00"
        restated = service.ingest_wazuh_alert(
            raw_alert=restated_payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        deduplicated = service.ingest_wazuh_alert(
            raw_alert=restated_payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )

        created_signal = service.get_record(
            AnalyticSignalRecord,
            created.alert.analytic_signal_id,
        )
        restated_signal = service.get_record(
            AnalyticSignalRecord,
            restated.reconciliation.analytic_signal_id,
        )
        restated_reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord,
            deduplicated.reconciliation.reconciliation_id,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, promoted_case.case_id)
        self.assertEqual(deduplicated.alert.case_id, promoted_case.case_id)
        self.assertEqual(restated.alert.lifecycle_state, "escalated_to_case")
        self.assertEqual(deduplicated.alert.lifecycle_state, "escalated_to_case")
        self.assertEqual(
            restated.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            restated.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        self.assertEqual(
            deduplicated.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            deduplicated.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )

        self.assertIsNotNone(created_signal)
        self.assertEqual(created_signal.case_ids, (promoted_case.case_id,))
        self.assertEqual(
            created_signal.substrate_detection_record_id,
            "wazuh:1731595300.1234567",
        )
        self.assertEqual(
            created_signal.last_seen_at,
            datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(restated_signal)
        self.assertEqual(restated_signal.case_ids, (promoted_case.case_id,))
        self.assertEqual(
            restated_signal.substrate_detection_record_id,
            "wazuh:1731595300.7654321",
        )
        self.assertEqual(
            restated_signal.last_seen_at,
            datetime(2026, 4, 5, 12, 25, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(restated_reconciliation)
        self.assertEqual(restated_reconciliation.ingest_disposition, "restated")
        self.assertEqual(
            restated_reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731595300.1234567", "wazuh:1731595300.7654321"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            (created.alert.analytic_signal_id, restated.reconciliation.analytic_signal_id),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )
        self.assertEqual(
            restated_reconciliation.last_seen_at,
            datetime(2026, 4, 5, 12, 25, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(deduplicated_reconciliation)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition,
            "deduplicated",
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage[
                "substrate_detection_record_ids"
            ],
            ("wazuh:1731595300.1234567", "wazuh:1731595300.7654321"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

        persisted_case = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(persisted_case)
        self.assertEqual(persisted_case.alert_id, created.alert.alert_id)
        self.assertEqual(persisted_case.finding_id, created.alert.finding_id)
        self.assertEqual(persisted_case.lifecycle_state, "open")
        self.assertEqual(
            persisted_case.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            persisted_case.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        evidence_records = sorted(
            (
                evidence
                for evidence in store.list(EvidenceRecord)
                if evidence.alert_id == created.alert.alert_id
            ),
            key=lambda evidence: evidence.evidence_id,
        )
        self.assertEqual(len(evidence_records), 2)
        self.assertEqual(
            tuple(evidence.case_id for evidence in evidence_records),
            (promoted_case.case_id, promoted_case.case_id),
        )

    def test_service_exposes_live_wazuh_entra_id_ingest_through_phase19_operator_surface(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("entra-id-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()
        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "entra_id",
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(case_detail.case_id, promoted_case.case_id)
        self.assertEqual(
            case_detail.reviewed_context["source"]["source_family"],
            "entra_id",
        )
        self.assertEqual(case_detail.linked_alert_ids, (admitted.alert.alert_id,))

    def test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("microsoft-365-audit-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "microsoft_365_audit",
                "accountable_source_identity": "manager:wazuh-manager-m365-1",
                "delivery_path": "microsoft365/contoso/exchange",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "alex@contoso.com",
                    "display_name": "Alex Rivera",
                },
                "target": {
                    "identity_type": "mailbox",
                    "identity_id": "shared-mailbox-finance",
                    "display_name": "shared-mailbox-finance",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-365-exchange",
                    "app_name": "Exchange Online",
                    "app_type": "workload",
                },
            },
            "authentication": {
                "method": "oauth2",
                "client_app": "Outlook",
                "result": "success",
            },
            "privilege": {
                "change_type": "permission_grant",
                "scope": "mailbox",
                "permission": "full_access",
            },
            "provenance": {
                "audit_action": "Add-MailboxPermission",
                "request_id": "M365-REQ-0001",
                "workload": "exchange",
                "operation": "Add-MailboxPermission",
                "record_type": "Microsoft 365 audit",
                "rule_id": "microsoft-365-audit-privilege-change",
                "rule_level": 7,
                "rule_description": "Microsoft 365 audit mailbox permission change",
                "decoder_name": "microsoft_365_audit",
                "location": "microsoft365/contoso/exchange",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "microsoft365/contoso/exchange",
                "data.source_family": "microsoft_365_audit",
                "data.audit_action": "Add-MailboxPermission",
                "data.workload": "exchange",
                "data.operation": "Add-MailboxPermission",
                "data.record_type": "Microsoft 365 audit",
                "data.actor.id": "alex@contoso.com",
                "data.actor.name": "Alex Rivera",
                "data.target.id": "shared-mailbox-finance",
                "data.target.name": "shared-mailbox-finance",
                "data.tenant.id": "tenant-001",
                "data.tenant.name": "Contoso",
                "data.app.id": "app-365-exchange",
                "data.app.name": "Exchange Online",
                "data.authentication.method": "oauth2",
                "data.authentication.client_app": "Outlook",
                "data.authentication.result": "success",
                "data.privilege.change_type": "permission_grant",
                "data.privilege.scope": "mailbox",
                "data.privilege.permission": "full_access",
            },
        )

    def test_service_admits_entra_id_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("entra-id-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "entra_id",
                "accountable_source_identity": "manager:wazuh-manager-entra-1",
                "delivery_path": "entra/contoso/directory",
            },
            "identity": {
                "actor": {
                    "identity_type": "service_principal",
                    "identity_id": "spn-operations",
                    "display_name": "Operations Automation",
                },
                "target": {
                    "identity_type": "role",
                    "identity_id": "role-global-admin",
                    "display_name": "Global Administrator",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-entra-admin",
                    "app_name": "Azure Portal",
                    "app_type": "service",
                },
            },
            "authentication": {
                "method": "mfa",
                "client_app": "Azure Portal",
                "result": "success",
            },
            "privilege": {
                "change_type": "role_assignment",
                "scope": "directory_role",
                "permission": "Global Administrator",
                "role": "Privileged Role Administrator",
            },
            "provenance": {
                "audit_action": "Add member to role",
                "request_id": "ENTRA-REQ-0001",
                "correlation_id": "entra-corr-0001",
                "operation": "Add member to role",
                "record_type": "Entra ID audit",
                "rule_id": "entra-id-role-assignment",
                "rule_level": 8,
                "rule_description": "Entra ID privileged role assignment",
                "decoder_name": "entra_id",
                "location": "entra/contoso/directory",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "entra/contoso/directory",
                "data.source_family": "entra_id",
                "data.audit_action": "Add member to role",
                "data.actor.id": "spn-operations",
                "data.actor.name": "Operations Automation",
                "data.target.id": "role-global-admin",
                "data.target.name": "Global Administrator",
                "data.tenant.id": "tenant-001",
                "data.tenant.name": "Contoso",
                "data.app.id": "app-entra-admin",
                "data.app.name": "Azure Portal",
                "data.authentication.method": "mfa",
                "data.authentication.client_app": "Azure Portal",
                "data.authentication.result": "success",
                "data.correlation_id": "entra-corr-0001",
                "data.operation": "Add member to role",
                "data.privilege.change_type": "role_assignment",
                "data.privilege.scope": "directory_role",
                "data.privilege.permission": "Global Administrator",
                "data.privilege.role": "Privileged Role Administrator",
                "data.record_type": "Entra ID audit",
            },
        )

    def test_service_admits_native_detection_records_via_substrate_adapter_boundary(self) -> None:
        @dataclass(frozen=True)
        class TestNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        admitted = service.ingest_native_detection_record(
            TestNativeRecordAdapter(),
            NativeDetectionRecord(
                substrate_key="test-substrate",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "test"},
            ),
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.finding_id, "finding::native-001")
        self.assertEqual(admitted.alert.analytic_signal_id, "signal::native-001")
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "test-substrate:native-001",
        )

    def test_service_trims_native_admission_provenance_before_persisting_reviewed_context(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class TestNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        admitted = service.ingest_native_detection_record(
            TestNativeRecordAdapter(),
            NativeDetectionRecord(
                substrate_key="test-substrate",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={
                    "admission_provenance": {
                        "admission_kind": " replay ",
                        "admission_channel": " fixture_replay ",
                    }
                },
            ),
        )

        self.assertEqual(
            admitted.alert.reviewed_context["provenance"],
            {
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        )
        self.assertEqual(
            service.get_record(
                ReconciliationRecord,
                admitted.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        )

    def test_service_rolls_back_native_ingest_when_evidence_timestamp_is_naive(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class TimestampNormalizingNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "record.first_seen_at must be timezone-aware",
        ):
            service.ingest_native_detection_record(
                TimestampNormalizingNativeRecordAdapter(),
                NativeDetectionRecord(
                    substrate_key="test-substrate",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0),
                    last_seen_at=datetime(2026, 4, 5, 12, 15),
                    metadata={"vendor": "test"},
                ),
            )

        self.assertEqual(store.list(AlertRecord), ())
        self.assertEqual(store.list(AnalyticSignalRecord), ())
        self.assertEqual(store.list(ReconciliationRecord), ())
        self.assertEqual(store.list(EvidenceRecord), ())

    def test_service_namespaces_fallback_substrate_detection_ids_by_substrate(self) -> None:
        @dataclass(frozen=True)
        class FallbackNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=None,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        first = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-a"),
            NativeDetectionRecord(
                substrate_key="substrate-a",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
                metadata={"vendor": "a"},
            ),
        )
        second = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-b"),
            NativeDetectionRecord(
                substrate_key="substrate-b",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "b"},
            ),
        )

        self.assertEqual(first.disposition, "created")
        self.assertEqual(second.disposition, "restated")
        self.assertIsNotNone(first.reconciliation.analytic_signal_id)
        self.assertIsNotNone(second.reconciliation.analytic_signal_id)
        self.assertNotEqual(
            first.reconciliation.analytic_signal_id,
            second.reconciliation.analytic_signal_id,
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-a:native-001", "substrate-b:native-001"),
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["analytic_signal_ids"],
            (
                first.reconciliation.analytic_signal_id,
                second.reconciliation.analytic_signal_id,
            ),
        )
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 2)

    def test_service_rejects_blank_substrate_keys_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankSubstrateAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "   "

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "adapter\\.substrate_key must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankSubstrateAdapter(),
                NativeDetectionRecord(
                    substrate_key="   ",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

    def test_service_rejects_blank_detection_id_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankDetectionIdAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id="   ",
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "substrate_detection_record_id/native_record_id must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankDetectionIdAdapter(),
                NativeDetectionRecord(
                    substrate_key="test-substrate",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

    def test_service_exposes_wazuh_origin_alerts_in_business_hours_analyst_queue(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()

        self.assertTrue(queue_view.read_only)
        self.assertEqual(queue_view.queue_name, "analyst_review")
        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["queue_selection"], "business_hours_triage")
        self.assertEqual(queue_view.records[0]["review_state"], "case_required")
        self.assertEqual(queue_view.records[0]["escalation_boundary"], "tracked_case")
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")
        self.assertEqual(
            queue_view.records[0]["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            queue_view.records[0]["accountable_source_identities"],
            ("agent:007",),
        )
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(queue_view.records[0]["case_lifecycle_state"], "open")
        self.assertEqual(
            queue_view.records[0]["native_rule"],
            {
                "id": "5710",
                "level": 10,
                "description": "SSH brute force attempt",
            },
        )
        self.assertEqual(len(queue_view.records[0]["evidence_ids"]), 1)

    def test_service_exposes_reviewed_context_in_analyst_queue_for_identity_rich_alerts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("microsoft-365-audit-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(
            queue_view.records[0]["reviewed_context"],
            admitted.alert.reviewed_context,
        )
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "microsoft_365_audit",
        )

    def test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )

        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        handoff_at = (
            service.list_lifecycle_transitions("case", promoted_case.case_id)[-1]
            .transitioned_at
            + timedelta(minutes=5)
        )
        handed_off_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=handoff_at,
            handoff_owner="analyst-001",
            handoff_note="Recheck repository owner membership against approved change window at next business-hours review.",
            follow_up_evidence_ids=(evidence_id,),
        )
        disposed_case = service.record_case_disposition(
            case_id=handed_off_case.case_id,
            disposition="business_hours_handoff",
            rationale="No same-day response required; preserve next-shift context and keep case open.",
            recorded_at=handoff_at,
        )

        detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(observation.case_id, promoted_case.case_id)
        self.assertEqual(observation.lifecycle_state, "confirmed")
        self.assertEqual(lead.case_id, promoted_case.case_id)
        self.assertEqual(lead.lifecycle_state, "triaged")
        self.assertEqual(recommendation.case_id, promoted_case.case_id)
        self.assertEqual(recommendation.lifecycle_state, "under_review")
        self.assertEqual(disposed_case.lifecycle_state, "pending_action")
        self.assertEqual(
            detail.case_record["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["triage"]["closure_rationale"],
            "No same-day response required; preserve next-shift context and keep case open.",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["handoff"]["note"],
            "Recheck repository owner membership against approved change window at next business-hours review.",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["handoff"]["handoff_owner"],
            "analyst-001",
        )
        self.assertEqual(detail.linked_observation_ids, (observation.observation_id,))
        self.assertEqual(detail.linked_lead_ids, (lead.lead_id,))
        self.assertIn(recommendation.recommendation_id, detail.linked_recommendation_ids)
        self.assertEqual(
            detail.linked_observation_records[0]["supporting_evidence_ids"],
            (evidence_id,),
        )
        self.assertEqual(
            detail.linked_lead_records[0]["triage_rationale"],
            "Privilege-impacting change needs durable business-hours follow-up.",
        )

    def test_service_allows_in_scope_case_assistant_context_on_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()

        snapshot = service.inspect_assistant_context("case", promoted_case.case_id)

        self.assertTrue(snapshot.read_only)
        self.assertEqual(snapshot.record_family, "case")
        self.assertEqual(snapshot.record_id, promoted_case.case_id)
        self.assertEqual(snapshot.record["case_id"], promoted_case.case_id)
        self.assertEqual(snapshot.advisory_output["output_kind"], "case_summary")
        self.assertIn(evidence_id, snapshot.linked_evidence_ids)

    def test_service_rejects_replay_only_case_from_phase19_operator_surface(self) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_assistant_context("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner="analyst-001",
                intended_outcome="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_handoff(
                case_id=promoted_case.case_id,
                handoff_at=reviewed_at,
                handoff_owner="analyst-001",
                handoff_note="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="business_hours_handoff",
                rationale="Replay-only casework must fail closed.",
                recorded_at=reviewed_at,
            )

    def test_service_rejects_case_scoped_advisory_reads_linked_to_replay_only_case(
        self,
    ) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-replay-linked-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-replay-linked-001",
                review_owner="reviewer-001",
                intended_outcome="Replay-linked advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-replay-linked-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=(),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        for record_family, record_id in (
            ("case", promoted_case.case_id),
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_rejects_synthetic_case_scoped_reads_spoofing_in_scope_case_lineage(
        self,
    ) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-synthetic-linked-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-synthetic-linked-001",
                review_owner="reviewer-001",
                intended_outcome="Synthetic case-scoped advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context={
                    "source": {
                        "source_family": "synthetic_review_fixture",
                        "admission_kind": "replay",
                    }
                },
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-synthetic-linked-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=("fixture://synthetic-phase19-review",),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        for record_family, record_id in (
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_rejects_synthetic_case_scoped_advisory_reads_from_ingested_finding_case(
        self,
    ) -> None:
        service, promoted_case, _ = self._build_phase19_synthetic_out_of_scope_case()

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_assistant_context("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_advisory_output("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.render_recommendation_draft("case", promoted_case.case_id)

    def test_service_rejects_ai_trace_subject_linkage_declaring_out_of_scope_provenance(
        self,
    ) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-trace-provenance-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-trace-provenance-001",
                review_owner="reviewer-001",
                intended_outcome="AI trace lineage must validate its own provenance.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-trace-provenance-001",
                subject_linkage={
                    "recommendation_ids": (recommendation.recommendation_id,),
                    "reviewed_source_profile": {
                        "source_family": "synthetic_review_fixture",
                    },
                    "admission_provenance": {
                        "admission_kind": "replay",
                        "admission_channel": "fixture_replay",
                    },
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=("fixture://synthetic-phase19-review",),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_advisory_output("ai_trace", ai_trace.ai_trace_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.render_recommendation_draft("ai_trace", ai_trace.ai_trace_id)

    def test_service_treats_non_mapping_provenance_context_as_out_of_scope(self) -> None:
        _, service, _, _, _ = self._build_phase19_in_scope_case()

        self.assertTrue(
            service._reviewed_context_declares_out_of_scope_provenance(
                "synthetic_review_fixture"
            )
        )

    def test_service_treats_missing_source_family_as_out_of_scope(self) -> None:
        _, service, _, _, _ = self._build_phase19_in_scope_case()

        self.assertTrue(
            service._reviewed_context_declares_out_of_scope_provenance(
                {
                    "provenance": {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    }
                }
            )
        )

    def test_service_rejects_non_github_audit_case_from_phase19_operator_surface(
        self,
    ) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="microsoft-365-audit-alert.json"
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Broader source-family casework must fail closed.",
            )

    def test_service_rejects_case_without_reciprocal_alert_linkage_from_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        spoofed_case = service.persist_record(
            CaseRecord(
                case_id="case-phase19-spoofed-alert-linkage",
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=dict(promoted_case.reviewed_context),
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(spoofed_case.case_id)

    def test_service_rejects_case_without_reciprocal_reconciliation_linkage_from_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        alert = service.get_record(AlertRecord, promoted_case.alert_id)
        self.assertIsNotNone(alert)

        spoofed_case_id = "case-phase19-spoofed-reconciliation-linkage"
        service.persist_record(
            replace(
                alert,
                case_id=spoofed_case_id,
            )
        )
        spoofed_case = service.persist_record(
            CaseRecord(
                case_id=spoofed_case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=dict(promoted_case.reviewed_context),
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(spoofed_case.case_id)

    def test_service_rejects_duplicate_casework_identifiers(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            observation_id="observation-phase19-duplicate-ids-001",
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Initial observation for duplicate-id guard coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        with self.assertRaisesRegex(
            ValueError,
            "observation_id 'observation-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                author_identity="analyst-002",
                observed_at=reviewed_at,
                scope_statement="Collision should be rejected before persist_record updates in place.",
                supporting_evidence_ids=(evidence_id,),
            )

        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            lead_id="lead-phase19-duplicate-ids-001",
            triage_owner="analyst-001",
            triage_rationale="Create a concrete lead before checking duplicate lead IDs.",
        )
        with self.assertRaisesRegex(
            ValueError,
            "lead_id 'lead-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                lead_id=lead.lead_id,
                triage_owner="analyst-002",
                triage_rationale="Collision should be rejected before persist_record updates in place.",
            )

        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            recommendation_id="recommendation-phase19-duplicate-ids-001",
            review_owner="analyst-001",
            intended_outcome="Establish a recommendation before checking duplicate recommendation IDs.",
        )
        with self.assertRaisesRegex(
            ValueError,
            "recommendation_id 'recommendation-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                lead_id=lead.lead_id,
                recommendation_id=recommendation.recommendation_id,
                review_owner="analyst-002",
                intended_outcome="Collision should be rejected before persist_record updates in place.",
            )

    def test_service_rejects_unknown_case_disposition(self) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported case disposition 'typo_pending_review'",
        ):
            service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="typo_pending_review",
                rationale="Typos should be rejected instead of changing lifecycle state.",
                recorded_at=reviewed_at,
            )

    def test_service_rejects_raced_observation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                ObservationRecord(
                    observation_id="observation-phase19-race-001",
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    supporting_evidence_ids=(evidence_id,),
                    author_identity="analyst-racer",
                    observed_at=reviewed_at,
                    scope_statement="Concurrent writer inserted the requested observation ID.",
                    lifecycle_state="confirmed",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "observation_id 'observation-phase19-race-001' already exists",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                observation_id="observation-phase19-race-001",
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Caller-supplied observation IDs must reject raced duplicates.",
                supporting_evidence_ids=(evidence_id,),
            )

    def test_service_rejects_raced_lead_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for raced lead collision coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                LeadRecord(
                    lead_id="lead-phase19-race-001",
                    observation_id=observation.observation_id,
                    finding_id=promoted_case.finding_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    triage_owner="analyst-racer",
                    triage_rationale="Concurrent writer inserted the requested lead ID.",
                    lifecycle_state="triaged",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "lead_id 'lead-phase19-race-001' already exists",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                lead_id="lead-phase19-race-001",
                triage_owner="analyst-001",
                triage_rationale="Caller-supplied lead IDs must reject raced duplicates.",
            )

    def test_service_rejects_raced_recommendation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for raced recommendation collision coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Seed lead for raced recommendation collision coverage.",
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                RecommendationRecord(
                    recommendation_id="recommendation-phase19-race-001",
                    lead_id=lead.lead_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    ai_trace_id=None,
                    review_owner="analyst-racer",
                    intended_outcome="Concurrent writer inserted the requested recommendation ID.",
                    lifecycle_state="under_review",
                    reviewed_context=promoted_case.reviewed_context,
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "recommendation_id 'recommendation-phase19-race-001' already exists",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                lead_id=lead.lead_id,
                recommendation_id="recommendation-phase19-race-001",
                review_owner="analyst-001",
                intended_outcome=(
                    "Caller-supplied recommendation IDs must reject raced duplicates."
                ),
            )

    def test_service_rejects_raced_generated_observation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                ObservationRecord(
                    observation_id="observation-phase19-generated-race-001",
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    supporting_evidence_ids=(evidence_id,),
                    author_identity="analyst-racer",
                    observed_at=reviewed_at,
                    scope_statement="Concurrent writer inserted the minted observation ID.",
                    lifecycle_state="confirmed",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="observation-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "observation_id 'observation-phase19-generated-race-001' already exists",
            ):
                service.record_case_observation(
                    case_id=promoted_case.case_id,
                    author_identity="analyst-001",
                    observed_at=reviewed_at,
                    scope_statement="Generated observation IDs must reject raced duplicates.",
                    supporting_evidence_ids=(evidence_id,),
                )

        observations = store.list(ObservationRecord)
        self.assertEqual(len(observations), 1)
        self.assertEqual(
            observations[0].observation_id,
            "observation-phase19-generated-race-001",
        )

    def test_service_rejects_raced_generated_lead_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for generated lead race coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                LeadRecord(
                    lead_id="lead-phase19-generated-race-001",
                    observation_id=observation.observation_id,
                    finding_id=promoted_case.finding_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    triage_owner="analyst-racer",
                    triage_rationale="Concurrent writer inserted the minted lead ID.",
                    lifecycle_state="triaged",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="lead-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "lead_id 'lead-phase19-generated-race-001' already exists",
            ):
                service.record_case_lead(
                    case_id=promoted_case.case_id,
                    observation_id=observation.observation_id,
                    triage_owner="analyst-001",
                    triage_rationale="Generated lead IDs must reject raced duplicates.",
                )

        leads = store.list(LeadRecord)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].lead_id, "lead-phase19-generated-race-001")

    def test_service_rejects_raced_generated_recommendation_identifier_collision(
        self,
    ) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for generated recommendation race coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Seed lead for generated recommendation race coverage.",
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                RecommendationRecord(
                    recommendation_id="recommendation-phase19-generated-race-001",
                    lead_id=lead.lead_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    ai_trace_id=None,
                    review_owner="analyst-racer",
                    intended_outcome=(
                        "Concurrent writer inserted the minted recommendation ID."
                    ),
                    lifecycle_state="under_review",
                    reviewed_context=promoted_case.reviewed_context,
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="recommendation-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "recommendation_id 'recommendation-phase19-generated-race-001' already exists",
            ):
                service.record_case_recommendation(
                    case_id=promoted_case.case_id,
                    lead_id=lead.lead_id,
                    review_owner="analyst-001",
                    intended_outcome=(
                        "Generated recommendation IDs must reject raced duplicates."
                    ),
                )

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(
            recommendations[0].recommendation_id,
            "recommendation-phase19-generated-race-001",
        )

    def test_service_merges_concurrent_reviewed_context_into_case_handoff(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _TransactionMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(CaseRecord, promoted_case.case_id),
                    reviewed_context={
                        **dict(
                            transactional_store.get(
                                CaseRecord,
                                promoted_case.case_id,
                            ).reviewed_context
                        ),
                        "triage": {
                            "disposition": "pending_approval",
                            "closure_rationale": "Concurrent triage update",
                            "recorded_at": reviewed_at.isoformat(),
                        },
                    },
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        updated_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at,
            handoff_owner="analyst-001",
            handoff_note="Carry forward the next-step evidence review.",
            follow_up_evidence_ids=(evidence_id,),
        )

        self.assertEqual(
            updated_case.reviewed_context["triage"]["disposition"],
            "pending_approval",
        )
        self.assertEqual(
            updated_case.reviewed_context["asset"]["repository"]["repository_full_name"],
            "TommyKammy/AegisOps",
        )
        self.assertEqual(
            updated_case.reviewed_context["identity"]["actor"]["identity_id"],
            "octocat",
        )
        self.assertEqual(
            updated_case.reviewed_context["handoff"]["follow_up_evidence_ids"],
            (evidence_id,),
        )

    def test_service_merges_concurrent_reviewed_context_into_case_disposition(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, _, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _TransactionMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(CaseRecord, promoted_case.case_id),
                    reviewed_context={
                        **dict(
                            transactional_store.get(
                                CaseRecord,
                                promoted_case.case_id,
                            ).reviewed_context
                        ),
                        "handoff": {
                            "handoff_at": reviewed_at.isoformat(),
                            "handoff_owner": "analyst-002",
                            "note": "Concurrent handoff note",
                            "follow_up_evidence_ids": (),
                        },
                    },
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        updated_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="pending_approval",
            rationale="Disposition update should preserve concurrent handoff context.",
            recorded_at=reviewed_at,
        )

        self.assertEqual(
            updated_case.reviewed_context["handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            updated_case.reviewed_context["asset"]["repository"]["repository_full_name"],
            "TommyKammy/AegisOps",
        )
        self.assertEqual(
            updated_case.reviewed_context["identity"]["actor"]["identity_id"],
            "octocat",
        )
        self.assertEqual(
            updated_case.reviewed_context["triage"]["disposition"],
            "pending_approval",
        )

    def test_service_analyst_queue_prefers_explicit_wazuh_source_for_multi_source_linkage(
        self,
    ) -> None:
        self._assert_service_analyst_queue_prefers_wazuh_source_for_multi_source_linkage(
            wazuh_source_system="wazuh"
        )

    def test_service_analyst_queue_accepts_mixed_case_wazuh_source_for_multi_source_linkage(
        self,
    ) -> None:
        self._assert_service_analyst_queue_prefers_wazuh_source_for_multi_source_linkage(
            wazuh_source_system="WaZuH"
        )

    def test_service_alert_detail_prefers_higher_reconciliation_id_when_compared_at_ties(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        preferred_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-z",
            correlation_key=f"{reconciliation.correlation_key}:z",
        )
        service.persist_record(preferred_reconciliation)

        queue_view = service.inspect_analyst_queue()
        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            preferred_reconciliation.correlation_key,
        )
        self.assertEqual(
            detail.latest_reconciliation["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )
        self.assertEqual(
            detail.lineage["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )

    def test_service_analyst_queue_keeps_latest_wazuh_detection_when_newer_non_wazuh_detection_exists(
        self,
    ) -> None:
        (
            service,
            admitted,
            reviewed_wazuh_reconciliation,
            newer_non_wazuh_reconciliation,
        ) = self._persist_newer_non_wazuh_detection_reconciliation()

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            reviewed_wazuh_reconciliation.correlation_key,
        )
        self.assertNotEqual(
            queue_view.records[0]["correlation_key"],
            newer_non_wazuh_reconciliation.correlation_key,
        )

    def test_service_alert_detail_keeps_latest_wazuh_detection_when_newer_non_wazuh_detection_exists(
        self,
    ) -> None:
        (
            service,
            admitted,
            reviewed_wazuh_reconciliation,
            newer_non_wazuh_reconciliation,
        ) = self._persist_newer_non_wazuh_detection_reconciliation()

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(
            detail.latest_reconciliation["reconciliation_id"],
            reviewed_wazuh_reconciliation.reconciliation_id,
        )
        self.assertEqual(
            detail.lineage["reconciliation_id"],
            reviewed_wazuh_reconciliation.reconciliation_id,
        )
        self.assertNotEqual(
            detail.latest_reconciliation["reconciliation_id"],
            newer_non_wazuh_reconciliation.reconciliation_id,
        )

    def test_service_alert_detail_reports_wazuh_when_origin_is_inferred_from_detection_ids(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        subject_linkage = dict(reconciliation.subject_linkage)
        subject_linkage["source_systems"] = ("opensearch",)
        subject_linkage["substrate_detection_record_ids"] = (
            "WaZuH:1731594986.4931506",
        )
        service.persist_record(
            replace(reconciliation, subject_linkage=subject_linkage)
        )

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(detail.source_system, "wazuh")
        self.assertEqual(
            detail.lineage["substrate_detection_record_ids"],
            ("WaZuH:1731594986.4931506",),
        )

    def test_service_alert_detail_redacts_raw_native_payload_from_latest_reconciliation(
        self,
    ) -> None:
        store, _ = make_store()
        shared_secret = secrets.token_urlsafe(24)
        reverse_proxy_secret = secrets.token_urlsafe(24)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=shared_secret,
                wazuh_ingest_reverse_proxy_secret=reverse_proxy_secret,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        stored_reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(stored_reconciliation)
        self.assertIn("latest_native_payload", stored_reconciliation.subject_linkage)

        detail = service.inspect_alert_detail(admitted.alert.alert_id)
        detail_subject_linkage = detail.latest_reconciliation["subject_linkage"]

        self.assertIsInstance(detail_subject_linkage, dict)
        self.assertNotIn("latest_native_payload", detail_subject_linkage)
        self.assertEqual(
            detail_subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

    def test_service_alert_detail_excludes_case_only_sibling_evidence(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        sibling_evidence = EvidenceRecord(
            evidence_id="evidence-case-sibling-001",
            source_record_id="case-sibling-source-001",
            alert_id="alert-sibling-001",
            case_id=promoted_case.case_id,
            source_system="wazuh",
            collector_identity="collector://wazuh/live",
            acquired_at=datetime(2026, 4, 11, 14, 0, tzinfo=timezone.utc),
            derivation_relationship="correlated_case_context",
            lifecycle_state="linked",
        )
        service.persist_record(sibling_evidence)

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        linked_evidence_ids = {
            record["evidence_id"] for record in detail.linked_evidence_records
        }

        self.assertNotIn(sibling_evidence.evidence_id, linked_evidence_ids)

    def test_service_detail_surfaces_link_only_external_ticket_reference_on_alert_and_case(
        self,
    ) -> None:
        store, service, promoted_case, _, _ = self._build_phase19_in_scope_case()

        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id="coord-ref-alert-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id="coord-ref-alert-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        alert_detail = service.inspect_alert_detail(promoted_case.alert_id)
        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            alert_detail.alert["coordination_reference_id"],
            "coord-ref-alert-001",
        )
        self.assertEqual(
            alert_detail.alert["coordination_target_type"],
            "zammad",
        )
        self.assertEqual(
            alert_detail.alert["coordination_target_id"],
            "ZM-4242",
        )
        self.assertEqual(
            alert_detail.alert["ticket_reference_url"],
            "https://tickets.example.test/#ticket/4242",
        )
        self.assertEqual(
            alert_detail.case_record["coordination_reference_id"],
            "coord-ref-alert-001",
        )
        self.assertEqual(
            case_detail.case_record["coordination_reference_id"],
            "coord-ref-alert-001",
        )
        self.assertEqual(
            case_detail.case_record["coordination_target_type"],
            "zammad",
        )
        self.assertEqual(
            case_detail.case_record["coordination_target_id"],
            "ZM-4242",
        )
        self.assertEqual(
            case_detail.case_record["ticket_reference_url"],
            "https://tickets.example.test/#ticket/4242",
        )
        self.assertEqual(
            case_detail.linked_alert_records[0]["coordination_reference_id"],
            "coord-ref-alert-001",
        )
        self.assertEqual(
            alert_detail.external_ticket_reference["status"],
            "present",
        )
        self.assertEqual(
            case_detail.external_ticket_reference["status"],
            "present",
        )

    def test_service_detail_treats_distinct_coordination_reference_ids_as_mismatch(
        self,
    ) -> None:
        store, service, promoted_case, _, _ = self._build_phase19_in_scope_case()

        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id="coord-ref-alert-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id="coord-ref-case-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        alert_detail = service.inspect_alert_detail(promoted_case.alert_id)
        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            alert_detail.external_ticket_reference["status"],
            "linked_case_reference_mismatch",
        )
        self.assertEqual(
            case_detail.external_ticket_reference["status"],
            "linked_alert_reference_mismatch",
        )
        self.assertEqual(
            case_detail.external_ticket_reference["linked_alert_references"][0][
                "coordination_reference_id"
            ],
            "coord-ref-alert-001",
        )

    def test_service_detail_keeps_mismatched_external_ticket_reference_explicit(
        self,
    ) -> None:
        store, service, promoted_case, _, _ = self._build_phase19_in_scope_case()

        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id="coord-ref-alert-002",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id="coord-ref-case-002",
                coordination_target_type="zammad",
                coordination_target_id="ZM-5150",
                ticket_reference_url="https://tickets.example.test/#ticket/5150",
            )
        )

        alert_detail = service.inspect_alert_detail(promoted_case.alert_id)
        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            alert_detail.external_ticket_reference["status"],
            "linked_case_reference_mismatch",
        )
        self.assertEqual(
            case_detail.external_ticket_reference["status"],
            "linked_alert_reference_mismatch",
        )
        self.assertEqual(
            case_detail.external_ticket_reference["linked_alert_references"][0][
                "coordination_target_id"
            ],
            "ZM-4242",
        )

    def test_service_detail_flags_missing_linked_alert_reference_when_case_has_none(
        self,
    ) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        primary_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        assert primary_alert is not None
        service.persist_record(
            replace(
                primary_alert,
                coordination_reference_id="coord-ref-alert-004",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                primary_alert,
                alert_id="alert-phase26-linked-missing-002",
                finding_id="finding-phase26-linked-missing-002",
                analytic_signal_id="signal-phase26-linked-missing-002",
            )
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase26-linked-missing-002",
                source_record_id="source-phase26-linked-missing-002",
                alert_id="alert-phase26-linked-missing-002",
                case_id=promoted_case.case_id,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=reviewed_at,
                derivation_relationship="correlated_case_context",
                lifecycle_state="linked",
            )
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            case_detail.external_ticket_reference["status"],
            "linked_alert_reference_missing",
        )
        self.assertEqual(len(case_detail.linked_alert_records), 2)

    def test_service_detail_flags_mismatched_linked_alert_references_when_case_has_none(
        self,
    ) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        primary_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        assert primary_alert is not None
        service.persist_record(
            replace(
                primary_alert,
                coordination_reference_id="coord-ref-alert-005",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                primary_alert,
                alert_id="alert-phase26-linked-mismatch-002",
                finding_id="finding-phase26-linked-mismatch-002",
                analytic_signal_id="signal-phase26-linked-mismatch-002",
                coordination_reference_id="coord-ref-alert-006",
                coordination_target_type="zammad",
                coordination_target_id="ZM-5150",
                ticket_reference_url="https://tickets.example.test/#ticket/5150",
            )
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase26-linked-mismatch-002",
                source_record_id="source-phase26-linked-mismatch-002",
                alert_id="alert-phase26-linked-mismatch-002",
                case_id=promoted_case.case_id,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=reviewed_at,
                derivation_relationship="correlated_case_context",
                lifecycle_state="linked",
            )
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            case_detail.external_ticket_reference["status"],
            "linked_alert_reference_mismatch",
        )
        self.assertEqual(
            {
                reference["coordination_target_id"]
                for reference in case_detail.external_ticket_reference[
                    "linked_alert_references"
                ]
            },
            {"ZM-4242", "ZM-5150"},
        )

    def test_service_rejects_unreviewed_external_ticket_target_type(self) -> None:
        store, service, promoted_case, _, _ = self._build_phase19_in_scope_case()

        with self.assertRaisesRegex(
            ValueError,
            r"unsupported coordination_target_type 'jira'",
        ):
            service.persist_record(
                replace(
                    service.get_record(AlertRecord, promoted_case.alert_id),
                    coordination_reference_id="coord-ref-alert-003",
                    coordination_target_type="jira",
                    coordination_target_id="JIRA-123",
                    ticket_reference_url="https://tickets.example.test/browse/JIRA-123",
                )
            )

    def test_service_preserves_external_ticket_reference_during_ingest_updates(
        self,
    ) -> None:
        store, service, promoted_case, _, _ = self._build_phase19_in_scope_case()

        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id="coord-ref-shared-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id="coord-ref-shared-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        alert = service.get_record(AlertRecord, promoted_case.alert_id)
        signal = service.get_record(AnalyticSignalRecord, alert.analytic_signal_id)
        self.assertIsNotNone(signal)

        updated = service.ingest_finding_alert(
            finding_id=alert.finding_id,
            analytic_signal_id=alert.analytic_signal_id,
            substrate_detection_record_id=signal.substrate_detection_record_id,
            correlation_key=signal.correlation_key,
            first_seen_at=signal.first_seen_at,
            last_seen_at=signal.last_seen_at,
            materially_new_work=True,
            reviewed_context={"triage": {"owner": "coordination-review"}},
        )

        refreshed_alert = service.get_record(AlertRecord, updated.alert.alert_id)
        refreshed_case = service.get_record(CaseRecord, promoted_case.case_id)

        self.assertEqual(
            refreshed_alert.coordination_reference_id,
            "coord-ref-shared-001",
        )
        self.assertEqual(
            refreshed_case.coordination_reference_id,
            "coord-ref-shared-001",
        )
        self.assertEqual(refreshed_alert.coordination_target_type, "zammad")
        self.assertEqual(refreshed_case.coordination_target_id, "ZM-4242")
        self.assertEqual(
            refreshed_case.ticket_reference_url,
            "https://tickets.example.test/#ticket/4242",
        )

    def test_service_preserves_external_ticket_reference_during_case_rewrites(
        self,
    ) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()

        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id="coord-ref-shared-002",
                coordination_target_type="zammad",
                coordination_target_id="ZM-5150",
                ticket_reference_url="https://tickets.example.test/#ticket/5150",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id="coord-ref-shared-002",
                coordination_target_type="zammad",
                coordination_target_id="ZM-5150",
                ticket_reference_url="https://tickets.example.test/#ticket/5150",
            )
        )

        handed_off_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at,
            handoff_owner="analyst-002",
            handoff_note="Escalated to coordination review.",
        )
        closed_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="closed_resolved",
            rationale="Linked ticket reviewed and closed.",
            recorded_at=reviewed_at + timedelta(minutes=1),
        )
        closed_alert = service.get_record(AlertRecord, promoted_case.alert_id)

        self.assertEqual(
            handed_off_case.coordination_reference_id,
            "coord-ref-shared-002",
        )
        self.assertEqual(
            closed_case.coordination_reference_id,
            "coord-ref-shared-002",
        )
        self.assertEqual(
            closed_alert.coordination_reference_id,
            "coord-ref-shared-002",
        )
        self.assertEqual(closed_alert.coordination_target_id, "ZM-5150")
        self.assertEqual(
            closed_alert.ticket_reference_url,
            "https://tickets.example.test/#ticket/5150",
        )

    def test_service_analyst_queue_ignores_newer_action_execution_reconciliation(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-queue-001",
                approval_decision_id="approval-queue-001",
                case_id=None,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-queue-001",
                target_scope={"asset_id": "asset-queue-001"},
                payload_hash="payload-hash-queue-001",
                requested_at=datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
                expires_at=None,
                lifecycle_state="approved",
            )
        )
        service.reconcile_action_execution(
            action_request_id="action-request-queue-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-queue-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-queue-001",
                    "observed_at": datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            admitted.reconciliation.correlation_key,
        )
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")

    def test_service_analyst_queue_scans_reconciliations_once_for_multiple_alerts(self) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("github-audit-alert.json")
            ),
        )

        store.reconciliation_list_calls = 0
        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 2)
        self.assertEqual(store.reconciliation_list_calls, 1)

    def test_service_analyst_queue_sorts_unknown_last_seen_after_real_timestamps(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        seen_at = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)

        service.persist_record(
            AlertRecord(
                alert_id="alert-known-last-seen",
                finding_id="finding-known-last-seen",
                analytic_signal_id="signal-known-last-seen",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-known-last-seen",
                subject_linkage={
                    "alert_ids": ("alert-known-last-seen",),
                    "analytic_signal_ids": ("signal-known-last-seen",),
                    "substrate_detection_record_ids": ("wazuh:known-last-seen",),
                    "source_systems": ("wazuh",),
                },
                alert_id="alert-known-last-seen",
                finding_id="finding-known-last-seen",
                analytic_signal_id="signal-known-last-seen",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="wazuh:known-last-seen",
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                ingest_disposition="created",
                mismatch_summary="known last-seen timestamp",
                compared_at=seen_at,
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            AlertRecord(
                alert_id="alert-unknown-last-seen",
                finding_id="finding-unknown-last-seen",
                analytic_signal_id="signal-unknown-last-seen",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-unknown-last-seen",
                subject_linkage={
                    "alert_ids": ("alert-unknown-last-seen",),
                    "analytic_signal_ids": ("signal-unknown-last-seen",),
                    "substrate_detection_record_ids": ("wazuh:unknown-last-seen",),
                    "source_systems": ("wazuh",),
                },
                alert_id="alert-unknown-last-seen",
                finding_id="finding-unknown-last-seen",
                analytic_signal_id="signal-unknown-last-seen",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="wazuh:unknown-last-seen",
                first_seen_at=seen_at,
                last_seen_at=None,
                ingest_disposition="created",
                mismatch_summary="unknown last-seen timestamp",
                compared_at=seen_at,
                lifecycle_state="matched",
            )
        )

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 2)
        self.assertEqual(
            tuple(record["alert_id"] for record in queue_view.records),
            ("alert-known-last-seen", "alert-unknown-last-seen"),
        )

    def test_service_rejects_schema_invalid_records_before_they_are_inspectable(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            service.persist_record(
                AlertRecord(
                    alert_id="alert-invalid",
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                )
            )

        with self.assertRaises(ValueError):
            service.persist_record(
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid",
                    subject_linkage={"action_request_ids": ["action-request-001"]},
                    alert_id=None,
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    execution_run_id=None,
                    linked_execution_run_ids=(),
                    correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
                    first_seen_at=timestamp,
                    last_seen_at=timestamp,
                    ingest_disposition="invalid",
                    mismatch_summary="invalid disposition",
                    compared_at=timestamp,
                    lifecycle_state="matched",
                )
            )

        alert_snapshot = service.inspect_records("alert")
        reconciliation_snapshot = service.inspect_records("reconciliation")

        self.assertEqual(alert_snapshot.total_records, 0)
        self.assertEqual(alert_snapshot.records, ())
        self.assertIsNone(service.get_record(AlertRecord, "alert-invalid"))
        self.assertEqual(reconciliation_snapshot.total_records, 0)
        self.assertEqual(reconciliation_snapshot.records, ())
        self.assertIsNone(
            service.get_record(ReconciliationRecord, "reconciliation-invalid")
        )

    def test_service_upserts_alert_lifecycle_from_upstream_signals(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        restated_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)
        updated_seen = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        duplicate_seen = datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-002",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=restated_seen,
        )
        updated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=updated_seen,
            materially_new_work=True,
        )
        deduplicated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=duplicate_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(updated.disposition, "updated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.finding_id, "finding-001")
        self.assertEqual(restated.alert.analytic_signal_id, "signal-001")
        self.assertEqual(updated.alert.finding_id, "finding-003")
        self.assertEqual(updated.alert.analytic_signal_id, "signal-003")
        self.assertEqual(deduplicated.alert.finding_id, "finding-003")
        self.assertEqual(deduplicated.alert.analytic_signal_id, "signal-003")

        stored_alert = service.get_record(AlertRecord, created.alert.alert_id)
        self.assertEqual(stored_alert, updated.alert)
        self.assertEqual(stored_alert.lifecycle_state, "new")

        created_reconciliation = service.get_record(
            ReconciliationRecord, created.reconciliation.reconciliation_id
        )
        restated_reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        updated_reconciliation = service.get_record(
            ReconciliationRecord, updated.reconciliation.reconciliation_id
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord, deduplicated.reconciliation.reconciliation_id
        )
        self.assertEqual(created_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(created_reconciliation.ingest_disposition, "created")
        self.assertEqual(created_reconciliation.first_seen_at, first_seen)
        self.assertEqual(created_reconciliation.last_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(restated_reconciliation.ingest_disposition, "restated")
        self.assertEqual(restated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.last_seen_at, restated_seen)
        self.assertEqual(
            restated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )
        self.assertEqual(updated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(updated_reconciliation.ingest_disposition, "updated")
        self.assertEqual(updated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(updated_reconciliation.last_seen_at, updated_seen)
        self.assertEqual(
            updated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
        )
        self.assertEqual(deduplicated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition, "deduplicated"
        )
        self.assertEqual(deduplicated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(deduplicated_reconciliation.last_seen_at, duplicate_seen)
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
        )

        signal_one = service.get_record(AnalyticSignalRecord, "signal-001")
        signal_two = service.get_record(AnalyticSignalRecord, "signal-002")
        signal_three = service.get_record(AnalyticSignalRecord, "signal-003")

        self.assertEqual(signal_one.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_one.case_ids, ())
        self.assertEqual(signal_one.finding_id, "finding-001")
        self.assertEqual(
            signal_one.substrate_detection_record_id,
            "substrate-detection-001",
        )
        self.assertEqual(signal_one.correlation_key, "claim:host-001:privilege-escalation")
        self.assertEqual(signal_one.first_seen_at, first_seen)
        self.assertEqual(signal_one.last_seen_at, first_seen)

        self.assertEqual(signal_two.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_two.finding_id, "finding-002")
        self.assertEqual(
            signal_two.substrate_detection_record_id,
            "substrate-detection-002",
        )
        self.assertEqual(signal_two.first_seen_at, first_seen)
        self.assertEqual(signal_two.last_seen_at, restated_seen)

        self.assertEqual(signal_three.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_three.finding_id, "finding-003")
        self.assertEqual(
            signal_three.substrate_detection_record_id,
            "substrate-detection-003",
        )
        self.assertEqual(signal_three.first_seen_at, updated_seen)
        self.assertEqual(signal_three.last_seen_at, duplicate_seen)

    def test_service_restates_when_repeated_finding_adds_new_signal_identity(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        second_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=second_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)

        reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        self.assertEqual(reconciliation.ingest_disposition, "restated")
        self.assertEqual(
            reconciliation.subject_linkage["finding_ids"],
            ("finding-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )

    def test_service_rejects_naive_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(ValueError, "first_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "last_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15),
            )

    def test_service_rejects_inverted_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "last_seen_at must be greater than or equal to first_seen_at",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            )

    def test_service_rejects_blank_required_admission_identities(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "finding_id must be a non-empty string"):
            service.ingest_finding_alert(
                finding_id="   ",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

        with self.assertRaisesRegex(
            ValueError,
            "correlation_key must be a non-empty string",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key=" \t ",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

    def test_service_mints_analytic_signal_identity_when_admission_leaves_it_blank(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="   ",
            substrate_detection_record_id="",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertTrue(admitted.alert.analytic_signal_id.startswith("analytic-signal-"))

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].analytic_signal_id, admitted.alert.analytic_signal_id)
        self.assertIsNone(signals[0].substrate_detection_record_id)
        self.assertEqual(signals[0].finding_id, "finding-001")

        reconciliation = service.get_record(
            ReconciliationRecord, admitted.reconciliation.reconciliation_id
        )
        self.assertEqual(
            reconciliation.analytic_signal_id,
            admitted.alert.analytic_signal_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            (),
        )

    def test_service_inspects_analytic_signal_records_as_first_class_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        analytic_signal = AnalyticSignalRecord(
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            finding_id="finding-001",
            alert_ids=("alert-001",),
            case_ids=("case-001",),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            lifecycle_state="active",
        )

        service.persist_record(analytic_signal)

        self.assertEqual(
            service.get_record(AnalyticSignalRecord, "signal-001"),
            analytic_signal,
        )

        inspection = service.inspect_records("analytic_signal")

        self.assertTrue(inspection.read_only)
        self.assertEqual(inspection.record_family, "analytic_signal")
        self.assertEqual(inspection.total_records, 1)
        self.assertEqual(
            inspection.records[0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            inspection.records[0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )
