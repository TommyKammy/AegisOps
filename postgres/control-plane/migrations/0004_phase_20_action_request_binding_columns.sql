-- Phase 20 forward migration for approval-bound action request payload grounding.
begin;

alter table if exists aegisops_control.action_request_records
  add column if not exists requester_identity text;

alter table if exists aegisops_control.action_request_records
  add column if not exists requested_payload jsonb not null default '{}'::jsonb;

update aegisops_control.action_request_records
set requested_payload = '{}'::jsonb
where requested_payload is null;

alter table if exists aegisops_control.action_request_records
  alter column requested_payload drop default;

commit;
