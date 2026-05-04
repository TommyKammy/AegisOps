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


class RestoreReadinessBoundaryTests(ServicePersistenceTestBase):
    def test_service_decomposes_backup_restore_codec_and_validation_boundaries(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        backup_restore_flow = (
            service._restore_readiness_service._backup_restore_flow
        )

        codec_module = importlib.import_module(
            "aegisops.control_plane.runtime.restore_backup_codec"
        )
        validation_module = importlib.import_module(
            "aegisops.control_plane.runtime.restore_backup_validation"
        )

        self.assertEqual(
            backup_restore_flow._backup_payload_codec.__class__.__module__,
            codec_module.__name__,
        )
        self.assertEqual(
            backup_restore_flow._restore_validation_boundary.__class__.__module__,
            validation_module.__name__,
        )
        for embedded_helper_name in (
            "_record_from_backup_payload",
            "_collect_restore_record_families",
            "_reject_duplicate_restore_identifiers",
            "_validate_restore_record_links",
            "_validate_restore_lifecycle_transitions",
        ):
            with self.subTest(helper_name=embedded_helper_name):
                self.assertFalse(
                    hasattr(backup_restore_flow, embedded_helper_name),
                    "backup/restore codec and validation helpers should live behind "
                    "focused runtime boundaries",
                )

    def test_service_round_trips_records_by_control_plane_identifier(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={"action_request_ids": ["action-request-001"]},
            alert_id=None,
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="n8n-exec-001",
            linked_execution_run_ids=("n8n-exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            ingest_disposition="matched",
            mismatch_summary="matched execution",
            compared_at=timestamp,
            lifecycle_state="matched",
        )

        service.persist_record(action_request)
        service.persist_record(reconciliation)

        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )
        self.assertEqual(
            service.get_record(ReconciliationRecord, "reconciliation-001"),
            reconciliation,
        )
        self.assertIsNone(service.get_record(ActionRequestRecord, "approval-001"))
        self.assertIsNone(service.get_record(ReconciliationRecord, "n8n-exec-001"))

    def test_service_routes_runtime_restore_and_readiness_through_diagnostics_boundary(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        diagnostics_service = (
            service._runtime_restore_readiness_diagnostics_service
        )

        self.assertIs(
            service._runtime_boundary_service,
            diagnostics_service._runtime_boundary_service,
        )
        self.assertIs(
            service._restore_readiness_service,
            diagnostics_service._restore_readiness_service,
        )

        with mock.patch.object(
            diagnostics_service,
            "describe_runtime",
            wraps=diagnostics_service.describe_runtime,
        ) as describe_runtime:
            service.describe_runtime()
        with mock.patch.object(
            diagnostics_service,
            "describe_startup_status",
            wraps=diagnostics_service.describe_startup_status,
        ) as describe_startup_status:
            service.describe_startup_status()
        with mock.patch.object(
            diagnostics_service,
            "export_authoritative_record_chain_backup",
            wraps=diagnostics_service.export_authoritative_record_chain_backup,
        ) as export_backup:
            service.export_authoritative_record_chain_backup()
        with mock.patch.object(
            diagnostics_service,
            "describe_shutdown_status",
            wraps=diagnostics_service.describe_shutdown_status,
        ) as describe_shutdown_status:
            service.describe_shutdown_status()
        with mock.patch.object(
            diagnostics_service,
            "inspect_readiness_diagnostics",
            wraps=diagnostics_service.inspect_readiness_diagnostics,
        ) as inspect_readiness_diagnostics:
            service.inspect_readiness_diagnostics()
        with mock.patch.object(
            diagnostics_service,
            "run_authoritative_restore_drill",
            wraps=diagnostics_service.run_authoritative_restore_drill,
        ) as run_authoritative_restore_drill:
            service.run_authoritative_restore_drill()

        describe_runtime.assert_called_once_with()
        describe_startup_status.assert_called_once_with()
        export_backup.assert_called_once_with()
        describe_shutdown_status.assert_called_once_with()
        inspect_readiness_diagnostics.assert_called_once_with()
        run_authoritative_restore_drill.assert_called_once_with()

    def test_service_exposes_read_only_record_and_reconciliation_inspection(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        latest_compared_at = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        alert = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="triaged",
        )
        matched = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "latest_native_payload": {"secret": "keep-in-store"},
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_compared_at,
            last_seen_at=first_compared_at,
            ingest_disposition="matched",
            mismatch_summary="matched upstream signal into alert lifecycle",
            compared_at=first_compared_at,
            lifecycle_state="matched",
        )
        stale = ReconciliationRecord(
            reconciliation_id="reconciliation-002",
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "execution_surface_types": ("automation_substrate",),
                "execution_surface_ids": ("n8n",),
                "latest_native_payload": {"secret": "keep-in-store"},
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="exec-001",
            linked_execution_run_ids=("exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=first_compared_at,
            last_seen_at=latest_compared_at,
            ingest_disposition="stale",
            mismatch_summary="stale downstream execution observation requires refresh",
            compared_at=latest_compared_at,
            lifecycle_state="stale",
        )

        service.persist_record(alert)
        service.persist_record(matched)
        service.persist_record(stale)

        records_view = service.inspect_records("alert")
        status_view = service.inspect_reconciliation_status()

        self.assertTrue(records_view.read_only)
        self.assertEqual(records_view.record_family, "alert")
        self.assertEqual(records_view.total_records, 1)
        self.assertEqual(records_view.records[0]["alert_id"], "alert-001")
        self.assertEqual(records_view.records[0]["lifecycle_state"], "triaged")

        self.assertTrue(status_view.read_only)
        self.assertEqual(status_view.total_records, 2)
        self.assertEqual(status_view.by_lifecycle_state, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.by_ingest_disposition, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.latest_compared_at, latest_compared_at)
        self.assertEqual(
            tuple(record["reconciliation_id"] for record in status_view.records),
            ("reconciliation-001", "reconciliation-002"),
        )
        self.assertNotIn(
            "latest_native_payload",
            status_view.records[0]["subject_linkage"],
        )
        self.assertNotIn(
            "latest_native_payload",
            status_view.records[1]["subject_linkage"],
        )
        stored_latest = service.get_record(type(stale), "reconciliation-002")
        self.assertIsNotNone(stored_latest)
        self.assertIn("latest_native_payload", stored_latest.subject_linkage)

    def test_service_accepts_injected_store_for_runtime_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://ignored.local/aegisops"),
            store=store,
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")
        self.assertEqual(snapshot.persistence_mode, "postgresql")

    def test_readiness_projection_does_not_import_postgres_adapter(self) -> None:
        module_path = (
            pathlib.Path(__file__).resolve().parents[1]
            / "aegisops"
            / "control_plane"
            / "runtime"
            / "restore_readiness_projection.py"
        )

        parsed = ast.parse(module_path.read_text())
        imported_modules: set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
                imported_modules.update(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )

        def _is_postgres_adapter_import(module_name: str) -> bool:
            parts = module_name.split(".")
            return any(
                parts[index : index + 2] == ["adapters", "postgres"]
                for index in range(len(parts) - 1)
            )

        self.assertFalse(
            any(_is_postgres_adapter_import(name) for name in imported_modules),
            "readiness projection should use the shared readiness contract, not the PostgreSQL adapter",
        )

    def test_service_wires_restore_readiness_internal_collaborators(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        restore_readiness_service = service._restore_readiness_service
        readiness_operability_helper = service._readiness_operability_helper

        self.assertTrue(
            hasattr(restore_readiness_service, "_backup_restore_flow"),
            "RestoreReadinessService should delegate backup/restore flow to a dedicated collaborator",
        )
        self.assertTrue(
            hasattr(restore_readiness_service, "_readiness_health_projection"),
            "RestoreReadinessService should delegate readiness projection to a dedicated collaborator",
        )
        self.assertIs(
            restore_readiness_service._readiness_operability_helper,
            readiness_operability_helper,
        )
        self.assertEqual(
            type(readiness_operability_helper).__module__,
            "aegisops.control_plane.runtime.readiness_operability",
        )
        for helper_name in (
            "_collect_readiness_review_snapshots",
            "_build_readiness_review_path_health",
            "_build_readiness_source_health",
            "_build_readiness_automation_substrate_health",
            "_build_optional_extension_operability",
        ):
            with self.subTest(helper_name=helper_name):
                self.assertFalse(hasattr(service, helper_name))
                self.assertTrue(hasattr(readiness_operability_helper, helper_name))

    def test_service_returns_nested_immutable_json_backed_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        record = ActionRequestRecord(
            action_request_id="action-request-immutable-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={
                "asset_ids": ["asset-001"],
                "filters": {"environment": "prod"},
            },
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        service.persist_record(record)
        persisted = service.get_record(
            ActionRequestRecord, "action-request-immutable-001"
        )

        assert persisted is not None
        with self.assertRaises(TypeError):
            persisted.target_scope["asset_ids"] += ("asset-002",)
        with self.assertRaises(TypeError):
            persisted.target_scope["filters"]["environment"] = "dev"  # type: ignore[index]

    def test_runtime_snapshot_reports_postgresql_authoritative_persistence_mode(self) -> None:
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.persistence_mode, "postgresql")
        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")

    def test_backup_restore_validation_does_not_import_postgres_adapter(self) -> None:
        module_path = (
            pathlib.Path(__file__).resolve().parents[1]
            / "aegisops"
            / "control_plane"
            / "runtime"
            / "restore_readiness_backup_restore.py"
        )

        parsed = ast.parse(module_path.read_text())
        imported_modules: set[str] = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
                imported_modules.update(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )

        def _is_postgres_adapter_import(module_name: str) -> bool:
            parts = module_name.split(".")
            return any(
                parts[index : index + 2] == ["adapters", "postgres"]
                for index in range(len(parts) - 1)
            )

        self.assertFalse(
            any(_is_postgres_adapter_import(name) for name in imported_modules),
            "backup/restore validation should use a shared record-validation boundary, not the PostgreSQL adapter",
        )

    def test_service_phase21_persist_record_rejects_direct_authoritative_transition_rows(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        orphan_transition = LifecycleTransitionRecord(
            transition_id="transition-phase21-orphan-alert-001",
            subject_record_family="alert",
            subject_record_id="alert-phase21-orphan-001",
            previous_lifecycle_state="new",
            lifecycle_state="closed",
            transitioned_at=datetime(2026, 4, 16, 0, 5, tzinfo=timezone.utc),
            attribution={"source": "test-fixture", "actor_identities": ("analyst-001",)},
        )

        with self.assertRaisesRegex(
            ValueError,
            "persist_record does not accept direct lifecycle transition records",
        ):
            service.persist_record(orphan_transition)

        self.assertEqual(store.list(LifecycleTransitionRecord), ())
