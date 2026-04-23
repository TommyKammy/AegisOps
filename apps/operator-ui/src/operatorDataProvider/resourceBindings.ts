import type { OperatorResourceBinding, StandardOperatorResourceName } from "./types";

export const JSON_HEADERS = {
  Accept: "application/json",
};

export const RESOURCE_BINDINGS: Record<
  StandardOperatorResourceName,
  OperatorResourceBinding
> = {
  alerts: {
    detailPath: "/inspect-alert-detail",
    detailQueryKey: "alert_id",
    idField: "alert_id",
    listPath: "/inspect-records",
    listSemantics: "client",
    recordFamily: "alert",
  },
  cases: {
    detailPath: "/inspect-case-detail",
    detailQueryKey: "case_id",
    idField: "case_id",
    listPath: "/inspect-records",
    listSemantics: "client",
    recordFamily: "case",
  },
  queue: {
    idField: "alert_id",
    listPath: "/inspect-analyst-queue",
    listSemantics: "client",
  },
  runtimeReadiness: {
    detailPath: "/diagnostics/readiness",
    idField: "status",
    listPath: "/diagnostics/readiness",
    listSemantics: "client",
  },
  reconciliations: {
    detailPath: "/inspect-reconciliation-status",
    idField: "reconciliation_id",
    listPath: "/inspect-reconciliation-status",
    listSemantics: "client",
  },
};

export function isStandardResource(
  resource: string,
): resource is StandardOperatorResourceName {
  return Object.prototype.hasOwnProperty.call(RESOURCE_BINDINGS, resource);
}
