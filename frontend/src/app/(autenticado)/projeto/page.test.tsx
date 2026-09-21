import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";

const navigation = vi.hoisted(() => ({
  permanentRedirect: vi.fn(() => {
    throw new Error("REDIRECT");
  }),
}));
vi.mock("next/navigation", () => ({
  permanentRedirect: navigation.permanentRedirect,
  useRouter: () => ({ push: vi.fn() }),
}));

import ProjetoPage from "@/app/(autenticado)/projeto/page";

describe("ProjetoPage", () => {
  it("preserva o link antigo com redirect permanente para Workspaces", () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("[]", { status: 200 }));
    expect(() => render(<ProjetoPage />)).toThrow("REDIRECT");
    expect(navigation.permanentRedirect).toHaveBeenCalledWith("/workspaces");
  });
});
