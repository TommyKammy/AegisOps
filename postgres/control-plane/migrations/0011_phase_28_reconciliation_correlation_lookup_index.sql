begin;

create index if not exists reconciliation_records_correlation_alert_latest_idx
  on aegisops_control.reconciliation_records (
    correlation_key,
    compared_at desc,
    reconciliation_id desc
  )
  where alert_id is not null;

commit;
