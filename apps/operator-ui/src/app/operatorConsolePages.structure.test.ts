import { describe, expect, it } from "vitest";

const operatorConsolePageModules = Object.keys(
  import.meta.glob("./operatorConsolePages/*.tsx"),
);
const taskActionModules = Object.keys(import.meta.glob("../taskActions/*.tsx"));

async function countSourceLines(path: string) {
  const module = await import(`${path}?raw`);
  const source = module.default as string;
  return source.split("\n").length;
}

describe("operatorConsolePages module structure", () => {
  it("keeps the entrypoint thin and delegates route families to dedicated modules", async () => {
    const entrypointLineCount = await countSourceLines("./operatorConsolePages.tsx");

    expect(entrypointLineCount).toBeLessThanOrEqual(400);
    expect(operatorConsolePageModules.length).toBeGreaterThanOrEqual(4);
  });

  it("keeps casework detail and reviewed action card surfaces decomposed", async () => {
    await expect(countSourceLines("./operatorConsolePages/caseworkPages.tsx")).resolves.toBeLessThanOrEqual(
      350,
    );
    await expect(countSourceLines("../taskActions/caseworkActionCards.tsx")).resolves.toBeLessThanOrEqual(
      450,
    );
    expect(operatorConsolePageModules).toContain("./operatorConsolePages/caseDetailSurfaces.tsx");
    expect(taskActionModules).toEqual(
      expect.arrayContaining([
        "../taskActions/actionRequestActionCards.tsx",
        "../taskActions/actionReviewActionCards.tsx",
      ]),
    );
  });
});
