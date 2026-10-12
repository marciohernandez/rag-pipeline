import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ConexaoFormSheet from "@/features/conexoes/ConexaoFormSheet";
import type { ConexaoResumo } from "@/features/conexoes/DataGridConexoes";

const existente: ConexaoResumo = {
  id: "con-1", nome: "OpenAI principal", tipo: "embeddings_openai", situacao: "ativa",
  configuracao: { modelo: "text-embedding-3-small", dimensoes: 1536 },
  segredo_definido: true, segredo_mascara: "••••••••", em_uso: 0,
};
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ConexaoFormSheet", () => {
  it("cria uma conexão de embeddings enviando a chave uma única vez", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-002 FR-012 FR-014 NFR-004 AC-018
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ ...existente, id: "novo" }, 201));
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(<ConexaoFormSheet open onSaved={onSaved} />);

    await user.type(screen.getByLabelText("Nome"), "OpenAI principal");
    await user.type(screen.getByLabelText("Chave"), "sk-teste-123");
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toMatch(/\/api\/v1\/conexoes$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toMatchObject({
      nome: "OpenAI principal",
      tipo: "embeddings_openai",
      configuracao: { modelo: "text-embedding-3-small", dimensoes: 1536 },
      segredo: "sk-teste-123",
    });
  });

  it("na edição a chave nasce vazia e só é enviada quando uma nova é digitada", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-002 FR-012 FR-014 NFR-004 AC-018
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(existente));
    const user = userEvent.setup();
    render(<ConexaoFormSheet open conexao={existente} />);

    const chave = screen.getByLabelText("Chave");
    expect(chave).toHaveValue("");
    expect(chave).toHaveAttribute("placeholder", "••••••••");
    expect(screen.getByLabelText("Tipo")).toBeDisabled();
    await user.clear(screen.getByLabelText("Nome"));
    await user.type(screen.getByLabelText("Nome"), "OpenAI renomeada");
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toMatch(/\/api\/v1\/conexoes\/con-1$/);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).not.toHaveProperty("segredo");
  });

  it("mostra o erro abaixo do campo e foca o primeiro campo com erro", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-002 FR-012 FR-014 NFR-004 AC-018
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "A URL aponta para um endereço interno não permitido." }, 422));
    const user = userEvent.setup();
    render(<ConexaoFormSheet open />);

    await user.click(screen.getByRole("button", { name: /salvar/i }));
    expect(await screen.findByText("Informe o nome da conexão.")).toBeInTheDocument();
    expect(screen.getByLabelText("Nome")).toHaveFocus();

    await user.selectOptions(screen.getByLabelText("Tipo"), "qdrant");
    await user.type(screen.getByLabelText("Nome"), "Qdrant interno");
    await user.type(screen.getByLabelText("URL do Qdrant"), "http://localhost:6333");
    await user.click(screen.getByRole("button", { name: /salvar/i }));

    expect(await screen.findByText(/endereço interno não permitido/i)).toBeInTheDocument();
    expect(screen.getByLabelText("URL do Qdrant")).toHaveFocus();
    expect(screen.getByLabelText("URL do Qdrant")).toHaveAttribute("aria-invalid", "true");
  });
});
