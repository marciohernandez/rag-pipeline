import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ExcluirWorkspaceDialog from "@/features/workspaces/ExcluirWorkspaceDialog";
import { saveSession } from "@/lib/session";

const workspace = { id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" };

beforeEach(() => {
  sessionStorage.clear();
  saveSession("token-demo-owner");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ExcluirWorkspaceDialog", () => {
  it("confirma o alvo e apaga Workspace vazio", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-003 FR-008 AC-005
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases={false} papel="owner"
        onDeleted={onDeleted}
      />,
    );

    expect(screen.getByRole("dialog")).toHaveTextContent(workspace.nome);
    expect(screen.getByRole("dialog")).toHaveTextContent(/deixará de aparecer/i);
    await user.click(screen.getByRole("button", { name: /^apagar workspace$/i }));

    await waitFor(() => expect(onDeleted).toHaveBeenCalledWith(workspace.id));
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/workspaces/workspace-1");
    expect(init.method).toBe("DELETE");
  });

  it("bloqueia a ação e explica o motivo quando há Bases", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-003 AC-006
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases papel="admin"
        onDeleted={vi.fn()}
      />,
    );

    expect(screen.getByText(/apague ou mova as bases/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^apagar workspace$/i })).toBeDisabled();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("não oferece exclusão para member", () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases={false} papel="member"
        onDeleted={vi.fn()}
      />,
    );

    expect(screen.getByRole("dialog")).toHaveTextContent(workspace.nome);
    expect(screen.queryByRole("button", { name: /^apagar workspace$/i })).not.toBeInTheDocument();
  });

  it("trata 409 sem apagar nem expor mensagem interna", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-003 NFR-002 AC-006 AC-023
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"tenant secreto: base inserida"}', { status: 409 }),
    );
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases={false} papel="owner"
        onDeleted={onDeleted}
      />,
    );

    await user.click(screen.getByRole("button", { name: /^apagar workspace$/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(/apague ou mova as bases/i);
    expect(alerta).not.toHaveTextContent(/secreto/i);
    expect(onDeleted).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /^apagar workspace$/i })).toBeDisabled();
  });

  it("preserva o diálogo após erro e permite fechar por Cancelar", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-003 NFR-002 AC-023
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"stack trace interno"}', { status: 500 }),
    );
    const onOpenChange = vi.fn();
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases={false} papel="owner"
        onOpenChange={onOpenChange} onDeleted={onDeleted}
      />,
    );

    await user.click(screen.getByRole("button", { name: /^apagar workspace$/i }));
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(/não foi possível apagar/i);
    expect(alerta).not.toHaveTextContent(/stack trace/i);
    expect(onDeleted).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("mantém o foco no diálogo e aceita Escape", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    render(
      <ExcluirWorkspaceDialog
        open workspace={workspace} temBases={false} papel="owner"
        onOpenChange={onOpenChange} onDeleted={vi.fn()}
      />,
    );

    await waitFor(() =>
      expect(screen.getByRole("dialog")).toContainElement(
        document.activeElement as HTMLElement | null,
      ),
    );
    await user.keyboard("{Escape}");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
