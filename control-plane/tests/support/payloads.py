from __future__ import annotations

import hashlib
import json


def approved_binding_hash(
    *,
    target_scope: dict[str, object],
    approved_payload: dict[str, object],
    execution_surface_type: str,
    execution_surface_id: str,
) -> str:
    binding = {
        "approved_payload": approved_payload,
        "execution_surface_id": execution_surface_id,
        "execution_surface_type": execution_surface_type,
        "target_scope": target_scope,
    }
    encoded = json.dumps(binding, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def phase20_notify_identity_owner_payload(
    *,
    recipient_identity: str,
    case_id: str,
    alert_id: str,
    finding_id: str,
    source_record_family: str = "recommendation",
    source_record_id: str = "recommendation-001",
    recommendation_id: str = "recommendation-001",
    linked_evidence_ids: tuple[str, ...] = ("evidence-001",),
    message_intent: str = (
        "Notify the accountable owner about the reviewed low-risk escalation."
    ),
    escalation_reason: str = (
        "Reviewed evidence requires a bounded single-recipient owner notification."
    ),
) -> dict[str, object]:
    return {
        "action_type": "notify_identity_owner",
        "recipient_identity": recipient_identity,
        "message_intent": message_intent,
        "escalation_reason": escalation_reason,
        "source_record_family": source_record_family,
        "source_record_id": source_record_id,
        "recommendation_id": recommendation_id,
        "case_id": case_id,
        "alert_id": alert_id,
        "finding_id": finding_id,
        "linked_evidence_ids": linked_evidence_ids,
    }


def phase26_create_tracking_ticket_payload(
    *,
    case_id: str,
    alert_id: str,
    finding_id: str,
    coordination_reference_id: str,
    coordination_target_type: str = "zammad",
    ticket_title: str = "Investigate reviewed case follow-up",
    ticket_description: str = (
        "Open one reviewed coordination ticket for bounded operator follow-up."
    ),
    ticket_severity: str = "medium",
) -> dict[str, object]:
    return {
        "action_type": "create_tracking_ticket",
        "case_id": case_id,
        "alert_id": alert_id,
        "finding_id": finding_id,
        "coordination_reference_id": coordination_reference_id,
        "coordination_target_type": coordination_target_type,
        "ticket_title": ticket_title,
        "ticket_description": ticket_description,
        "ticket_severity": ticket_severity,
    }
