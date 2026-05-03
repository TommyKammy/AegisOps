import type { GetListParams, RaRecord } from "react-admin";

export type OperatorResourceName =
  | "queue"
  | "alerts"
  | "cases"
  | "firstLoginChecklist"
  | "runtimeReadiness"
  | "reconciliations"
  | "todayView"
  | "businessHoursHandoff"
  | "advisoryOutput"
  | "actionReview";

export interface OperatorDataProviderConfig {
  fetchFn?: typeof fetch;
}

export interface OperatorRecordFamilyListResponse {
  records: unknown;
  total_records?: unknown;
}

export interface OperatorResourceBinding {
  detailPath?: string;
  detailQueryKey?: string;
  idField: string;
  listPath?: string;
  listSemantics?: "client";
  recordFamily?: string;
}

export interface StandardListReaderOptions {
  binding: OperatorResourceBinding;
  fetchFn: typeof fetch;
  params: GetListParams;
  resource: StandardOperatorResourceName;
}

export type StandardOperatorResourceName = Exclude<
  OperatorResourceName,
  "advisoryOutput" | "actionReview" | "businessHoursHandoff" | "todayView"
>;

export type OperatorRecord = RaRecord;
