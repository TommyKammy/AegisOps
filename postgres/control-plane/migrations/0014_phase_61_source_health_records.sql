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

commit;
