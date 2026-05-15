import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

const detectorLifecycleRecords = [
  {
    detector_lifecycle_id: "det-candidate-001",
    owner: "detector-owner-candidate",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    detector_identifier: "github-audit-impossible-travel",
    expected_signal_posture: "reviewed low-volume activation candidate",
    review_cadence: "weekly",
    rollback_owner: "rollback-owner-candidate",
    disable_owner: "disable-owner-candidate",
    lifecycle_audit_references: ["audit-evidence://candidate-001"],
    lifecycle_state: "candidate",
    source_native_lifecycle_state: "active",
  },
  {
    detector_lifecycle_id: "det-staging-001",
    owner: "detector-owner-staging",
    source_family: "entra_id",
    source_catalog_entry: "docs/source-families/entra-id/onboarding-package.md",
    detector_identifier: "entra-id-risky-sign-in",
    expected_signal_posture: "staging with reviewed sampling",
    review_cadence: "weekly",
    rollback_owner: "rollback-owner-staging",
    disable_owner: "disable-owner-staging",
    lifecycle_audit_references: ["audit-evidence://staging-001"],
    lifecycle_state: "staging",
  },
  {
    detector_lifecycle_id: "det-active-001",
    owner: "detector-owner-active",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    detector_identifier: "github-audit-owner-change",
    expected_signal_posture: "active reviewed signal posture",
    review_cadence: "monthly",
    rollback_owner: "rollback-owner-active",
    disable_owner: "disable-owner-active",
    lifecycle_audit_references: ["audit-evidence://active-001"],
    lifecycle_state: "active",
  },
  {
    detector_lifecycle_id: "det-disabled-001",
    owner: "detector-owner-disabled",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    detector_identifier: "github-audit-disabled-noisy-rule",
    expected_signal_posture: "disabled after reviewed false-positive spike",
    review_cadence: "monthly",
    rollback_owner: "rollback-owner-disabled",
    disable_owner: "disable-owner-disabled",
    lifecycle_audit_references: ["audit-evidence://disabled-001"],
    lifecycle_state: "disabled",
    disabled_reason: "Reviewed noisy-rule disablement",
  },
  {
    detector_lifecycle_id: "det-rollback-001",
    owner: "detector-owner-rollback",
    source_family: "entra_id",
    source_catalog_entry: "docs/source-families/entra-id/onboarding-package.md",
    detector_identifier: "entra-id-rollback-signin-rule",
    expected_signal_posture: "rollback after reviewed regression",
    review_cadence: "weekly",
    rollback_owner: "rollback-owner-rollback",
    disable_owner: "disable-owner-rollback",
    lifecycle_audit_references: ["audit-evidence://rollback-001"],
    lifecycle_state: "rollback",
    rollback_reason: "Reviewed rollback reason",
  },
  {
    detector_lifecycle_id: "det-overdue-001",
    owner: "detector-owner-overdue",
    source_family: "github_audit",
    source_catalog_entry: "docs/source-families/github-audit/onboarding-package.md",
    detector_identifier: "github-audit-overdue-rule",
    expected_signal_posture: "review overdue",
    review_cadence: "weekly",
    rollback_owner: "rollback-owner-overdue",
    disable_owner: "disable-owner-overdue",
    lifecycle_audit_references: ["audit-evidence://overdue-001"],
    lifecycle_state: "review-overdue",
    review_overdue_reason: "Next review missed by owner",
  },
] as const;

export function registerOperatorRoutesDetectorActivationReviewTests() {
  describe("detector activation review route", () => {
    it("renders reviewed detector activation posture without trusting source-native active state", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-records": {
          records: detectorLifecycleRecords,
          total_records: detectorLifecycleRecords.length,
        },
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      renderOperatorRoute("/operator/detectors", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Detector Activation Review" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByRole("menuitem", { name: "Detectors" })).toHaveAttribute(
        "href",
        expect.stringContaining("/operator/detectors"),
      );
      expect(screen.getByText("detector-owner-candidate")).toBeInTheDocument();
      expect(
        screen.getByText("reviewed low-volume activation candidate"),
      ).toBeInTheDocument();
      expect(screen.getAllByText("Expected volume").length).toBeGreaterThan(0);
      expect(screen.getAllByText("False-positive review").length).toBeGreaterThan(0);
      expect(screen.getByText("disable-owner-disabled")).toBeInTheDocument();
      expect(screen.getByText("rollback-owner-rollback")).toBeInTheDocument();
      expect(screen.getAllByText("Next review").length).toBeGreaterThan(0);
      expect(screen.getByText("Next review missed by owner")).toBeInTheDocument();
      for (const state of [
        "candidate",
        "staging",
        "active",
        "disabled",
        "rollback",
        "review-overdue",
      ]) {
        expect(screen.getAllByText(state).length).toBeGreaterThan(0);
      }
      expect(
        screen.getByText(
          "Source-native active status is subordinate display context only.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /activate/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /disable/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /rollback/i })).toBeNull();

      const detectorCall = fetchFn.mock.calls.find(([url]) =>
        String(url).startsWith("/inspect-records"),
      );
      expect(detectorCall).toBeDefined();
      const [url] = detectorCall!;
      const parsedUrl = new URL(String(url), "http://operator-ui.local");
      expect(parsedUrl.searchParams.get("family")).toBe("detector_lifecycle");
    });

    it("fails closed for missing owner, malformed lifecycle state, or stale display state", async () => {
      const invalidRecords = [
        {
          ...detectorLifecycleRecords[0],
          detector_lifecycle_id: "det-missing-owner",
          owner: "",
        },
        {
          ...detectorLifecycleRecords[0],
          detector_lifecycle_id: "det-malformed-state",
          lifecycle_state: "source-active",
        },
        {
          ...detectorLifecycleRecords[0],
          detector_lifecycle_id: "det-stale-display",
          stale_display_state: true,
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

      renderOperatorRoute("/operator/detectors", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("det-malformed-state")).not.toBeInTheDocument();
      expect(screen.queryByText("source-active")).not.toBeInTheDocument();
    });
  });
}
