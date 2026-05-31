import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

const normalLimitationOwnership = {
  authority_boundary: "reviewed_evidence_input_only",
  authority_posture: "subordinate_limitation_context_only",
  consumer: "inspection",
  due_date: "2026-06-15",
  evidence_references: [
    "docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition",
  ],
  gate_truth: false,
  limitation_id: "limitation-phase64-support-bundle-001",
  mitigation: "Track the support bundle slice before Phase 66 RC proof.",
  owner: "supportability-owner",
  phase66_handoff_posture: "handoff_required",
  readiness_truth: false,
  release_truth: false,
  review_cadence: "weekly",
  review_due_date_expired: false,
  review_due_date_status: "current",
  review_state: "accepted_risk",
  severity: "material",
  title: "Support bundle evidence remains separately tracked.",
  affected_surface: "supportability_evidence",
  workflow_authority: "none",
  workflow_truth: false,
};

const normalLimitationOwnershipListRecord = {
  affected_surface: normalLimitationOwnership.affected_surface,
  authority_boundary: normalLimitationOwnership.authority_boundary,
  due_date: normalLimitationOwnership.due_date,
  evidence_references: normalLimitationOwnership.evidence_references,
  limitation_id: normalLimitationOwnership.limitation_id,
  mitigation: normalLimitationOwnership.mitigation,
  owner: normalLimitationOwnership.owner,
  phase66_handoff_posture: normalLimitationOwnership.phase66_handoff_posture,
  readiness_claim: null,
  review_cadence: normalLimitationOwnership.review_cadence,
  review_state: normalLimitationOwnership.review_state,
  severity: normalLimitationOwnership.severity,
  title: normalLimitationOwnership.title,
};

export function registerOperatorRoutesLimitationOwnershipTests() {
  describe("limitation ownership route", () => {
    it("renders reviewed limitation ownership as subordinate backend context", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-limitation-ownership?limitation_id=limitation-phase64-support-bundle-001":
          normalLimitationOwnership,
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      renderOperatorRoute(
        "/operator/limitations?limitation_id=limitation-phase64-support-bundle-001",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Limitation ownership" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByText("Support bundle evidence remains separately tracked."),
      ).toBeInTheDocument();
      expect(screen.getByText("Owner: supportability-owner")).toBeInTheDocument();
      expect(
        screen.getByText("Track the support bundle slice before Phase 66 RC proof."),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition",
        ),
      ).toBeInTheDocument();
      expect(screen.getByText("Affected surface: supportability evidence")).toBeInTheDocument();
      expect(screen.getByText("Phase 66 handoff: handoff required")).toBeInTheDocument();
      expect(screen.getByText("Due date: 2026-06-15")).toBeInTheDocument();
      expect(screen.getByText("Cadence: weekly")).toBeInTheDocument();
      expect(screen.getByText("Subordinate limitation context only")).toBeInTheDocument();
      expect(
        screen.getByText(
          "This surface cannot satisfy readiness, release, gate, workflow, or limitation resolution truth.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /resolve/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /approve/i })).toBeNull();
      expect(screen.queryByText(/ready for rc/i)).toBeNull();
      expect(fetchFn).toHaveBeenCalledWith(
        "/inspect-limitation-ownership?limitation_id=limitation-phase64-support-bundle-001",
        {
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        },
      );
    });

    it("requires operators to choose a concrete limitation before detail inspection", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-records?family=known_limitation_ownership": {
          records: [normalLimitationOwnershipListRecord],
          total_records: 1,
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      renderOperatorRoute("/operator/limitations", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Limitation ownership" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByText(
          "Limitation ownership detail remains subordinate backend context and requires a concrete reviewed limitation id.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Support bundle evidence remains separately tracked.",
        }),
      ).toHaveAttribute(
        "href",
        "/operator/limitations?limitation_id=limitation-phase64-support-bundle-001",
      );
      expect(
        fetchFn.mock.calls.some(([url]) =>
          String(url).startsWith("/inspect-limitation-ownership"),
        ),
      ).toBe(false);
    });

    it("fails closed on browser or cache sourced limitation ownership truth", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-limitation-ownership?limitation_id=limitation-phase64-support-bundle-001": {
            ...normalLimitationOwnership,
            projection_source: "browser_cache",
          },
        }),
      });

      renderOperatorRoute(
        "/operator/limitations?limitation_id=limitation-phase64-support-bundle-001",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", {
            name: "Limitation ownership unavailable",
          }),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByText("Support bundle evidence remains separately tracked."),
      ).toBeNull();
      expect(
        screen.getByText(
          "The backend limitation ownership projection was stale, malformed, or claimed authority the browser cannot hold.",
        ),
      ).toBeInTheDocument();
    });

    it("fails closed when limitation ownership omits review timing", async () => {
      const payloadWithoutReviewTiming: Record<string, unknown> = {
        ...normalLimitationOwnership,
      };
      delete payloadWithoutReviewTiming.due_date;
      delete payloadWithoutReviewTiming.review_cadence;
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-limitation-ownership?limitation_id=limitation-phase64-support-bundle-001": {
            ...payloadWithoutReviewTiming,
            review_due_date_status: "not_specified",
          },
        }),
      });

      renderOperatorRoute(
        "/operator/limitations?limitation_id=limitation-phase64-support-bundle-001",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", {
            name: "Limitation ownership unavailable",
          }),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByText("Support bundle evidence remains separately tracked."),
      ).toBeNull();
    });
  });
}
