begin;

create index if not exists ai_trace_records_latest_idx
  on aegisops_control.ai_trace_records (
    generated_at desc,
    ai_trace_id desc
  );

commit;
