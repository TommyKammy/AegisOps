begin;

alter table if exists aegisops_control.approval_decision_records
  add column if not exists decision_rationale text;

commit;
