begin;

alter table if exists aegisops_control.alert_records
  add column if not exists coordination_reference_id text;

alter table if exists aegisops_control.alert_records
  add column if not exists coordination_target_type text;

alter table if exists aegisops_control.alert_records
  add column if not exists coordination_target_id text;

alter table if exists aegisops_control.alert_records
  add column if not exists ticket_reference_url text;

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_coordination_reference_fields_complete;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_coordination_reference_fields_complete check (
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
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_coordination_target_type_reviewed;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_coordination_target_type_reviewed check (
    coordination_target_type is null
    or coordination_target_type in ('glpi', 'zammad')
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_ticket_reference_url_https;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_ticket_reference_url_https check (
    ticket_reference_url is null
    or ticket_reference_url ~* '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_coordination_reference_id_bounded;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_coordination_reference_id_bounded check (
    coordination_reference_id is null
    or char_length(coordination_reference_id) <= 128
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_coordination_target_type_bounded;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_coordination_target_type_bounded check (
    coordination_target_type is null
    or char_length(coordination_target_type) <= 32
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_coordination_target_id_bounded;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_coordination_target_id_bounded check (
    coordination_target_id is null
    or char_length(coordination_target_id) <= 256
  );

alter table if exists aegisops_control.alert_records
  drop constraint if exists alert_records_ticket_reference_url_bounded;

alter table if exists aegisops_control.alert_records
  add constraint alert_records_ticket_reference_url_bounded check (
    ticket_reference_url is null
    or char_length(ticket_reference_url) <= 2048
  );

alter table if exists aegisops_control.case_records
  add column if not exists coordination_reference_id text;

alter table if exists aegisops_control.case_records
  add column if not exists coordination_target_type text;

alter table if exists aegisops_control.case_records
  add column if not exists coordination_target_id text;

alter table if exists aegisops_control.case_records
  add column if not exists ticket_reference_url text;

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_coordination_reference_fields_complete;

alter table if exists aegisops_control.case_records
  add constraint case_records_coordination_reference_fields_complete check (
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
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_coordination_target_type_reviewed;

alter table if exists aegisops_control.case_records
  add constraint case_records_coordination_target_type_reviewed check (
    coordination_target_type is null
    or coordination_target_type in ('glpi', 'zammad')
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_ticket_reference_url_https;

alter table if exists aegisops_control.case_records
  add constraint case_records_ticket_reference_url_https check (
    ticket_reference_url is null
    or ticket_reference_url ~* '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_coordination_reference_id_bounded;

alter table if exists aegisops_control.case_records
  add constraint case_records_coordination_reference_id_bounded check (
    coordination_reference_id is null
    or char_length(coordination_reference_id) <= 128
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_coordination_target_type_bounded;

alter table if exists aegisops_control.case_records
  add constraint case_records_coordination_target_type_bounded check (
    coordination_target_type is null
    or char_length(coordination_target_type) <= 32
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_coordination_target_id_bounded;

alter table if exists aegisops_control.case_records
  add constraint case_records_coordination_target_id_bounded check (
    coordination_target_id is null
    or char_length(coordination_target_id) <= 256
  );

alter table if exists aegisops_control.case_records
  drop constraint if exists case_records_ticket_reference_url_bounded;

alter table if exists aegisops_control.case_records
  add constraint case_records_ticket_reference_url_bounded check (
    ticket_reference_url is null
    or char_length(ticket_reference_url) <= 2048
  );

commit;
