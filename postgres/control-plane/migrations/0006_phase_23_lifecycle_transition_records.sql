begin;

create table if not exists aegisops_control.lifecycle_transition_records (
  transition_id text primary key,
  subject_record_family text not null,
  subject_record_id text not null,
  previous_lifecycle_state text,
  lifecycle_state text not null,
  transitioned_at timestamptz not null,
  attribution jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  check (
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
      'reconciliation'
    )
  ),
  check (
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
      'resolved'
    )
  ),
  check (
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
      'resolved'
    )
  )
);

with baseline_transitions as (
  select
    'analytic_signal'::text as subject_record_family,
    analytic_signal_id as subject_record_id,
    lifecycle_state,
    coalesce(first_seen_at, last_seen_at, created_at, updated_at) as transitioned_at,
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    ) as attribution
  from aegisops_control.analytic_signal_records

  union all

  select
    'alert'::text,
    alert_id,
    lifecycle_state,
    coalesce(
      case
        when nullif(btrim(reviewed_context -> 'triage' ->> 'recorded_at'), '') ~* '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ t][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(z|[+-][0-9]{2}:[0-9]{2})$'
        then (reviewed_context -> 'triage' ->> 'recorded_at')::timestamptz
      end,
      created_at,
      updated_at
    ),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.alert_records

  union all

  select
    'evidence'::text,
    evidence_id,
    lifecycle_state,
    coalesce(acquired_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.evidence_records

  union all

  select
    'observation'::text,
    observation_id,
    lifecycle_state,
    coalesce(observed_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array(author_identity)
    )
  from aegisops_control.observation_records

  union all

  select
    'lead'::text,
    lead_id,
    lifecycle_state,
    coalesce(created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array(triage_owner)
    )
  from aegisops_control.lead_records

  union all

  select
    'case'::text,
    case_id,
    lifecycle_state,
    coalesce(
      case
        when nullif(btrim(reviewed_context -> 'triage' ->> 'recorded_at'), '') ~* '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ t][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(z|[+-][0-9]{2}:[0-9]{2})$'
        then (reviewed_context -> 'triage' ->> 'recorded_at')::timestamptz
      end,
      created_at,
      updated_at
    ),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.case_records

  union all

  select
    'recommendation'::text,
    recommendation_id,
    lifecycle_state,
    coalesce(created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      case
        when nullif(btrim(review_owner), '') is null then jsonb_build_array()
        else jsonb_build_array(review_owner)
      end
    )
  from aegisops_control.recommendation_records

  union all

  select
    'approval_decision'::text,
    approval_decision_id,
    lifecycle_state,
    coalesce(decided_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      to_jsonb(approver_identities)
    )
  from aegisops_control.approval_decision_records

  union all

  select
    'action_request'::text,
    action_request_id,
    lifecycle_state,
    coalesce(requested_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      case
        when nullif(btrim(requester_identity), '') is null then jsonb_build_array()
        else jsonb_build_array(requester_identity)
      end
    )
  from aegisops_control.action_request_records

  union all

  select
    'action_execution'::text,
    action_execution_id,
    lifecycle_state,
    coalesce(delegated_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.action_execution_records

  union all

  select
    'hunt'::text,
    hunt_id,
    lifecycle_state,
    coalesce(opened_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array(owner_identity)
    )
  from aegisops_control.hunt_records

  union all

  select
    'hunt_run'::text,
    hunt_run_id,
    lifecycle_state,
    coalesce(started_at, completed_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.hunt_run_records

  union all

  select
    'ai_trace'::text,
    ai_trace_id,
    lifecycle_state,
    coalesce(generated_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array(reviewer_identity)
    )
  from aegisops_control.ai_trace_records

  union all

  select
    'reconciliation'::text,
    reconciliation_id,
    lifecycle_state,
    coalesce(first_seen_at, last_seen_at, compared_at, created_at, updated_at),
    jsonb_build_object(
      'source',
      'phase23-migration-backfill',
      'actor_identities',
      jsonb_build_array()
    )
  from aegisops_control.reconciliation_records
)
insert into aegisops_control.lifecycle_transition_records (
  transition_id,
  subject_record_family,
  subject_record_id,
  previous_lifecycle_state,
  lifecycle_state,
  transitioned_at,
  attribution
)
select
  concat(
    to_char(
      baseline_transitions.transitioned_at at time zone 'utc',
      'YYYYMMDD"T"HH24MISS.US"Z"'
    ),
    ':phase23-backfill:',
    baseline_transitions.subject_record_family,
    ':',
    baseline_transitions.subject_record_id
  ),
  baseline_transitions.subject_record_family,
  baseline_transitions.subject_record_id,
  null,
  baseline_transitions.lifecycle_state,
  baseline_transitions.transitioned_at,
  baseline_transitions.attribution
from baseline_transitions
left join aegisops_control.lifecycle_transition_records as existing
  on existing.subject_record_family = baseline_transitions.subject_record_family
  and existing.subject_record_id = baseline_transitions.subject_record_id
where existing.transition_id is null
on conflict (transition_id) do nothing;

commit;
