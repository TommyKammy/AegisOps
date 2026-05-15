-- Phase 61 source-health dashboard records.
begin;

create table if not exists aegisops_control.source_health_records (
  source_health_id text primary key,
  source_family text not null,
  source_catalog_entry text not null,
  health_state text not null,
  reviewed_state text not null,
  reviewed_at timestamptz not null,
  observed_at timestamptz not null,
  detector_drift text not null,
  credential_posture text not null,
  evidence_references text[] not null default '{}'::text[],
  operator_visible_reason text not null,
  source_native_authority boolean not null default false,
  display_state_authority boolean not null default false,
  cache_sourced boolean not null default false,
  lifecycle_state text not null default 'reviewed',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (cardinality(evidence_references) >= 1),
  check (observed_at <= reviewed_at),
  check (source_native_authority = false),
  check (display_state_authority = false),
  check (cache_sourced = false),
  check (
    health_state in (
      'available',
      'degraded',
      'unavailable',
      'stale_source',
      'missing_agent',
      'parser_failure',
      'volume_anomaly',
      'credential_degraded',
      'detector_drift',
      'mismatched'
    )
  ),
  check (reviewed_state in ('reviewed', 'superseded', 'withdrawn')),
  check (reviewed_state = lifecycle_state),
  check (detector_drift in ('none', 'review_required', 'mismatched')),
  check (credential_posture in ('reviewed', 'degraded', 'unavailable'))
);

alter table aegisops_control.lifecycle_transition_records
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
      'source_health'
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
    )
  );

commit;
