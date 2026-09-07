import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Componente ainda não existe (RED de T024/T025/T026).
import ExcluirBaseDialog from "@/features/bases/ExcluirBaseDialog";

const base = { id: "base-1", nome: "base-exemplo" };

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ExcluirBaseDialog", () => {
  it("confirma com o nome e a consequência e chama DELETE ao apagar", async () => {
    // SPECSFY: US-003 FR-007 AC-011 (SPEC-0013)
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(<ExcluirBaseDialog open base={base} papel="owner" onDeleted={onDeleted} />);

    expect(screen.getByRole("dialog")).toHaveTextContent(/base-exemplo/);
    expect(screen.getByRole("dialog")).toHaveTextContent(
      /execuç|consulta|vetor/i,
    );

    await user.click(screen.getByRole("button", { name: /apagar/i }));

    expect(fetchSpy).toHaveBeenCalled();
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toMatch(/\/api\/v1\/bases\/base-1$/);
    expect(init.method).toBe("DELETE");
    expect(onDeleted).toHaveBeenCalledWith("base-1");
  });

  it("não oferece a ação de apagar para member", () => {
    // SPECSFY: US-003 FR-007 AC-019 (SPEC-0013)
    render(<ExcluirBaseDialog open base={base} papel="member" onDeleted={vi.fn()} />);

    expect(screen.queryByRole("button", { name: /apagar/i })).toBeNull();
  });

  it("após apagar, informa o pai para remover a base da listagem", async () => {
    // SPECSFY: US-003 FR-007 AC-020 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(<ExcluirBaseDialog open base={base} papel="admin" onDeleted={onDeleted} />);

    await user.click(screen.getByRole("button", { name: /apagar/i }));

    expect(onDeleted).toHaveBeenCalledWith("base-1");
  });
});
