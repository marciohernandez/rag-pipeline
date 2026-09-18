import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Componente ainda não existe (RED de T014/T015).
import UploadBaseSheet from "@/features/bases/UploadBaseSheet";

const md = (nome: string, corpo = "# titulo\nconteudo") =>
  new File([corpo], nome, { type: "text/markdown" });

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("UploadBaseSheet", () => {
  it("envia múltiplos .md válidos e cria uma base com origem upload", async () => {
    // SPECSFY: US-002 FR-004 AC-006 (SPEC-0013)
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response('{"base_id":"b-1"}', { status: 201 }),
      );
    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<UploadBaseSheet open onCreated={onCreated} />);

    await user.upload(screen.getByLabelText(/arquivos/i), [
      md("a.md"),
      md("b.md"),
    ]);
    await user.click(screen.getByRole("button", { name: /enviar/i }));

    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toMatch(/\/api\/v1\/bases$/);
    expect(init.method).toBe("POST");
  });

  it("associa o envio ao Workspace aberto", async () => {
    // SPECSFY: SPEC-0019 US-002 FR-004 AC-007
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response('{"base_id":"b-1"}', { status: 201 }));
    const user = userEvent.setup();
    render(
      <UploadBaseSheet
        open
        workspaceId="workspace-1"
        onCreated={vi.fn()}
      />,
    );

    await user.upload(screen.getByLabelText(/arquivos/i), [md("a.md")]);
    await user.click(screen.getByRole("button", { name: /^enviar$/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const body = fetchSpy.mock.calls[0]?.[1]?.body as FormData;
    expect(body.get("workspace_id")).toBe("workspace-1");
  });

  it("oferece a base preparada como contingência (origem preparada)", async () => {
    // SPECSFY: US-002 FR-004 AC-006 (SPEC-0013)
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response('{"base_id":"b-2"}', { status: 201 }));
    const user = userEvent.setup();
    render(<UploadBaseSheet open onCreated={vi.fn()} />);

    await user.click(
      screen.getByRole("button", { name: /base preparada/i }),
    );

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
    expect(String(init.body)).toMatch(/usar_base_preparada/);
  });

  it("rejeita envio acima de 50 arquivos antes de chamar o backend e preserva os válidos", async () => {
    // SPECSFY: US-002 FR-004 AC-007 (SPEC-0013)
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 201 }),
    );
    const user = userEvent.setup();
    render(<UploadBaseSheet open onCreated={vi.fn()} />);

    const arquivos = Array.from({ length: 51 }, (_, i) => md(`doc${i}.md`));
    await user.upload(screen.getByLabelText(/arquivos/i), arquivos);
    await user.click(screen.getByRole("button", { name: /enviar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/50|limite/i);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("rejeita extensão diferente de .md sem chamar o backend", async () => {
    // SPECSFY: US-002 FR-004 AC-007 (SPEC-0013)
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 201 }),
    );
    const user = userEvent.setup();
    render(<UploadBaseSheet open onCreated={vi.fn()} />);

    await user.upload(screen.getByLabelText(/arquivos/i), [
      new File(["x"], "nota.txt", { type: "text/plain" }),
    ]);
    await user.click(screen.getByRole("button", { name: /enviar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/\.md/i);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
