from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import inspect
import logging
import pathlib
import secrets
from types import SimpleNamespace
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.assistant.assistant_context import (
    _reviewed_context_identifier_citations,
)
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from aegisops.control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops.control_plane.actions.execution_coordinator import _approved_payload_binding_hash
from aegisops.control_plane.service import (
    AegisOpsControlPlaneService,
    AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
    NativeDetectionRecordAdapter,
)
from postgres_test_support import make_store
from support.fake_store import (
    CommitFailingStore,
    ConcurrentListMutationStore,
    ListCountingStore,
    OutOfBandMutationStore,
    RecordTypeSaveFailingStore,
    TransactionMutationStore,
)
from support.fixtures import load_wazuh_fixture
from support.payloads import (
    approved_binding_hash,
    phase26_create_tracking_ticket_payload,
    phase20_notify_identity_owner_payload,
)
from support.service_persistence import (
    ServicePersistenceTestBase as _SharedServicePersistenceTestBase,
)


_load_wazuh_fixture = load_wazuh_fixture
_approved_binding_hash = approved_binding_hash
_phase26_create_tracking_ticket_payload = phase26_create_tracking_ticket_payload
_phase20_notify_identity_owner_payload = phase20_notify_identity_owner_payload
_TransactionMutationStore = TransactionMutationStore
_ConcurrentListMutationStore = ConcurrentListMutationStore
_CommitFailingStore = CommitFailingStore
_RecordTypeSaveFailingStore = RecordTypeSaveFailingStore
_ListCountingStore = ListCountingStore
_OutOfBandMutationStore = OutOfBandMutationStore


# Keep an AST-visible unittest.TestCase base in this compatibility module so
# repo validation scripts still recognize legacy test classes as discoverable.
class ServicePersistenceTestBase(unittest.TestCase):
    pass


for _helper_name, _helper_value in vars(_SharedServicePersistenceTestBase).items():
    if _helper_name.startswith("__") and _helper_name.endswith("__"):
        continue
    setattr(ServicePersistenceTestBase, _helper_name, _helper_value)
