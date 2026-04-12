-- Phase 20 forward migration for approval-bound action request payload grounding.
begin;

alter table if exists aegisops_control.action_request_records
  add column if not exists requester_identity text;

alter table if exists aegisops_control.action_request_records
  add column if not exists requested_payload jsonb not null default '{}'::jsonb;

commit;
