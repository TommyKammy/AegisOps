from __future__ import annotations

import argparse
from typing import Callable

from .entrypoint_support import (
    json_ready,
    normalize_alert_id,
    normalize_case_id,
    normalize_optional_string,
    parse_datetime_arg,
    read_json_file,
)
from .service import AegisOpsControlPlaneService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the reviewed control-plane runtime service or render read-only "
            "runtime, record, and reconciliation inspection views."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "serve",
        help="Run the reviewed long-running control-plane runtime service.",
    )
    subparsers.add_parser("runtime", help="Render the current runtime snapshot.")

    inspect_records = subparsers.add_parser(
        "inspect-records",
        help="Render a read-only view of one control-plane record family.",
    )
    inspect_records.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect.",
    )

    subparsers.add_parser(
        "inspect-reconciliation-status",
        help="Render a read-only reconciliation status summary.",
    )
    subparsers.add_parser(
        "startup-status",
        help="Render the reviewed production-like startup readiness summary.",
    )
    subparsers.add_parser(
        "shutdown-status",
        help="Render the reviewed controlled shutdown readiness summary.",
    )
    subparsers.add_parser(
        "backup-authoritative-record-chain",
        help="Render the reviewed authoritative backup payload for the control-plane record chain.",
    )
    restore_backup = subparsers.add_parser(
        "restore-authoritative-record-chain",
        help="Restore the reviewed authoritative backup payload into an empty control-plane store.",
    )
    restore_backup.add_argument(
        "--input",
        required=True,
        help="Path to the reviewed authoritative backup JSON payload.",
    )
    subparsers.add_parser(
        "run-authoritative-restore-drill",
        help="Reread the restored authoritative record chain through reviewed service inspections.",
    )
    subparsers.add_parser(
        "inspect-analyst-queue",
        help="Render the business-hours analyst review queue view.",
    )
    inspect_alert_detail = subparsers.add_parser(
        "inspect-alert-detail",
        help="Render the reviewed Wazuh-backed alert detail view for one alert.",
    )
    inspect_alert_detail.add_argument(
        "--alert-id",
        required=True,
        help="Control-plane alert identifier to inspect.",
    )
    inspect_case_detail = subparsers.add_parser(
        "inspect-case-detail",
        help="Render the approved case detail view for one case.",
    )
    inspect_case_detail.add_argument(
        "--case-id",
        required=True,
        help="Control-plane case identifier to inspect.",
    )
    promote_alert_to_case = subparsers.add_parser(
        "promote-alert-to-case",
        help="Promote one reviewed alert into durable bounded casework.",
    )
    promote_alert_to_case.add_argument(
        "--alert-id",
        required=True,
        help="Control-plane alert identifier to promote.",
    )
    promote_alert_to_case.add_argument(
        "--case-id",
        help="Optional case identifier to reuse when linking the alert.",
    )
    promote_alert_to_case.add_argument(
        "--case-lifecycle-state",
        default="open",
        help="Lifecycle state to apply when the case is first created.",
    )
    record_case_observation = subparsers.add_parser(
        "record-case-observation",
        help="Record a bounded reviewed case observation.",
    )
    record_case_observation.add_argument("--case-id", required=True)
    record_case_observation.add_argument("--author-identity", required=True)
    record_case_observation.add_argument("--observed-at", required=True)
    record_case_observation.add_argument("--scope-statement", required=True)
    record_case_observation.add_argument(
        "--supporting-evidence-id",
        action="append",
        default=[],
        help="Supporting evidence identifier to link; may be repeated.",
    )
    record_case_lead = subparsers.add_parser(
        "record-case-lead",
        help="Record a bounded reviewed triage lead for a case.",
    )
    record_case_lead.add_argument("--case-id", required=True)
    record_case_lead.add_argument("--triage-owner", required=True)
    record_case_lead.add_argument("--triage-rationale", required=True)
    record_case_lead.add_argument(
        "--observation-id",
        help="Optional observation identifier to anchor the lead.",
    )
    record_case_recommendation = subparsers.add_parser(
        "record-case-recommendation",
        help="Record a bounded reviewed recommendation for a case.",
    )
    record_case_recommendation.add_argument("--case-id", required=True)
    record_case_recommendation.add_argument("--review-owner", required=True)
    record_case_recommendation.add_argument("--intended-outcome", required=True)
    record_case_recommendation.add_argument(
        "--lead-id",
        help="Optional lead identifier to anchor the recommendation.",
    )
    record_case_handoff = subparsers.add_parser(
        "record-case-handoff",
        help="Record a bounded business-hours handoff note for a case.",
    )
    record_case_handoff.add_argument("--case-id", required=True)
    record_case_handoff.add_argument("--handoff-at", required=True)
    record_case_handoff.add_argument("--handoff-owner", required=True)
    record_case_handoff.add_argument("--handoff-note", required=True)
    record_case_handoff.add_argument(
        "--follow-up-evidence-id",
        action="append",
        default=[],
        help="Follow-up evidence identifier to link; may be repeated.",
    )
    record_case_disposition = subparsers.add_parser(
        "record-case-disposition",
        help="Record a bounded reviewed case disposition or closure state.",
    )
    record_case_disposition.add_argument("--case-id", required=True)
    record_case_disposition.add_argument("--disposition", required=True)
    record_case_disposition.add_argument("--rationale", required=True)
    record_case_disposition.add_argument("--recorded-at", required=True)
    record_action_review_manual_fallback = subparsers.add_parser(
        "record-action-review-manual-fallback",
        help="Record reviewed manual-fallback runtime visibility for one action review.",
    )
    record_action_review_manual_fallback.add_argument("--action-request-id", required=True)
    record_action_review_manual_fallback.add_argument("--fallback-at", required=True)
    record_action_review_manual_fallback.add_argument(
        "--fallback-actor-identity",
        required=True,
    )
    record_action_review_manual_fallback.add_argument("--authority-boundary", required=True)
    record_action_review_manual_fallback.add_argument("--reason", required=True)
    record_action_review_manual_fallback.add_argument("--action-taken", required=True)
    record_action_review_manual_fallback.add_argument(
        "--verification-evidence-id",
        action="append",
        default=[],
        help="Verification evidence identifier to link; may be repeated.",
    )
    record_action_review_manual_fallback.add_argument(
        "--residual-uncertainty",
        help="Optional unresolved follow-up or uncertainty note.",
    )
    record_action_review_escalation_note = subparsers.add_parser(
        "record-action-review-escalation-note",
        help="Record reviewed escalation-note visibility for one action review.",
    )
    record_action_review_escalation_note.add_argument("--action-request-id", required=True)
    record_action_review_escalation_note.add_argument("--escalated-at", required=True)
    record_action_review_escalation_note.add_argument(
        "--escalated-by-identity",
        required=True,
    )
    record_action_review_escalation_note.add_argument("--escalated-to", required=True)
    record_action_review_escalation_note.add_argument("--note", required=True)
    create_reviewed_action_request = subparsers.add_parser(
        "create-reviewed-action-request",
        help="Create an approval-bound reviewed action request from cited advisory context.",
    )
    create_reviewed_action_request.add_argument("--family", required=True)
    create_reviewed_action_request.add_argument("--record-id", required=True)
    create_reviewed_action_request.add_argument("--requester-identity", required=True)
    create_reviewed_action_request.add_argument("--recipient-identity", required=True)
    create_reviewed_action_request.add_argument("--message-intent", required=True)
    create_reviewed_action_request.add_argument("--escalation-reason", required=True)
    create_reviewed_action_request.add_argument("--expires-at", required=True)
    create_reviewed_action_request.add_argument(
        "--action-request-id",
        help="Optional action request identifier to use instead of an auto-generated value.",
    )
    inspect_assistant_context = subparsers.add_parser(
        "inspect-assistant-context",
        help="Render a read-only analyst-assistant context view for one record.",
    )
    inspect_assistant_context.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for assistant context.",
    )
    inspect_assistant_context.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for assistant context.",
    )
    inspect_advisory_output = subparsers.add_parser(
        "inspect-advisory-output",
        help="Render the cited advisory-output contract for one reviewed record.",
    )
    inspect_advisory_output.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for advisory output.",
    )
    inspect_advisory_output.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for advisory output.",
    )
    render_recommendation_draft = subparsers.add_parser(
        "render-recommendation-draft",
        help="Render cited recommendation-draft output for one reviewed record.",
    )
    render_recommendation_draft.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to render for recommendation drafting.",
    )
    render_recommendation_draft.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to render for recommendation drafting.",
    )
    run_live_assistant_workflow = subparsers.add_parser(
        "run-live-assistant-workflow",
        help="Run one bounded reviewed live assistant workflow over reviewed records only.",
    )
    run_live_assistant_workflow.add_argument(
        "--workflow-task",
        required=True,
        choices=("case_summary", "queue_triage_summary"),
        help="Bounded live assistant workflow task to run.",
    )
    run_live_assistant_workflow.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to ground for the live assistant workflow.",
    )
    run_live_assistant_workflow.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to ground for the live assistant workflow.",
    )
    return parser


def run_command(
    parsed: argparse.Namespace,
    *,
    service: AegisOpsControlPlaneService,
    parser: argparse.ArgumentParser | None = None,
    read_json_file_fn: Callable[[str], dict[str, object]] | None = None,
) -> dict[str, object]:
    read_json_file_fn = read_json_file_fn or read_json_file
    command = parsed.command or "runtime"
    if command == "runtime":
        return service.describe_runtime().to_dict()
    if command == "inspect-records":
        try:
            return service.inspect_records(parsed.family).to_dict()
        except ValueError as exc:
            _usage_error(parser, str(exc))
    if command == "inspect-assistant-context":
        try:
            return service.inspect_assistant_context(
                parsed.family,
                parsed.record_id,
            ).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "inspect-case-detail":
        case_id = parsed.case_id.strip()
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return service.inspect_case_detail(case_id).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "promote-alert-to-case":
        alert_id = normalize_alert_id(parsed.alert_id)
        if not alert_id:
            _usage_error(parser, "alert_id must be a non-empty string")
        try:
            return json_ready(
                service.promote_alert_to_case(
                    alert_id,
                    case_id=normalize_optional_string(parsed.case_id),
                    case_lifecycle_state=parsed.case_lifecycle_state.strip(),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-case-observation":
        case_id = normalize_case_id(parsed.case_id)
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return json_ready(
                service.record_case_observation(
                    case_id=case_id,
                    author_identity=parsed.author_identity.strip(),
                    observed_at=parse_datetime_arg(parsed.observed_at, "observed_at"),
                    scope_statement=parsed.scope_statement.strip(),
                    supporting_evidence_ids=tuple(
                        evidence_id.strip()
                        for evidence_id in parsed.supporting_evidence_id
                    ),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-case-lead":
        case_id = normalize_case_id(parsed.case_id)
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return json_ready(
                service.record_case_lead(
                    case_id=case_id,
                    triage_owner=parsed.triage_owner.strip(),
                    triage_rationale=parsed.triage_rationale.strip(),
                    observation_id=normalize_optional_string(parsed.observation_id),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-case-recommendation":
        case_id = normalize_case_id(parsed.case_id)
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return json_ready(
                service.record_case_recommendation(
                    case_id=case_id,
                    review_owner=parsed.review_owner.strip(),
                    intended_outcome=parsed.intended_outcome.strip(),
                    lead_id=normalize_optional_string(parsed.lead_id),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-case-handoff":
        case_id = normalize_case_id(parsed.case_id)
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return json_ready(
                service.record_case_handoff(
                    case_id=case_id,
                    handoff_at=parse_datetime_arg(parsed.handoff_at, "handoff_at"),
                    handoff_owner=parsed.handoff_owner.strip(),
                    handoff_note=parsed.handoff_note.strip(),
                    follow_up_evidence_ids=tuple(
                        evidence_id.strip()
                        for evidence_id in parsed.follow_up_evidence_id
                    ),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-case-disposition":
        case_id = normalize_case_id(parsed.case_id)
        if not case_id:
            _usage_error(parser, "case_id must be a non-empty string")
        try:
            return json_ready(
                service.record_case_disposition(
                    case_id=case_id,
                    disposition=parsed.disposition.strip(),
                    rationale=parsed.rationale.strip(),
                    recorded_at=parse_datetime_arg(parsed.recorded_at, "recorded_at"),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-action-review-manual-fallback":
        action_request_id = parsed.action_request_id.strip()
        if not action_request_id:
            _usage_error(parser, "action_request_id must be a non-empty string")
        try:
            return json_ready(
                service.record_action_review_manual_fallback(
                    action_request_id=action_request_id,
                    fallback_at=parse_datetime_arg(parsed.fallback_at, "fallback_at"),
                    fallback_actor_identity=parsed.fallback_actor_identity.strip(),
                    authority_boundary=parsed.authority_boundary.strip(),
                    reason=parsed.reason.strip(),
                    action_taken=parsed.action_taken.strip(),
                    verification_evidence_ids=tuple(
                        evidence_id.strip()
                        for evidence_id in parsed.verification_evidence_id
                    ),
                    residual_uncertainty=normalize_optional_string(parsed.residual_uncertainty),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "record-action-review-escalation-note":
        action_request_id = parsed.action_request_id.strip()
        if not action_request_id:
            _usage_error(parser, "action_request_id must be a non-empty string")
        try:
            return json_ready(
                service.record_action_review_escalation_note(
                    action_request_id=action_request_id,
                    escalated_at=parse_datetime_arg(parsed.escalated_at, "escalated_at"),
                    escalated_by_identity=parsed.escalated_by_identity.strip(),
                    escalated_to=parsed.escalated_to.strip(),
                    note=parsed.note.strip(),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "create-reviewed-action-request":
        try:
            return json_ready(
                service.create_reviewed_action_request_from_advisory(
                    record_family=parsed.family.strip(),
                    record_id=parsed.record_id.strip(),
                    requester_identity=parsed.requester_identity.strip(),
                    recipient_identity=parsed.recipient_identity.strip(),
                    message_intent=parsed.message_intent.strip(),
                    escalation_reason=parsed.escalation_reason.strip(),
                    expires_at=parse_datetime_arg(parsed.expires_at, "expires_at"),
                    action_request_id=normalize_optional_string(parsed.action_request_id),
                )
            )
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "inspect-advisory-output":
        try:
            return service.inspect_advisory_output(
                parsed.family,
                parsed.record_id,
            ).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "render-recommendation-draft":
        try:
            return service.render_recommendation_draft(
                parsed.family,
                parsed.record_id,
            ).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "run-live-assistant-workflow":
        try:
            return service.run_live_assistant_workflow(
                workflow_task=parsed.workflow_task,
                record_family=parsed.family,
                record_id=parsed.record_id,
            ).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "inspect-reconciliation-status":
        return service.inspect_reconciliation_status().to_dict()
    if command == "startup-status":
        return service.describe_startup_status().to_dict()
    if command == "shutdown-status":
        return service.describe_shutdown_status().to_dict()
    if command == "backup-authoritative-record-chain":
        try:
            return service.export_authoritative_record_chain_backup()
        except ValueError as exc:
            _usage_error(parser, str(exc))
    if command == "restore-authoritative-record-chain":
        try:
            return service.restore_authoritative_record_chain_backup(
                read_json_file_fn(parsed.input)
            ).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "run-authoritative-restore-drill":
        try:
            return service.run_authoritative_restore_drill().to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    if command == "inspect-analyst-queue":
        return service.inspect_analyst_queue().to_dict()
    if command == "inspect-alert-detail":
        alert_id = normalize_alert_id(parsed.alert_id)
        if not alert_id:
            _usage_error(parser, "alert_id must be a non-empty string")
        try:
            return service.inspect_alert_detail(alert_id).to_dict()
        except (LookupError, ValueError) as exc:
            _usage_error(parser, str(exc))
    raise AssertionError(f"Unhandled command: {command}")


def _usage_error(
    parser: argparse.ArgumentParser | None,
    message: str,
) -> None:
    if parser is not None:
        parser.error(message)
    raise ValueError(message)
