begin;

create index if not exists lifecycle_transition_records_subject_latest_idx
  on aegisops_control.lifecycle_transition_records (
    subject_record_family,
    subject_record_id,
    transitioned_at desc,
    transition_id desc
  );

commit;
