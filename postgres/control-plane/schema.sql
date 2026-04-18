-- Control-plane schema v1 for the AegisOps-owned PostgreSQL boundary.
-- runtime_baseline: reviewed_v1
-- schema: aegisops_control
-- reconciliation boundary: control-plane records keep mismatch state explicit without collapsing into n8n-owned execution tables.
create schema if not exists aegisops_control;

create table if not exists aegisops_control.alert_records (
  alert_id text primary key,
  finding_id text not null,
  analytic_signal_id text,
  case_id text,
  coordination_reference_id text,
  coordination_target_type text,
  coordination_target_id text,
  ticket_reference_url text,
  reviewed_context jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint alert_records_coordination_reference_fields_complete check (
    (
      coordination_reference_id is null
      and coordination_target_type is null
      and coordination_target_id is null
      and ticket_reference_url is null
    ) or (
      nullif(btrim(coordination_reference_id), '') is not null
      and nullif(btrim(coordination_target_type), '') is not null
      and nullif(btrim(coordination_target_id), '') is not null
      and nullif(btrim(ticket_reference_url), '') is not null
    )
  ),
  constraint alert_records_coordination_target_type_reviewed check (
    coordination_target_type is null
    or coordination_target_type in ('glpi', 'zammad')
  ),
  constraint alert_records_ticket_reference_url_https check (
    ticket_reference_url is null
    or ticket_reference_url ~ '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'
  ),
  constraint alert_records_coordination_reference_id_bounded check (
    coordination_reference_id is null
    or char_length(coordination_reference_id) <= 128
  ),
  constraint alert_records_coordination_target_type_bounded check (
    coordination_target_type is null
    or char_length(coordination_target_type) <= 32
  ),
  constraint alert_records_coordination_target_id_bounded check (
    coordination_target_id is null
    or char_length(coordination_target_id) <= 256
  ),
  constraint alert_records_ticket_reference_url_bounded check (
    ticket_reference_url is null
    or char_length(ticket_reference_url) <= 2048
  ),
  check (lifecycle_state in ('new','triaged','investigating','escalated_to_case','closed','reopened','superseded'))
);

create table if not exists aegisops_control.analytic_signal_records (
  analytic_signal_id text primary key,
  substrate_detection_record_id text,
  finding_id text,
  alert_ids text[] not null default '{}'::text[],
  case_ids text[] not null default '{}'::text[],
  reviewed_context jsonb not null default '{}'::jsonb,
  correlation_key text not null,
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (
    nullif(btrim(substrate_detection_record_id), '') is not null
    or nullif(btrim(finding_id), '') is not null
  ),
  check (first_seen_at is null or last_seen_at is null or first_seen_at <= last_seen_at),
  check (lifecycle_state in ('active','superseded','withdrawn'))
);

create table if not exists aegisops_control.case_records (
  case_id text primary key,
  alert_id text,
  finding_id text,
  evidence_ids text[] not null,
  coordination_reference_id text,
  coordination_target_type text,
  coordination_target_id text,
  ticket_reference_url text,
  reviewed_context jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (finding_id is not null or alert_id is not null),
  check (cardinality(evidence_ids) >= 1),
  constraint case_records_coordination_reference_fields_complete check (
    (
      coordination_reference_id is null
      and coordination_target_type is null
      and coordination_target_id is null
      and ticket_reference_url is null
    ) or (
      nullif(btrim(coordination_reference_id), '') is not null
      and nullif(btrim(coordination_target_type), '') is not null
      and nullif(btrim(coordination_target_id), '') is not null
      and nullif(btrim(ticket_reference_url), '') is not null
    )
  ),
  constraint case_records_coordination_target_type_reviewed check (
    coordination_target_type is null
    or coordination_target_type in ('glpi', 'zammad')
  ),
  constraint case_records_ticket_reference_url_https check (
    ticket_reference_url is null
    or ticket_reference_url ~ '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'
  ),
  constraint case_records_coordination_reference_id_bounded check (
    coordination_reference_id is null
    or char_length(coordination_reference_id) <= 128
  ),
  constraint case_records_coordination_target_type_bounded check (
    coordination_target_type is null
    or char_length(coordination_target_type) <= 32
  ),
  constraint case_records_coordination_target_id_bounded check (
    coordination_target_id is null
    or char_length(coordination_target_id) <= 256
  ),
  constraint case_records_ticket_reference_url_bounded check (
    ticket_reference_url is null
    or char_length(ticket_reference_url) <= 2048
  ),
  check (lifecycle_state in ('open','investigating','pending_action','contained_pending_validation','closed','reopened','superseded'))
);

create table if not exists aegisops_control.evidence_records (
  evidence_id text primary key,
  source_record_id text not null,
  alert_id text,
  case_id text,
  source_system text not null,
  collector_identity text not null,
  acquired_at timestamptz not null,
  derivation_relationship text,
  provenance jsonb not null default '{}'::jsonb,
  content jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (alert_id is not null or case_id is not null),
  check (lifecycle_state in ('collected','validated','linked','superseded','withdrawn'))
);

create table if not exists aegisops_control.observation_records (
  observation_id text primary key,
  hunt_id text,
  hunt_run_id text,
  alert_id text,
  case_id text,
  supporting_evidence_ids text[] not null,
  author_identity text not null,
  observed_at timestamptz not null,
  scope_statement text not null,
  provenance jsonb not null default '{}'::jsonb,
  content jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (hunt_id is not null or hunt_run_id is not null or alert_id is not null or case_id is not null),
  check (cardinality(supporting_evidence_ids) >= 1),
  check (lifecycle_state in ('captured','confirmed','challenged','superseded','withdrawn'))
);

create table if not exists aegisops_control.lead_records (
  lead_id text primary key,
  observation_id text,
  finding_id text,
  hunt_run_id text,
  alert_id text,
  case_id text,
  triage_owner text not null,
  triage_rationale text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  lifecycle_state text not null,
  check (observation_id is not null or finding_id is not null or hunt_run_id is not null),
  check (lifecycle_state in ('open','triaged','promoted_to_alert','promoted_to_case','closed','superseded'))
);

create table if not exists aegisops_control.recommendation_records (
  recommendation_id text primary key,
  lead_id text,
  hunt_run_id text,
  alert_id text,
  case_id text,
  ai_trace_id text,
  review_owner text not null,
  intended_outcome text not null,
  reviewed_context jsonb not null default '{}'::jsonb,
  assistant_advisory_draft jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  lifecycle_state text not null,
  check (lead_id is not null or hunt_run_id is not null or alert_id is not null or case_id is not null),
  check (lifecycle_state in ('proposed','under_review','accepted','rejected','materialized','superseded','withdrawn'))
);

create table if not exists aegisops_control.approval_decision_records (
  approval_decision_id text primary key,
  action_request_id text not null,
  approver_identities text[] not null,
  target_snapshot jsonb not null,
  payload_hash text not null,
  decided_at timestamptz,
  decision_rationale text,
  approved_expires_at timestamptz,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (cardinality(approver_identities) >= 1),
  check (lifecycle_state in ('pending','approved','rejected','expired','canceled','superseded'))
);

create table if not exists aegisops_control.action_request_records (
  action_request_id text primary key,
  approval_decision_id text,
  case_id text,
  alert_id text,
  finding_id text,
  idempotency_key text not null,
  target_scope jsonb not null,
  requester_identity text,
  requested_payload jsonb not null,
  policy_basis jsonb not null default '{}'::jsonb,
  policy_evaluation jsonb not null default '{}'::jsonb,
  payload_hash text not null,
  requested_at timestamptz not null,
  expires_at timestamptz,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (case_id is not null or alert_id is not null or finding_id is not null),
  check (lifecycle_state in ('draft','pending_approval','approved','rejected','expired','canceled','superseded','executing','completed','failed','unresolved'))
);

create table if not exists aegisops_control.action_execution_records (
  action_execution_id text primary key,
  action_request_id text not null,
  approval_decision_id text not null,
  delegation_id text not null,
  execution_surface_type text not null,
  execution_surface_id text not null,
  execution_run_id text not null,
  idempotency_key text not null,
  target_scope jsonb not null,
  approved_payload jsonb not null,
  payload_hash text not null,
  delegated_at timestamptz not null,
  expires_at timestamptz,
  provenance jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint action_execution_records_identifiers_non_blank check (
    nullif(btrim(action_execution_id), '') is not null
    and nullif(btrim(action_request_id), '') is not null
    and nullif(btrim(approval_decision_id), '') is not null
    and nullif(btrim(delegation_id), '') is not null
    and nullif(btrim(execution_surface_type), '') is not null
    and nullif(btrim(execution_surface_id), '') is not null
    and nullif(btrim(execution_run_id), '') is not null
    and nullif(btrim(idempotency_key), '') is not null
    and nullif(btrim(payload_hash), '') is not null
  ),
  constraint action_execution_records_expiry_not_before_delegation check (
    expires_at is null or expires_at >= delegated_at
  ),
  check (lifecycle_state in ('queued','running','succeeded','failed','canceled','superseded'))
);

create table if not exists aegisops_control.hunt_records (
  hunt_id text primary key,
  hypothesis_statement text not null,
  hypothesis_version text not null,
  owner_identity text not null,
  scope_boundary text not null,
  opened_at timestamptz not null,
  alert_id text,
  case_id text,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (lifecycle_state in ('draft','active','on_hold','concluded','closed','superseded'))
);

create table if not exists aegisops_control.hunt_run_records (
  hunt_run_id text primary key,
  hunt_id text not null,
  scope_snapshot jsonb not null,
  execution_plan_reference text not null,
  output_linkage jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (lifecycle_state in ('planned','running','completed','canceled','superseded','unresolved'))
);

create table if not exists aegisops_control.ai_trace_records (
  ai_trace_id text primary key,
  subject_linkage jsonb not null,
  model_identity text not null,
  prompt_version text not null,
  generated_at timestamptz not null,
  material_input_refs text[] not null default '{}'::text[],
  reviewer_identity text not null,
  assistant_advisory_draft jsonb not null default '{}'::jsonb,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (lifecycle_state in ('generated','under_review','accepted_for_reference','rejected_for_reference','superseded','withdrawn'))
);

create table if not exists aegisops_control.reconciliation_records (
  reconciliation_id text primary key,
  subject_linkage jsonb not null,
  alert_id text,
  finding_id text,
  analytic_signal_id text,
  execution_run_id text,
  linked_execution_run_ids text[] not null default '{}'::text[],
  correlation_key text not null,
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  ingest_disposition text not null default 'matched',
  mismatch_summary text not null,
  compared_at timestamptz not null,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (finding_id is not null or analytic_signal_id is not null or execution_run_id is not null),
  check (first_seen_at is null or last_seen_at is null or first_seen_at <= last_seen_at),
  check (
    ingest_disposition in (
      'created',
      'updated',
      'deduplicated',
      'restated',
      'matched',
      'missing',
      'duplicate',
      'mismatch',
      'stale'
    )
  ),
  check (lifecycle_state in ('pending','matched','mismatched','stale','resolved','superseded'))
);

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
  ),
  constraint lifecycle_transition_records_state_matches_subject_family check (
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
  ),
  constraint lifecycle_transition_records_previous_state_matches_subject_family check (
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
    )
  )
);

create index if not exists lifecycle_transition_records_subject_latest_idx
  on aegisops_control.lifecycle_transition_records (
    subject_record_family,
    subject_record_id,
    transitioned_at desc,
    transition_id desc
  );
