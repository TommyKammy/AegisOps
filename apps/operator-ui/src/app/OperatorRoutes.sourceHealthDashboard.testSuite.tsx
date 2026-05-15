import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

const sourceHealthRecords = [
  {
    source_health_id: "source-health-available-001",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    health_state: "available",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-15T07:55:00Z",
    detector_drift: "none",
    credential_posture: "reviewed",
    evidence_references: ["evidence://source-health/github-audit"],
    operator_visible_reason: "Reviewed GitHub audit source is available.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
  {
    source_health_id: "source-health-missing-agent-001",
    source_family: "windows_security_endpoint",
    source_catalog_entry:
      "docs/source-families/windows-security-and-endpoint/onboarding-package.md",
    health_state: "missing_agent",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-15T07:50:00Z",
    detector_drift: "none",
    credential_posture: "reviewed",
    evidence_references: ["evidence://source-health/windows-endpoint"],
    operator_visible_reason: "Reviewed endpoint source is missing an agent.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
  {
    source_health_id: "source-health-parser-failure-001",
    source_family: "wazuh_detection",
    source_catalog_entry: "docs/phase-61-minimum-source-catalog-contract.md",
    health_state: "parser_failure",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-15T07:45:00Z",
    detector_drift: "review_required",
    credential_posture: "reviewed",
    evidence_references: ["evidence://source-health/wazuh-parser"],
    operator_visible_reason: "Parser failure and detector drift require review.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
  {
    source_health_id: "source-health-volume-anomaly-001",
    source_family: "microsoft_365_audit",
    source_catalog_entry: "docs/source-families/microsoft-365-audit/onboarding-package.md",
    health_state: "volume_anomaly",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-15T07:40:00Z",
    detector_drift: "none",
    credential_posture: "reviewed",
    evidence_references: ["evidence://source-health/m365-volume"],
    operator_visible_reason: "Reviewed Microsoft 365 audit volume anomaly.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
  {
    source_health_id: "source-health-credential-degraded-001",
    source_family: "entra_id",
    source_catalog_entry: "docs/source-families/entra-id/onboarding-package.md",
    health_state: "credential_degraded",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-15T07:35:00Z",
    detector_drift: "none",
    credential_posture: "degraded",
    evidence_references: ["evidence://source-health/entra-credential"],
    operator_visible_reason: "Credential degraded state is visible for operator review.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
  {
    source_health_id: "source-health-stale-001",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    health_state: "stale_source",
    reviewed_state: "reviewed",
    lifecycle_state: "reviewed",
    reviewed_at: "2026-05-15T08:00:00Z",
    observed_at: "2026-05-14T08:00:00Z",
    detector_drift: "none",
    credential_posture: "reviewed",
    evidence_references: ["evidence://source-health/github-stale"],
    operator_visible_reason: "Reviewed stale source remains visible.",
    source_native_authority: false,
    display_state_authority: false,
    cache_sourced: false,
  },
] as const;

export function registerOperatorRoutesSourceHealthDashboardTests() {
  describe("source-health dashboard route", () => {
    it("renders reviewed source-health rows as subordinate dashboard context", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-records": {
          records: sourceHealthRecords,
          total_records: sourceHealthRecords.length,
        },
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      renderOperatorRoute("/operator/source-health", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Source Health Dashboard" }),
        ).toBeInTheDocument();
      });

      for (const state of [
        "available",
        "missing_agent",
        "parser_failure",
        "volume_anomaly",
        "credential_degraded",
        "stale_source",
      ]) {
        expect(screen.getAllByText(state).length).toBeGreaterThan(0);
      }
      expect(screen.getByText("Detector drift: review_required")).toBeInTheDocument();
      expect(
        screen.getByText("Credential degraded state is visible for operator review."),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /close case/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /reconcile/i })).toBeNull();

      const healthCall = fetchFn.mock.calls.find(([url]) =>
        String(url).startsWith("/inspect-records"),
      );
      expect(healthCall).toBeDefined();
      const [url] = healthCall!;
      const parsedUrl = new URL(String(url), "http://operator-ui.local");
      expect(parsedUrl.searchParams.get("family")).toBe("source_health");
    });

    it("fails closed for malformed, stale-cache, or authority-leaking rows", async () => {
      const invalidRecords = [
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-malformed-state",
          health_state: "source_native_ok",
        },
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-cache",
          cache_sourced: true,
        },
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-authority-leak",
          source_native_authority: true,
        },
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-unreviewed-state",
          reviewed_state: "pending",
          lifecycle_state: "pending",
        },
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-lifecycle-mismatch",
          lifecycle_state: "superseded",
        },
        {
          ...sourceHealthRecords[0],
          source_health_id: "source-health-unreviewed-catalog",
          source_catalog_entry: "docs/source-families/github-audit/unreviewed.md",
        },
      ];
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-records": {
            records: invalidRecords,
            total_records: invalidRecords.length,
          },
        }),
      });

      renderOperatorRoute("/operator/source-health", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("source_native_ok")).not.toBeInTheDocument();
      expect(screen.queryByText("source-health-authority-leak")).not.toBeInTheDocument();
      expect(screen.queryByText("source-health-unreviewed-catalog")).not.toBeInTheDocument();
    });
  });
}
