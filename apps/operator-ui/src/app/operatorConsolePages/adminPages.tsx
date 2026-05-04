import {
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { RBAC_ROLE_MATRIX, type RbacRoleId } from "../../auth/roleMatrix";

const ADMIN_ROLE_IDS: RbacRoleId[] = [
  "platform_admin",
  "analyst",
  "approver",
  "read_only_auditor",
  "support_operator",
  "external_collaborator",
];

const ADMIN_USERS = [
  {
    email: "platform.admin@example.com",
    role: "platform_admin",
    status: "Reviewed admin policy",
  },
  {
    email: "analyst@example.com",
    role: "analyst",
    status: "Reviewed operator policy",
  },
  {
    email: "approver@example.com",
    role: "approver",
    status: "Reviewed approval policy",
  },
] as const;

const SOURCE_PROFILE_STATES = [
  {
    label: "Create: reviewed source profile draft",
    posture:
      "New profile requests stay blocked until source family, custody, parser, provenance, and admission boundaries are reviewed.",
  },
  {
    label: "Update: reviewed posture change",
    posture:
      "Version, intake, credential, and source-health posture changes require explicit reviewed evidence and audit linkage.",
  },
  {
    label: "Disable: source admission blocked",
    posture:
      "Disabled profiles block future source admission without rewriting historical alerts, cases, evidence, or reconciliation records.",
  },
  {
    label: "Degraded: visible subordinate context",
    posture:
      "Degraded posture stays visible to operators as source-health context only and cannot advance workflow state.",
  },
] as const;

const SOURCE_PROFILE_AUDIT_TRAIL = [
  "Created by reviewed platform_admin session",
  "Changed fields and reason captured",
  "Disable or degraded transition records source admission impact",
  "Backend record-chain reread required before workflow use",
] as const;

const FUTURE_SOURCE_POSTURE = [
  "Explicit reviewed source-family identifier",
  "Parser and provenance evidence present",
  "Credential custody reference reviewed",
  "No source profile state promoted to record-chain truth",
] as const;

const ACTION_POLICY_POSTURES = [
  {
    family: "Read",
    posture: "Allowed by default",
    description:
      "Eligible for policy-authorized enrichment only when request context and execution logging stay complete.",
  },
  {
    family: "Notify",
    posture: "Allowed by default",
    description:
      "Eligible for reviewed notification posture when recipient, message intent, and escalation path are explicit.",
  },
  {
    family: "Soft Write",
    posture: "Degraded until reviewed",
    description:
      "Coordination writes stay disabled or degraded until the exact reversible action pattern and evidence path are reviewed.",
  },
] as const;

const DISABLED_ACTION_POLICY_POSTURES = [
  {
    family: "Controlled",
    posture: "Disabled by default",
  },
  {
    family: "Hard Write",
    posture: "Disabled by default",
  },
] as const;

const ACTION_POLICY_AUDIT_TRAIL = [
  "Policy posture change reason captured",
  "Changed by reviewed platform_admin session",
  "Default enablement decision and effective state recorded",
  "Backend authorization reread required before action use",
] as const;

const RETENTION_RECORD_FAMILIES = [
  {
    family: "Alerts",
    posture: "Preserve authoritative detection linkage",
  },
  {
    family: "Cases",
    posture: "Preserve workflow lifecycle and closeout truth",
  },
  {
    family: "Evidence",
    posture: "Preserve custody, provenance, and subordinate context",
  },
  {
    family: "AI traces",
    posture: "Preserve advisory-only trace boundaries",
  },
  {
    family: "Audit exports",
    posture: "Preserve export custody and audit reconstruction",
  },
  {
    family: "Execution receipts",
    posture: "Preserve execution outcome and receipt lineage",
  },
  {
    family: "Reconciliations",
    posture: "Preserve mismatch and terminal reconciliation truth",
  },
] as const;

const RETENTION_STATE_POSTURES = [
  {
    state: "Locked",
    posture: "Deletion rejected while the authoritative record is locked.",
    color: "error",
  },
  {
    state: "Export pending",
    posture: "Deletion rejected until export custody is resolved.",
    color: "error",
  },
  {
    state: "Expired",
    posture: "Eligible for future review only after authoritative reread.",
    color: "warning",
  },
  {
    state: "Active",
    posture: "Policy cannot close or advance active workflow records.",
    color: "primary",
  },
  {
    state: "Denied",
    posture: "Denied disposition remains preserved audit truth.",
    color: "default",
  },
] as const;

const RETENTION_NEGATIVE_POSTURES = [
  "Unsafe deletion rejected",
  "Historical rewrite rejected",
  "Policy-as-closeout rejected",
  "Stale retention cache rejected",
] as const;

const AUDIT_EXPORT_STATES = [
  {
    state: "Normal",
    posture:
      "Reviewed export window is ready to derive evidence from authoritative records.",
    color: "success",
  },
  {
    state: "Empty",
    posture:
      "No eligible authoritative records are present; empty export remains explicit.",
    color: "default",
  },
  {
    state: "Degraded",
    posture:
      "Export remains blocked or marked degraded when snapshot or custody signals are incomplete.",
    color: "warning",
  },
  {
    state: "Denied",
    posture:
      "Denied role access cannot request export configuration or view protected output.",
    color: "error",
  },
  {
    state: "Export pending",
    posture:
      "Pending generated output cannot be treated as audit, workflow, release, gate, or closeout truth.",
    color: "error",
  },
] as const;

const AUDIT_EXPORT_ACCESS_ROLES: RbacRoleId[] = [
  "platform_admin",
  "read_only_auditor",
  "analyst",
  "approver",
  "support_operator",
  "external_collaborator",
];

const AUDIT_EXPORT_NEGATIVE_POSTURES = [
  "Export config as audit truth rejected",
  "Export output as workflow truth rejected",
  "Denied role access rejected",
  "Stale export cache as authority rejected",
] as const;

function formatAccess(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function SourceProfileAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Source profile administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Source profile state configures source admission posture only; it
          cannot become signal, alert, case, evidence, workflow, release, gate,
          or closeout truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale source admin UI or browser cache is never authority. Backend
          record-chain reread remains decisive before source admission or
          workflow use.
        </Typography>
      </Stack>

      <Alert severity="info" variant="outlined">
        Wazuh profile administration remains bounded to reviewed source profile
        expectations; unsupported source onboarding and broad source catalog
        claims stay out of this surface.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack
                  alignItems="center"
                  direction={{ xs: "column", sm: "row" }}
                  justifyContent="space-between"
                  spacing={1}
                >
                  <Stack spacing={0.5}>
                    <Typography fontWeight={700}>Wazuh SMB single-node</Typography>
                    <Typography color="text.secondary" variant="body2">
                      Reviewed source profile for the Phase 53 Wazuh substrate
                      contract and source-health posture.
                    </Typography>
                  </Stack>
                  <Chip color="success" label="Reviewed" size="small" />
                </Stack>
                <Divider />
                <Stack spacing={1}>
                  {SOURCE_PROFILE_STATES.map((state) => (
                    <Stack key={state.label} spacing={0.5}>
                      <Typography fontWeight={600} variant="body2">
                        {state.label}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        {state.posture}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Audit trail
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {SOURCE_PROFILE_AUDIT_TRAIL.map((entry) => (
                    <Typography key={entry} variant="body2">
                      {entry}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Future reviewed sources
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {FUTURE_SOURCE_POSTURE.map((entry) => (
                    <Typography key={entry} variant="body2">
                      {entry}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

function ActionPolicyAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Action policy administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Action policy admin config is eligible posture only; stale UI or
          cache state cannot approve, execute, reconcile, mutate substrates, or
          rewrite historical receipts.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Existing approval, execution, and reconciliation authority remains
          backend-owned and reread from the authoritative record chain.
        </Typography>
      </Stack>

      <Alert severity="warning" variant="outlined">
        Controlled and Hard Write default enablement is rejected; those action
        families remain approval-bound and backend-enforced.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Default low-risk posture
                </Typography>
                <Divider />
                <Stack spacing={1.5}>
                  {ACTION_POLICY_POSTURES.map((policy) => (
                    <Stack key={policy.family} spacing={0.75}>
                      <Stack
                        alignItems="center"
                        direction={{ xs: "column", sm: "row" }}
                        justifyContent="space-between"
                        spacing={1}
                      >
                        <Typography fontWeight={600}>{policy.family}</Typography>
                        <Chip
                          color={
                            policy.posture === "Allowed by default"
                              ? "success"
                              : "warning"
                          }
                          label={policy.posture}
                          size="small"
                        />
                      </Stack>
                      <Typography color="text.secondary" variant="body2">
                        {policy.description}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Rejected default enablement
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {DISABLED_ACTION_POLICY_POSTURES.map((policy) => (
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      key={policy.family}
                      spacing={1}
                    >
                      <Typography fontWeight={600} variant="body2">
                        {policy.family}
                      </Typography>
                      <Chip
                        color="error"
                        label={policy.posture}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Policy audit trail
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {ACTION_POLICY_AUDIT_TRAIL.map((entry) => (
                    <Typography key={entry} variant="body2">
                      {entry}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

function RetentionPolicyAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Retention policy administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Retention policy admin config can define posture and review windows
          only; it cannot delete locked or export-pending records, close active
          workflow records, erase audit truth, or rewrite historical record
          chains.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale retention admin cache is never authority. Backend authoritative
          lifecycle state and record-chain reread remain decisive before any
          future purge candidate can be considered.
        </Typography>
      </Stack>

      <Alert severity="warning" variant="outlined">
        Retention administration leaves runtime purge jobs, customer-specific
        retention modeling, broad reporting, and RC/GA readiness outside this
        surface.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Record families
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {RETENTION_RECORD_FAMILIES.map((recordFamily) => (
                    <Stack key={recordFamily.family} spacing={0.5}>
                      <Typography fontWeight={600} variant="body2">
                        {recordFamily.family}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        {recordFamily.posture}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Retention states
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {RETENTION_STATE_POSTURES.map((state) => (
                    <Stack key={state.state} spacing={0.75}>
                      <Chip
                        color={
                          state.color as
                            | "default"
                            | "error"
                            | "primary"
                            | "warning"
                        }
                        label={state.state}
                        size="small"
                        sx={{ alignSelf: "flex-start" }}
                        variant={state.color === "default" ? "outlined" : "filled"}
                      />
                      <Typography color="text.secondary" variant="body2">
                        {state.posture}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Fail-closed checks
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {RETENTION_NEGATIVE_POSTURES.map((posture) => (
                    <Typography key={posture} variant="body2">
                      {posture}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

function AuditExportAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Audit export administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Audit export admin config can request export windows and custody
          posture only; it cannot rewrite historical audit records, workflow
          records, release gates, or closeout truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Generated exports remain derived evidence from authoritative AegisOps
          records and must be reread from one committed backend snapshot.
        </Typography>
      </Stack>

      <Alert severity="info" variant="outlined">
        This surface does not add commercial reporting breadth, compliance
        templates, support bundles, production report custody, or RC/GA
        readiness claims.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Export states
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {AUDIT_EXPORT_STATES.map((state) => (
                    <Stack key={state.state} spacing={0.75}>
                      <Chip
                        color={
                          state.color as
                            | "default"
                            | "error"
                            | "success"
                            | "warning"
                        }
                        label={state.state}
                        size="small"
                        sx={{ alignSelf: "flex-start" }}
                        variant={state.color === "default" ? "outlined" : "filled"}
                      />
                      <Typography color="text.secondary" variant="body2">
                        {state.posture}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  RBAC export access
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {AUDIT_EXPORT_ACCESS_ROLES.map((roleId) => (
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      key={roleId}
                      spacing={1}
                    >
                      <Typography fontWeight={600} variant="body2">
                        {roleId}:{" "}
                        {formatAccess(RBAC_ROLE_MATRIX[roleId].surfaces.auditExport)}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Fail-closed checks
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {AUDIT_EXPORT_NEGATIVE_POSTURES.map((posture) => (
                    <Typography key={posture} variant="body2">
                      {posture}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

export function UserRoleAdminPage() {
  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h4">
          User and role administration
        </Typography>
        <Typography color="text.secondary" variant="body1">
          User and role changes are reviewed policy/config state only; they
          cannot rewrite historical workflow truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale browser role cache is never authority. Backend reread and denial
          remain decisive.
        </Typography>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack spacing={0.5}>
                  <Typography component="h2" variant="h5">
                    Users
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Minimum reviewed account bindings for the operator console.
                    The backend remains the source of effective access.
                  </Typography>
                </Stack>
                <Divider />
                {ADMIN_USERS.map((user) => (
                  <Stack key={user.email} spacing={0.75}>
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      spacing={1}
                    >
                      <Typography fontWeight={600}>{user.email}</Typography>
                      <Chip label={user.status} size="small" />
                    </Stack>
                    <Typography color="text.secondary" variant="body2">
                      Assigned role: {user.role}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack spacing={0.5}>
                  <Typography component="h2" variant="h5">
                    Roles
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Phase 57.1 role matrix values are rendered as policy posture,
                    not workflow authority or approval truth.
                  </Typography>
                </Stack>
                <Divider />
                {ADMIN_ROLE_IDS.map((roleId) => {
                  const contract = RBAC_ROLE_MATRIX[roleId];

                  return (
                    <Stack key={roleId} spacing={1}>
                      <Stack
                        alignItems="center"
                        direction={{ xs: "column", sm: "row" }}
                        justifyContent="space-between"
                        spacing={1}
                      >
                        <Typography fontWeight={600}>{roleId}</Typography>
                        <Chip
                          color={
                            roleId === "platform_admin" ? "primary" : "default"
                          }
                          label={formatAccess(contract.surfaces.platformAdministration)}
                          size="small"
                        />
                      </Stack>
                      <Typography color="text.secondary" variant="body2">
                        {contract.description}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        Historical truth rewrite:{" "}
                        {formatAccess(contract.surfaces.historicalTruthRewrite)}
                      </Typography>
                    </Stack>
                  );
                })}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <SourceProfileAdministrationPage />

      <ActionPolicyAdministrationPage />

      <RetentionPolicyAdministrationPage />

      <AuditExportAdministrationPage />
    </Stack>
  );
}
