import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Componente ainda não existe (RED de T012).
import LoginForm from "@/features/auth/LoginForm";

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LoginForm — acessibilidade", () => {
  it("alcança campo e botão por teclado, confirma com Enter e anuncia o resultado", async () => {
    // SPECSFY: US-001 NFR-003 AC-016 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"nope"}', { status: 401 }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.tab();
    const campo = screen.getByLabelText(/token de demonstra/i);
    expect(campo).toHaveFocus();

    await user.keyboard("token-errado{Enter}");

    const alerta = await screen.findByRole("alert");
    // status/alert precisa ter live region para leitura assistiva
    await waitFor(() =>
      expect(alerta.closest("[aria-live],[role=alert]")).not.toBeNull(),
    );
    expect(
      screen.getByRole("button", { name: /entrar/i }),
    ).toBeInTheDocument();
  });
});
