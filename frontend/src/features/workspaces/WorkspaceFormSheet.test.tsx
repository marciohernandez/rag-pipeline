import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import WorkspaceFormSheet from "@/features/workspaces/WorkspaceFormSheet";
import { saveSession } from "@/lib/session";

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-owner");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("WorkspaceFormSheet", () => {
  it("cria com nome normalizado, feedback de envio e resultado", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-001 FR-008 AC-001
    let responder!: (response: Response) => void;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockReturnValue(
      new Promise((resolve) => { responder = resolve; }),
    );
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(<WorkspaceFormSheet open onSaved={onSaved} />);

    expect(screen.getByRole("dialog", { name: /criar workspace/i })).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Nome" }), "  Vivo — Gold  ");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    expect(screen.getByRole("button", { name: /salvando/i })).toBeDisabled();
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/workspaces");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ nome: "Vivo — Gold" });

    responder(new Response('{"id":"workspace-1","nome":"Vivo — Gold"}', { status: 201 }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith({ id: "workspace-1", nome: "Vivo — Gold" }));
  });

  it("edita o mesmo Workspace sem trocar sua identidade", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-002 FR-008 AC-002
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"id":"workspace-1","nome":"Novo nome"}', { status: 200 }),
    );
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(
      <WorkspaceFormSheet
        open
        workspace={{ id: "workspace-1", nome: "Nome antigo" }}
        onSaved={onSaved}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Nome" })).toHaveValue("Nome antigo");
    await user.clear(screen.getByRole("textbox", { name: "Nome" }));
    await user.type(screen.getByRole("textbox", { name: "Nome" }), "Novo nome");
    await user.keyboard("{Enter}");

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith({ id: "workspace-1", nome: "Novo nome" }));
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/workspaces/workspace-1");
    expect(init.method).toBe("PATCH");
  });

  it("valida nome vazio antes da API, associa o erro e move o foco", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-001 NFR-002 AC-004 AC-022
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const user = userEvent.setup();
    render(<WorkspaceFormSheet open onSaved={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Salvar" }));

    const campo = screen.getByRole("textbox", { name: "Nome" });
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(campo).toHaveFocus();
    expect(campo).toHaveAttribute("aria-invalid", "true");
    expect(campo).toHaveAccessibleDescription(/informe um nome/i);
    expect(screen.getByRole("alert")).toHaveTextContent(/informe um nome/i);
  });

  it("mantém o nome após falha segura da API para permitir nova tentativa", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-001 FR-008 NFR-002 AC-023
    const fetchSpy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response('{"detail":"erro interno sensível"}', { status: 500 }))
      .mockResolvedValueOnce(new Response('{"id":"workspace-2","nome":"Retentativa"}', { status: 201 }));
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(<WorkspaceFormSheet open onSaved={onSaved} />);

    await user.type(screen.getByRole("textbox", { name: "Nome" }), "Retentativa");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).not.toHaveTextContent(/sensível/i);
    expect(screen.getByRole("textbox", { name: "Nome" })).toHaveValue("Retentativa");
    await user.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("limpa o rascunho ao cancelar e reabrir", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    const { rerender } = render(
      <WorkspaceFormSheet open onOpenChange={onOpenChange} onSaved={vi.fn()} />,
    );

    await user.type(screen.getByRole("textbox", { name: "Nome" }), "Rascunho");
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
    rerender(<WorkspaceFormSheet open={false} onOpenChange={onOpenChange} onSaved={vi.fn()} />);
    rerender(<WorkspaceFormSheet open onOpenChange={onOpenChange} onSaved={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Nome" })).toHaveValue("");
  });
});
