-- Phase 64 known limitation ownership records.
begin;

create table if not exists aegisops_control.known_limitation_ownership_records (
  limitation_id text primary key,
  title text not null,
  severity text not null,
  affected_surface text not null,
  owner text not null,
  mitigation text not null,
  evidence_references text[] not null default '{}'::text[],
  review_state text not null,
  review_cadence text,
  due_date text,
  accepted_risk_posture text not null,
  phase66_handoff_posture text not null,
  authority_boundary text not null,
  readiness_claim text,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (cardinality(evidence_references) >= 1),
  check (
    nullif(btrim(review_cadence), '') is not null
    or nullif(btrim(due_date), '') is not null
  ),
  check (severity in ('low', 'medium', 'material', 'high', 'blocking')),
  check (
    review_state in (
      'identified',
      'under_review',
      'accepted_risk',
      'mitigation_planned',
      'mitigation_in_progress',
      'closed'
    )
  ),
  check (
    phase66_handoff_posture in (
      'not_ready_for_handoff',
      'handoff_required',
      'handoff_ready_as_subordinate_evidence',
      'blocked_until_mitigated'
    )
  ),
  check (authority_boundary = 'reviewed_evidence_input_only'),
  check (lifecycle_state = review_state)
);

alter table aegisops_control.lifecycle_transition_records
  drop constraint if exists lifecycle_transition_records_subject_record_family_check,
  drop constraint if exists lifecycle_transition_records_lifecycle_state_check,
  drop constraint if exists lifecycle_transition_records_previous_lifecycle_state_check,
  drop constraint if exists lifecycle_transition_records_lifecycle_state_known,
  drop constraint if exists lifecycle_transition_records_previous_lifecycle_state_known,
  drop constraint if exists lifecycle_transition_records_subject_family_matches,
  drop constraint if exists lifecycle_transition_records_state_matches_subject_family,
  drop constraint if exists lifecycle_transition_records_previous_state_matches_subject_family,
  add constraint lifecycle_transition_records_subject_family_matches check (
    subject_record_family in (
      'alert',
      'analytic_signal',
      'case',
      'evidence',
      'observation',
      'lead',
      'recommendation',
      'approval_decision',
      'action_request',
      'action_execution',
      'hunt',
      'hunt_run',
      'ai_trace',
      'reconciliation',
      'detector_lifecycle',
      'false_positive_review',
      'suppression_proposal',
      'source_health',
      'known_limitation_ownership'
    )
  ),
  add constraint lifecycle_transition_records_lifecycle_state_known_values check (
    lifecycle_state in (
      'new',
      'triaged',
      'investigating',
      'escalated_to_case',
      'closed',
      'reopened',
      'superseded',
      'active',
      'withdrawn',
      'open',
      'pending_action',
      'contained_pending_validation',
      'collected',
      'validated',
      'linked',
      'captured',
      'confirmed',
      'challenged',
      'promoted_to_alert',
      'promoted_to_case',
      'proposed',
      'under_review',
      'accepted',
      'rejected',
      'materialized',
      'pending',
      'approved',
      'expired',
      'canceled',
      'draft',
      'pending_approval',
      'executing',
      'completed',
      'failed',
      'unresolved',
      'dispatching',
      'queued',
      'running',
      'succeeded',
      'on_hold',
      'concluded',
      'planned',
      'generated',
      'accepted_for_reference',
      'rejected_for_reference',
      'matched',
      'mismatched',
      'stale',
      'resolved',
      'candidate',
      'staging',
      'disabled',
      'rollback',
      'review-overdue',
      'reviewed',
      'disputed',
      'identified',
      'accepted_risk',
      'mitigation_planned',
      'mitigation_in_progress'
    )
  ),
  add constraint lifecycle_transition_records_previous_lifecycle_state_known_values check (
    previous_lifecycle_state is null or previous_lifecycle_state in (
      'new',
      'triaged',
      'investigating',
      'escalated_to_case',
      'closed',
      'reopened',
      'superseded',
      'active',
      'withdrawn',
      'open',
      'pending_action',
      'contained_pending_validation',
      'collected',
      'validated',
      'linked',
      'captured',
      'confirmed',
      'challenged',
      'promoted_to_alert',
      'promoted_to_case',
      'proposed',
      'under_review',
      'accepted',
      'rejected',
      'materialized',
      'pending',
      'approved',
      'expired',
      'canceled',
      'draft',
      'pending_approval',
      'executing',
      'completed',
      'failed',
      'unresolved',
      'dispatching',
      'queued',
      'running',
      'succeeded',
      'on_hold',
      'concluded',
      'planned',
      'generated',
      'accepted_for_reference',
      'rejected_for_reference',
      'matched',
      'mismatched',
      'stale',
      'resolved',
      'candidate',
      'staging',
      'disabled',
      'rollback',
      'review-overdue',
      'reviewed',
      'disputed',
      'identified',
      'accepted_risk',
      'mitigation_planned',
      'mitigation_in_progress'
    )
  ),
  add constraint lifecycle_transition_records_state_matches_subject_family check (
    (subject_record_family = 'alert' and lifecycle_state in (
      'new',
      'triaged',
      'investigating',
      'escalated_to_case',
      'closed',
      'reopened',
      'superseded'
    ))
    or (subject_record_family = 'analytic_signal' and lifecycle_state in (
      'active',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'case' and lifecycle_state in (
      'open',
      'investigating',
      'pending_action',
      'contained_pending_validation',
      'closed',
      'reopened',
      'superseded'
    ))
    or (subject_record_family = 'evidence' and lifecycle_state in (
      'collected',
      'validated',
      'linked',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'observation' and lifecycle_state in (
      'captured',
      'confirmed',
      'challenged',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'lead' and lifecycle_state in (
      'open',
      'triaged',
      'promoted_to_alert',
      'promoted_to_case',
      'closed',
      'superseded'
    ))
    or (subject_record_family = 'recommendation' and lifecycle_state in (
      'proposed',
      'under_review',
      'accepted',
      'rejected',
      'materialized',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'approval_decision' and lifecycle_state in (
      'pending',
      'approved',
      'rejected',
      'expired',
      'canceled',
      'superseded'
    ))
    or (subject_record_family = 'action_request' and lifecycle_state in (
      'draft',
      'pending_approval',
      'approved',
      'rejected',
      'expired',
      'canceled',
      'superseded',
      'executing',
      'completed',
      'failed',
      'unresolved'
    ))
    or (subject_record_family = 'action_execution' and lifecycle_state in (
      'dispatching',
      'queued',
      'running',
      'succeeded',
      'failed',
      'canceled',
      'superseded'
    ))
    or (subject_record_family = 'hunt' and lifecycle_state in (
      'draft',
      'active',
      'on_hold',
      'concluded',
      'closed',
      'superseded'
    ))
    or (subject_record_family = 'hunt_run' and lifecycle_state in (
      'planned',
      'running',
      'completed',
      'canceled',
      'superseded',
      'unresolved'
    ))
    or (subject_record_family = 'ai_trace' and lifecycle_state in (
      'generated',
      'under_review',
      'accepted_for_reference',
      'rejected_for_reference',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'reconciliation' and lifecycle_state in (
      'pending',
      'matched',
      'mismatched',
      'stale',
      'resolved',
      'superseded'
    ))
    or (subject_record_family = 'detector_lifecycle' and lifecycle_state in (
      'candidate',
      'staging',
      'active',
      'disabled',
      'rollback',
      'review-overdue'
    ))
    or (subject_record_family = 'false_positive_review' and lifecycle_state in (
      'reviewed',
      'disputed',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'suppression_proposal' and lifecycle_state in (
      'proposed',
      'under_review',
      'rejected',
      'withdrawn',
      'expired',
      'superseded'
    ))
    or (subject_record_family = 'source_health' and lifecycle_state in (
      'reviewed',
      'superseded',
      'withdrawn'
    ))
    or (subject_record_family = 'known_limitation_ownership' and lifecycle_state in (
      'identified',
      'under_review',
      'accepted_risk',
      'mitigation_planned',
      'mitigation_in_progress',
      'closed'
    ))
  ),
  add constraint lifecycle_transition_records_previous_state_matches_subject_family check (
    previous_lifecycle_state is null or (
      (subject_record_family = 'alert' and previous_lifecycle_state in (
        'new',
        'triaged',
        'investigating',
        'escalated_to_case',
        'closed',
        'reopened',
        'superseded'
      ))
      or (subject_record_family = 'analytic_signal' and previous_lifecycle_state in (
        'active',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'case' and previous_lifecycle_state in (
        'open',
        'investigating',
        'pending_action',
        'contained_pending_validation',
        'closed',
        'reopened',
        'superseded'
      ))
      or (subject_record_family = 'evidence' and previous_lifecycle_state in (
        'collected',
        'validated',
        'linked',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'observation' and previous_lifecycle_state in (
        'captured',
        'confirmed',
        'challenged',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'lead' and previous_lifecycle_state in (
        'open',
        'triaged',
        'promoted_to_alert',
        'promoted_to_case',
        'closed',
        'superseded'
      ))
      or (subject_record_family = 'recommendation' and previous_lifecycle_state in (
        'proposed',
        'under_review',
        'accepted',
        'rejected',
        'materialized',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'approval_decision' and previous_lifecycle_state in (
        'pending',
        'approved',
        'rejected',
        'expired',
        'canceled',
        'superseded'
      ))
      or (subject_record_family = 'action_request' and previous_lifecycle_state in (
        'draft',
        'pending_approval',
        'approved',
        'rejected',
        'expired',
        'canceled',
        'superseded',
        'executing',
        'completed',
        'failed',
        'unresolved'
      ))
      or (subject_record_family = 'action_execution' and previous_lifecycle_state in (
        'dispatching',
        'queued',
        'running',
        'succeeded',
        'failed',
        'canceled',
        'superseded'
      ))
      or (subject_record_family = 'hunt' and previous_lifecycle_state in (
        'draft',
        'active',
        'on_hold',
        'concluded',
        'closed',
        'superseded'
      ))
      or (subject_record_family = 'hunt_run' and previous_lifecycle_state in (
        'planned',
        'running',
        'completed',
        'canceled',
        'superseded',
        'unresolved'
      ))
      or (subject_record_family = 'ai_trace' and previous_lifecycle_state in (
        'generated',
        'under_review',
        'accepted_for_reference',
        'rejected_for_reference',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'reconciliation' and previous_lifecycle_state in (
        'pending',
        'matched',
        'mismatched',
        'stale',
        'resolved',
        'superseded'
      ))
      or (subject_record_family = 'detector_lifecycle' and previous_lifecycle_state in (
        'candidate',
        'staging',
        'active',
        'disabled',
        'rollback',
        'review-overdue'
      ))
      or (subject_record_family = 'false_positive_review' and previous_lifecycle_state in (
        'reviewed',
        'disputed',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'suppression_proposal' and previous_lifecycle_state in (
        'proposed',
        'under_review',
        'rejected',
        'withdrawn',
        'expired',
        'superseded'
      ))
      or (subject_record_family = 'source_health' and previous_lifecycle_state in (
        'reviewed',
        'superseded',
        'withdrawn'
      ))
      or (subject_record_family = 'known_limitation_ownership' and previous_lifecycle_state in (
        'identified',
        'under_review',
        'accepted_risk',
        'mitigation_planned',
        'mitigation_in_progress',
        'closed'
      ))
    )
  );

commit;
