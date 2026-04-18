alter table if exists aegisops_control.evidence_records
  add column if not exists provenance jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.evidence_records
  add column if not exists content jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.observation_records
  add column if not exists provenance jsonb not null default '{}'::jsonb;

alter table if exists aegisops_control.observation_records
  add column if not exists content jsonb not null default '{}'::jsonb;
