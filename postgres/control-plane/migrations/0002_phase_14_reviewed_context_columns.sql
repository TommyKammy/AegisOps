-- Phase 14 forward migration for reviewed_context on identity-rich reviewed record families.
begin;

alter table if exists aegisops_control.alert_records
  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.analytic_signal_records
  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.case_records
  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.recommendation_records
  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;

commit;
