begin;

with duplicate_action_requests as (
  select
    ctid,
    row_number() over (
      partition by idempotency_key
      order by requested_at asc, action_request_id asc
    ) as duplicate_rank
  from aegisops_control.action_request_records
  where idempotency_key is not null
)
delete from aegisops_control.action_request_records as action_request
using duplicate_action_requests
where action_request.ctid = duplicate_action_requests.ctid
  and duplicate_action_requests.duplicate_rank > 1;

create unique index if not exists action_request_records_idempotency_key_key
  on aegisops_control.action_request_records (idempotency_key);

commit;
