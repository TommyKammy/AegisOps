begin;

create unique index if not exists action_request_records_idempotency_key_key
  on aegisops_control.action_request_records (idempotency_key);

commit;
