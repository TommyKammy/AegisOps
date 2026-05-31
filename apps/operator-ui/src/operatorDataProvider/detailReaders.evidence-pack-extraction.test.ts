import { describe, expect, it } from "vitest";
import detailReadersSource from "./detailReaders.ts?raw";
import linkedEvidencePackValidatorSource from "./linkedEvidencePackValidator.ts?raw";

describe("case detail evidence-pack validation layout", () => {
  it("keeps linked evidence-pack validation in a focused validator module", () => {
    expect(linkedEvidencePackValidatorSource).toContain(
      "export function validateLinkedEvidencePacks",
    );
    expect(linkedEvidencePackValidatorSource).toContain(
      "function validateEvidencePackLabel",
    );
    expect(detailReadersSource).toContain(
      'import { validateLinkedEvidencePacks } from "./linkedEvidencePackValidator";',
    );
    expect(detailReadersSource).not.toContain(
      "const EVIDENCE_PACK_ALLOWED_LABELS",
    );
    expect(detailReadersSource).not.toContain(
      "function validateEvidencePackLabel",
    );
  });
});
