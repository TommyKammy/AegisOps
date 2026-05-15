-- Phase 61 forward migration for detector lifecycle records and transition contracts.
begin;

create table if not exists aegisops_control.detector_lifecycle_records (
  detector_lifecycle_id text primary key,
  owner text not null,
  source_family text not null,
  source_catalog_entry text not null,
  detector_identifier text not null,
  expected_signal_posture text not null,
  review_cadence text not null,
  rollback_owner text not null,
  disable_owner text not null,
  lifecycle_audit_references text[] not null default '{}'::text[],
  lifecycle_state text not null,
  disabled_reason text,
  rollback_reason text,
  review_overdue_reason text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (cardinality(lifecycle_audit_references) >= 1),
  check (
    lifecycle_state in (
      'candidate',
      'staging',
      'active',
      'disabled',
      'rollback',
      'review-overdue'
    )
  )
);

create table if not exists aegisops_control.false_positive_review_records (
  false_positive_review_id text primary key,
  detector_lifecycle_id text not null,
  source_family text not null,
  source_catalog_entry text not null,
  alert_id text,
  case_id text,
  evidence_ids text[] not null default '{}'::text[],
  owner text not null,
  disposition text not null,
  disposition_rationale text not null,
  dispute_state text not null,
  recurrence_posture text not null,
  review_evidence_references text[] not null default '{}'::text[],
  source_signal_handling text not null,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (alert_id is not null or case_id is not null or cardinality(evidence_ids) >= 1),
  check (cardinality(review_evidence_references) >= 1),
  check (
    disposition in (
      'benign_activity',
      'expected_activity',
      'duplicate_signal',
      'needs_detector_tuning',
      'recurring_benign_activity'
    )
  ),
  check (dispute_state in ('undisputed', 'disputed', 'resolved')),
  check (
    recurrence_posture in (
      'single_reviewed_instance',
      'recurring_reviewed_pattern',
      'recurrence_under_review'
    )
  ),
  check (
    source_signal_handling in (
      'preserve_source_signal',
      'preserve_and_escalate_for_tuning'
    )
  ),
  check (lifecycle_state in ('reviewed', 'disputed', 'superseded', 'withdrawn'))
);

create table if not exists aegisops_control.suppression_proposal_records (
  suppression_proposal_id text primary key,
  detector_lifecycle_id text not null,
  source_family text not null,
  source_catalog_entry text not null,
  alert_id text,
  case_id text,
  evidence_ids text[] not null default '{}'::text[],
  owner text not null,
  rationale text not null,
  citation_references text[] not null default '{}'::text[],
  expires_at timestamptz not null,
  review_cadence text not null,
  expected_signal_impact text not null,
  scope text not null,
  source_signal_handling text not null,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (alert_id is not null or case_id is not null or cardinality(evidence_ids) >= 1),
  check (cardinality(citation_references) >= 1),
  check (
    scope in (
      'detector_case_context',
      'detector_alert_context',
      'detector_evidence_context',
      'reviewed_recurring_pattern'
    )
  ),
  check (
    source_signal_handling in (
      'preserve_source_signal',
      'preserve_and_escalate_for_review'
    )
  ),
  check (
    lifecycle_state in (
      'proposed',
      'under_review',
      'rejected',
      'withdrawn',
      'expired',
      'superseded'
    )
  )
);

do $$
declare
  constraint_name text;
begin
  for constraint_name in (
    select conname
    from pg_constraint
    where conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
      and contype = 'c'
  )
  loop
    execute format(
      'alter table aegisops_control.lifecycle_transition_records drop constraint %I',
      constraint_name
    );
  end loop;

  alter table aegisops_control.lifecycle_transition_records
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
        'suppression_proposal'
      )
    ),
    add constraint lifecycle_transition_records_lifecycle_state_known check (
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
        'disputed'
      )
    ),
    add constraint lifecycle_transition_records_previous_lifecycle_state_known check (
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
        'active',
        'disabled',
        'rollback',
        'review-overdue',
        'reviewed',
        'disputed'
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
      )
    );
end $$;

commit;
