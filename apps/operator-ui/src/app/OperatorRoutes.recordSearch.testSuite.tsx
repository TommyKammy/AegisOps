import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

const recordSearchResults = [
  {
    id: "case:case-001",
    record_family: "case",
    record_id: "case-001",
    source_family: "github_audit",
    lifecycle_state: "open",
    route: "/operator/cases/case-001",
    route_kind: "reviewed_surface",
    authority: "navigation_only",
    raw_source_authority: false,
    matched_query: "github",
    summary: "Reviewed GitHub audit case.",
  },
  {
    id: "source_health:source-health-github-audit-001",
    record_family: "source_health",
    record_id: "source-health-github-audit-001",
    source_family: "github_audit",
    lifecycle_state: "reviewed",
    route: "/operator/source-health",
    route_kind: "reviewed_surface",
    authority: "navigation_only",
    raw_source_authority: false,
    matched_query: "github",
    summary: "Reviewed GitHub audit source is available.",
  },
] as const;

export function registerOperatorRoutesRecordSearchTests() {
  describe("record search route", () => {
    it("searches reviewed records and routes only to reviewed surfaces", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-record-search": {
          records: recordSearchResults,
          total_records: recordSearchResults.length,
        },
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      renderOperatorRoute("/operator/search", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Record Search" }),
        ).toBeInTheDocument();
      });

      expect(await screen.findByRole("link", { name: "case:case-001" })).toHaveAttribute(
        "href",
        "/operator/cases/case-001",
      );
      expect(screen.getAllByText("navigation_only").length).toBeGreaterThan(0);
      expect(screen.queryByRole("button", { name: /close case/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /reconcile/i })).toBeNull();

      const searchCall = fetchFn.mock.calls.find(([url]) =>
        String(url).startsWith("/inspect-record-search"),
      );
      expect(searchCall).toBeDefined();
      const parsedUrl = new URL(String(searchCall![0]), "http://operator-ui.local");
      expect(parsedUrl.searchParams.get("q")).toBe("github");

      fireEvent.change(screen.getByLabelText("Search reviewed records"), {
        target: { value: "source-health" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Search" }));

      await waitFor(() => {
        const latestSearchCall = fetchFn.mock.calls
          .map(([url]) => String(url))
          .filter((url) => url.startsWith("/inspect-record-search"))
          .at(-1);
        expect(latestSearchCall).toContain("q=source-health");
      });
    });

    it("fails closed for stale-cache or authority-leaking search results", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-record-search": {
            records: [
              {
                ...recordSearchResults[0],
                authority: "workflow_truth",
                raw_source_authority: true,
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/search", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("workflow_truth")).not.toBeInTheDocument();
    });
  });
}
