import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Importado depois dos mocks; o componente ainda não existe (RED de T008/T009).
import LoginForm from "@/features/auth/LoginForm";
import { getToken } from "@/lib/session";

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LoginForm", () => {
  it("guarda o token em sessionStorage e leva aos Workspaces quando o backend aceita", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-001 (SPEC-0013)
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("[]", { status: 200, headers: { "content-type": "application/json" } }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(
      screen.getByLabelText(/token de demonstra/i),
      "token-demo-owner",
    );
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => expect(getToken()).toBe("token-demo-owner"));
    expect(push).toHaveBeenCalledWith("/workspaces");
  });

  it("rejeita token inválido com erro genérico, preserva o campo e não guarda sessão", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-002 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Token inválido"}', {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    const campo = screen.getByLabelText(/token de demonstra/i);
    await user.type(campo, "token-errado");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("alert").textContent ?? "").not.toMatch(/inválido/i);
    expect(campo).toHaveValue("token-errado");
    expect(getToken()).toBeNull();
    expect(push).not.toHaveBeenCalled();
  });
});
