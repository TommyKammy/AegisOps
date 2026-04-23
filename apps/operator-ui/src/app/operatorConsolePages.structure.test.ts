import { describe, expect, it } from "vitest";

const operatorConsolePageModules = Object.keys(
  import.meta.glob("./operatorConsolePages/*.tsx"),
);

describe("operatorConsolePages module structure", () => {
  it("keeps the entrypoint thin and delegates route families to dedicated modules", async () => {
    const entrypointModule = await import("./operatorConsolePages.tsx?raw");
    const entrypointSource = entrypointModule.default as string;
    const entrypointLineCount = entrypointSource.split("\n").length;

    expect(entrypointLineCount).toBeLessThanOrEqual(400);
    expect(operatorConsolePageModules.length).toBeGreaterThanOrEqual(4);
  });
});
