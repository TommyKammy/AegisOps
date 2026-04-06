-- Control-plane schema v1 baseline migration.
begin;
create schema if not exists aegisops_control;

create table if not exists aegisops_control.alert_records (
  alert_id text primary key,
  finding_id text not null,
  analytic_signal_id text,
  case_id text,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (lifecycle_state in ('new','triaged','investigating','escalated_to_case','closed','reopened','superseded'))
);

create table if not exists aegisops_control.analytic_signal_records (
  analytic_signal_id text primary key,
  substrate_detection_record_id text,
  finding_id text,
  alert_ids text[] not null default '{}'::text[],
  case_ids text[] not null default '{}'::text[],
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
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (finding_id is not null or alert_id is not null),
  check (cardinality(evidence_ids) >= 1),
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
  payload_hash text not null,
  requested_at timestamptz not null,
  expires_at timestamptz,
  lifecycle_state text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (case_id is not null or alert_id is not null or finding_id is not null),
  check (lifecycle_state in ('draft','pending_approval','approved','rejected','expired','canceled','superseded','executing','completed','failed','unresolved'))
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

commit;
