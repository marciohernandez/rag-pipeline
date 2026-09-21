import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import WorkspacesPage from "@/app/(autenticado)/workspaces/page";
import { saveSession } from "@/lib/session";

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("WorkspacesPage", () => {
  it("lista Workspaces e mostra a ação de criação para owner", async () => {
    // SPECSFY: SPEC-0019 US-001 FR-001 FR-008 AC-001
    saveSession("token-demo-owner");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('[{"id":"workspace-1","nome":"Vivo — Gold"}]', {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    render(<WorkspacesPage />);

    expect(await screen.findByText("Vivo — Gold")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /criar workspace/i })).toBeInTheDocument();
  });

  it("abre a criação para admin e inclui o Workspace salvo na listagem", async () => {
    // SPECSFY: SPEC-0019 US-001 US-004 FR-001 FR-008 AC-001 AC-003
    saveSession("token-demo-admin");
    const fetchSpy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("[]", { status: 200 }))
      .mockResolvedValueOnce(
        new Response('{"id":"workspace-novo","nome":"Atendimento B2B"}', {
          status: 201,
        }),
      );
    const user = userEvent.setup();
    render(<WorkspacesPage />);

    await screen.findByText("Nenhum Workspace ainda");
    await user.click(screen.getByRole("button", { name: /criar workspace/i }));
    expect(screen.getByRole("dialog", { name: /criar workspace/i })).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Nome" }), "Atendimento B2B");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await screen.findByText("Atendimento B2B")).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: /criar workspace/i })).not.toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("mantém a listagem somente leitura para member", async () => {
    // SPECSFY: SPEC-0019 US-001 US-004 FR-001 FR-008 AC-003 AC-017
    saveSession("token-demo-member");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('[{"id":"workspace-1","nome":"Vivo"}]', {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    render(<WorkspacesPage />);

    expect(await screen.findByText("Vivo")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /criar workspace/i })).not.toBeInTheDocument();
  });

  it("mostra o estado vazio depois do carregamento", async () => {
    saveSession("token-demo-owner");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("[]", {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    render(<WorkspacesPage />);

    expect(await screen.findByText("Nenhum Workspace ainda")).toBeInTheDocument();
  });

  it("mostra erro seguro e permite tentar novamente", async () => {
    saveSession("token-demo-owner");
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response('{"detail":"erro interno sensível"}', {
          status: 500,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response('[{"id":"workspace-2","nome":"Recuperado"}]', {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );
    const user = userEvent.setup();

    render(<WorkspacesPage />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(/não foi possível carregar/i);
    expect(alerta).not.toHaveTextContent(/sensível/i);

    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Recuperado")).toBeInTheDocument();
  });
});
