from __future__ import annotations

import importlib
import importlib.util
from contextlib import contextmanager
import pathlib
import sys
import threading
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
SUPPORT_PACKAGE_ROOT = TESTS_ROOT / "support"
SUPPORT_PACKAGE_NAME = "_control_plane_test_support"


class ControlPlaneTestSupportPackageTests(unittest.TestCase):
    def test_support_package_exposes_shared_control_plane_test_helpers(self) -> None:
        auth = _import_support_submodule("auth")
        fake_store = _import_support_submodule("fake_store")
        fixtures = _import_support_submodule("fixtures")
        payloads = _import_support_submodule("payloads")

        self.assertEqual(
            auth.REVIEWED_PROXY_SERVICE_ACCOUNT,
            "svc-aegisops-proxy-control-plane",
        )
        self.assertEqual(auth.REVIEWED_ANALYST_PRINCIPAL.identity, "analyst-001")
        self.assertEqual(
            auth.REVIEWED_PLATFORM_ADMIN_PRINCIPAL.identity,
            "platform-admin-001",
        )
        self.assertTrue(callable(fixtures.load_wazuh_fixture))
        self.assertTrue(callable(payloads.phase20_notify_identity_owner_payload))
        self.assertTrue(callable(payloads.approved_binding_hash))
        self.assertTrue(issubclass(fake_store.TransactionMutationStore, object))
        self.assertTrue(issubclass(fake_store.ConcurrentListMutationStore, object))
        self.assertTrue(issubclass(fake_store.CommitFailingStore, object))
        self.assertTrue(issubclass(fake_store.RecordTypeSaveFailingStore, object))
        self.assertTrue(issubclass(fake_store.ListCountingStore, object))
        self.assertTrue(issubclass(fake_store.OutOfBandMutationStore, object))

    def test_transaction_mutation_store_consumes_mutation_token_once(self) -> None:
        fake_store = _import_support_submodule("fake_store")

        store = fake_store.TransactionMutationStore(
            inner=_NoOpStore(),
            mutate_once=_BlockingMutation(),
        )

        self._run_transaction_threads(store)

        self.assertEqual(store.mutate_once.calls, 1)

    def test_concurrent_list_mutation_store_consumes_mutation_token_once(self) -> None:
        fake_store = _import_support_submodule("fake_store")

        mutation = _BlockingMutation()
        readiness_started = threading.Event()
        store = fake_store.ConcurrentListMutationStore(
            inner=_NoOpStore(readiness_started=readiness_started),
            mutate_once=mutation,
        )

        first_thread = threading.Thread(
            target=store.list,
            args=(object,),
        )
        first_thread.start()
        self.assertTrue(mutation.started.wait(timeout=1))

        second_thread = threading.Thread(
            target=store.inspect_readiness_aggregates,
        )
        second_thread.start()

        self.assertTrue(readiness_started.wait(timeout=1))
        mutation.release.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())
        self.assertEqual(mutation.calls, 1)

    def test_out_of_band_mutation_store_consumes_mutation_token_once(self) -> None:
        fake_store = _import_support_submodule("fake_store")

        store = fake_store.OutOfBandMutationStore(
            inner=_NoOpStore(),
            mutate_once=_BlockingMutation(),
        )

        self._run_transaction_threads(store)

        self.assertEqual(store.mutate_once.calls, 1)

    def _run_transaction_threads(self, store: object) -> None:
        first_ready = threading.Event()
        second_ready = threading.Event()

        first_thread = threading.Thread(
            target=self._run_transaction,
            args=(store, first_ready),
        )
        first_thread.start()
        self.assertTrue(first_ready.wait(timeout=1))
        self.assertTrue(store.mutate_once.started.wait(timeout=1))

        second_thread = threading.Thread(
            target=self._run_transaction,
            args=(store, second_ready),
        )
        second_thread.start()
        self.assertTrue(second_ready.wait(timeout=1))

        store.mutate_once.release.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())

    @staticmethod
    def _run_transaction(store: object, ready: threading.Event) -> None:
        ready.set()
        with store.transaction():
            return


def _import_support_submodule(module_name: str) -> object:
    _load_support_package()
    return importlib.import_module(f"{SUPPORT_PACKAGE_NAME}.{module_name}")


def _load_support_package() -> None:
    if SUPPORT_PACKAGE_NAME in sys.modules:
        return

    spec = importlib.util.spec_from_file_location(
        SUPPORT_PACKAGE_NAME,
        SUPPORT_PACKAGE_ROOT / "__init__.py",
        submodule_search_locations=[str(SUPPORT_PACKAGE_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load control-plane test support package")

    module = importlib.util.module_from_spec(spec)
    sys.modules[SUPPORT_PACKAGE_NAME] = module
    spec.loader.exec_module(module)


class _BlockingMutation:
    def __init__(self) -> None:
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self._lock = threading.Lock()

    def __call__(self, *_args: object) -> None:
        with self._lock:
            self.calls += 1
        self.started.set()
        self.release.wait(timeout=1)


class _NoOpStore:
    dsn = "sqlite://:memory:"
    persistence_mode = "test"

    def __init__(self, *, readiness_started: threading.Event | None = None) -> None:
        self._readiness_started = readiness_started

    def save(self, record: object) -> object:
        return record

    def get(self, record_type: object, record_id: str) -> None:
        return None

    def list(self, record_type: object) -> tuple[object, ...]:
        return ()

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        del record_family, record_id
        return None

    def inspect_readiness_aggregates(self) -> dict[str, object]:
        if self._readiness_started is not None:
            self._readiness_started.set()
        return {}

    @contextmanager
    def transaction(self, *, isolation_level: str | None = None):
        del isolation_level
        yield
