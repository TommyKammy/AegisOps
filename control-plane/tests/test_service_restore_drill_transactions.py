from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _restore_readiness_test_support as support

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class RestoreDrillTransactionTests(ServicePersistenceTestBase):
    def test_service_phase21_backup_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        if seed_alert is None:
            self.fail("expected seeded alert record before snapshot export")

        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(
                replace(
                    seed_alert,
                    alert_id="alert-phase21-backup-concurrent-001",
                )
            ),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=snapshot_store,
        )

        statement_count_before_backup = len(backend.statements)
        backup = snapshot_service.export_authoritative_record_chain_backup()

        self.assertEqual(
            backend.statements[statement_count_before_backup][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(backup["record_counts"]["alert"], 1)
        self.assertEqual(len(backup["record_families"]["alert"]), 1)
        self.assertCountEqual(
            [record["alert_id"] for record in backup["record_families"]["alert"]],
            (promoted_case.alert_id,),
        )
        self.assertEqual(len(base_store.list(AlertRecord)), 2)
        self.assertEqual(
            concurrent_store.get(AlertRecord, "alert-phase21-backup-concurrent-001"),
            replace(
                seed_alert,
                alert_id="alert-phase21-backup-concurrent-001",
            ),
        )

    def test_service_phase21_restore_drill_reraises_unrelated_repeatable_read_value_errors(
        self,
    ) -> None:
        base_store, _ = make_store()
        _store, _service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        failing_store = IsolationLevelFallbackProbeStore(
            base_store,
            "synthetic repeatable read setup failure",
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=failing_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "synthetic repeatable read setup failure",
        ):
            failing_service.run_authoritative_restore_drill()

        self.assertEqual(
            failing_store.transaction_isolation_levels,
            ("REPEATABLE READ",),
        )

    def test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        readiness = restored_service.inspect_readiness_diagnostics()

        self.assertFalse(restore_summary.restore_drill.drill_passed)
        self.assertEqual(readiness.status, "failing_closed")
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
            readiness.startup["missing_bindings"],
        )
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
            readiness.startup["missing_bindings"],
        )

    def test_service_phase21_restore_drill_filters_non_authoritative_transition_subjects(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement=(
                "Keep a reviewed observation transition in the live store while "
                "the restore drill validates only the authoritative subset."
            ),
            supporting_evidence_ids=(evidence_id,),
        )

        self.assertIn(
            ("observation", observation.observation_id),
            {
                (record.subject_record_family, record.subject_record_id)
                for record in store.list(LifecycleTransitionRecord)
            },
        )

        restore_drill = service.run_authoritative_restore_drill()

        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))

    def test_service_phase21_readiness_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-readiness-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        readiness = snapshot_service.inspect_readiness_diagnostics()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(readiness.metrics["reconciliations"]["stale"], 0)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-readiness-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_restore_drill_uses_single_transaction_snapshot(
        self,
    ) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before restore drill")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-restore-drill-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        restore_drill = snapshot_service.run_authoritative_restore_drill()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            (seed_reconciliation.reconciliation_id,),
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-restore-drill-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_restore_drill_can_run_standalone_after_restore(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        restore_drill = restored_service.run_authoritative_restore_drill()

        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_case_ids,
            restore_summary.restore_drill.verified_case_ids,
        )
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            restore_summary.restore_drill.verified_reconciliation_ids,
        )
        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))

        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))

    def test_service_phase21_restore_drill_falls_back_when_nested_transaction_blocks_repeatable_read(
        self,
    ) -> None:
        base_store, _ = make_store()
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        fallback_store = IsolationLevelFallbackProbeStore(
            base_store,
            "Cannot set isolation_level while inside an active transaction",
        )
        fallback_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=fallback_store,
        )

        restore_drill = fallback_service.run_authoritative_restore_drill()

        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))
        self.assertEqual(
            fallback_store.transaction_isolation_levels,
            ("REPEATABLE READ", None),
        )

    def test_service_phase21_backup_fails_closed_when_lifecycle_history_is_missing(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        legacy_alert = AlertRecord(
            alert_id="alert-phase21-missing-history-export-001",
            finding_id="finding-phase21-missing-history-export-001",
            analytic_signal_id=None,
            case_id=None,
            lifecycle_state="new",
        )

        store.save(legacy_alert)

        with self.assertRaisesRegex(
            ValueError,
            (
                r"missing lifecycle transition history for alert record "
                r"'alert-phase21-missing-history-export-001'"
            ),
        ):
            service.export_authoritative_record_chain_backup()

    def test_service_phase21_backup_and_restore_drill_fail_closed_on_orphan_transition(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        orphan_transition = LifecycleTransitionRecord(
            transition_id="transition-phase21-orphan-export-001",
            subject_record_family="alert",
            subject_record_id="alert-phase21-orphan-export-001",
            previous_lifecycle_state=None,
            lifecycle_state="new",
            transitioned_at=reviewed_at + timedelta(minutes=1),
            attribution={"source": "test-fixture", "actor_identities": ()},
        )
        store.save(orphan_transition)

        error_pattern = (
            r"missing alert record 'alert-phase21-orphan-export-001' required by "
            r"lifecycle transition 'transition-phase21-orphan-export-001'"
        )
        with self.assertRaisesRegex(ValueError, error_pattern):
            service.export_authoritative_record_chain_backup()
        with self.assertRaisesRegex(ValueError, error_pattern):
            service.run_authoritative_restore_drill()

        self.assertIsNotNone(service.get_record(CaseRecord, promoted_case.case_id))

    def test_store_phase21_readiness_aggregates_use_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness aggregate snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-aggregate-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        original_count_grouped_by_field = base_store._count_grouped_by_field
        mutation_applied = False

        def count_grouped_by_field(
            record_type: object,
            field_name: str,
        ) -> dict[str, int]:
            nonlocal mutation_applied
            counts = original_count_grouped_by_field(record_type, field_name)
            if not mutation_applied:
                mutation_applied = True
                concurrent_store.save(concurrent_reconciliation)
            return counts

        statement_count_before_snapshot = len(backend.statements)
        with mock.patch.object(
            base_store,
            "_count_grouped_by_field",
            side_effect=count_grouped_by_field,
        ):
            aggregates = base_store.inspect_readiness_aggregates()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(aggregates.reconciliation_lifecycle_counts.get("stale", 0), 0)
        self.assertEqual(
            aggregates.latest_reconciliation.reconciliation_id
            if aggregates.latest_reconciliation is not None
            else None,
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-aggregate-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_readiness_avoids_full_table_list_reads(self) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, _service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(readiness.status, "ready")
        self.assertEqual(store.list_calls, 0)
