-- Phase 15 forward migration for assistant advisory draft anchoring on review records.
begin;

alter table if exists aegisops_control.recommendation_records
  add column if not exists assistant_advisory_draft jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.ai_trace_records
  add column if not exists assistant_advisory_draft jsonb not null default '{}'::jsonb;

commit;
