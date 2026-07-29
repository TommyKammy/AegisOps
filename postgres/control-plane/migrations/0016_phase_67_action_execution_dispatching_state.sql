begin;

alter table aegisops_control.action_execution_records
  drop constraint if exists action_execution_records_lifecycle_state_check;

alter table aegisops_control.action_execution_records
  add constraint action_execution_records_lifecycle_state_check
  check (
    lifecycle_state in (
      'dispatching',
      'queued',
      'running',
      'succeeded',
      'failed',
      'canceled',
      'superseded'
    )
  );

commit;
