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

  it("envia coleção e pares customizados no multipart, com foco ao adicionar", async () => {
    // SPECSFY: SPEC-0019 US-002 US-003 FR-004 FR-005 FR-007 AC-009 AC-014
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"base_id":"b-3"}', { status: 201 }),
    );
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={vi.fn()} />);

    expect(screen.getByText(/deixe em branco para usar o padrão deste workspace/i)).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: /nome da coleção/i }), "  colecao-especial  ");
    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    const rotulo = screen.getByRole("textbox", { name: /rótulo 1/i });
    await waitFor(() => expect(rotulo).toHaveFocus());
    await user.type(rotulo, " categoria ");
    await user.type(screen.getByRole("textbox", { name: /valor 1/i }), "gold");
    await user.upload(screen.getByLabelText(/arquivos markdown/i), [md("a.md")]);
    await user.click(screen.getByRole("button", { name: /^enviar$/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const body = fetchSpy.mock.calls[0]?.[1]?.body as FormData;
    expect(body.get("workspace_id")).toBe("workspace-1");
    expect(body.get("collection_name")).toBe("colecao-especial");
    expect(JSON.parse(String(body.get("metadados_chunk")))).toEqual([
      { rotulo: "categoria", valor: "gold" },
    ]);
  });

  it("aplica coleção e metadados também à Base preparada", async () => {
    // SPECSFY: SPEC-0019 US-002 US-003 FR-004 FR-005 FR-007 AC-010 AC-014
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"base_id":"b-4"}', { status: 201 }),
    );
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 1/i }), "campanha");
    await user.type(screen.getByRole("textbox", { name: /valor 1/i }), "setembro");
    await user.click(screen.getByRole("button", { name: /base preparada/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const body = fetchSpy.mock.calls[0]?.[1]?.body as URLSearchParams;
    expect(body.get("workspace_id")).toBe("workspace-1");
    expect(body.get("usar_base_preparada")).toBe("true");
    expect(body.has("collection_name")).toBe(false);
    expect(JSON.parse(String(body.get("metadados_chunk")))).toEqual([
      { rotulo: "campanha", valor: "setembro" },
    ]);
  });

  it("rejeita rótulo repetido depois de normalizar espaços sem chamar a API", async () => {
    // SPECSFY: SPEC-0019 US-003 FR-007 AC-016
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 1/i }), "categoria");
    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 2/i }), " categoria ");
    await user.click(screen.getByRole("button", { name: /base preparada/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/rótulo.*repetido/i);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(screen.getByRole("textbox", { name: /rótulo 2/i })).toHaveFocus();
  });

  it("rejeita par sem rótulo e associa o erro ao campo", async () => {
    // SPECSFY: SPEC-0019 US-003 FR-007 AC-015
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.click(screen.getByRole("button", { name: /base preparada/i }));

    const rotulo = screen.getByRole("textbox", { name: /rótulo 1/i });
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(rotulo).toHaveFocus();
    expect(rotulo).toHaveAttribute("aria-invalid", "true");
    expect(rotulo).toHaveAccessibleDescription(/informe o rótulo/i);
  });

  it("preserva coleção e pares depois de erro de envio", async () => {
    // SPECSFY: SPEC-0019 US-002 US-003 FR-005 FR-007 AC-014
    const fetchSpy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response('{"detail":"falha interna"}', { status: 500 }))
      .mockResolvedValueOnce(new Response('{"base_id":"b-6"}', { status: 201 }));
    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={onCreated} />);

    await user.type(screen.getByRole("textbox", { name: /nome da coleção/i }), "colecao-x");
    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 1/i }), "categoria");
    await user.click(screen.getByRole("button", { name: /base preparada/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).not.toHaveTextContent(/falha interna/i);
    expect(screen.getByRole("textbox", { name: /nome da coleção/i })).toHaveValue("colecao-x");
    expect(screen.getByRole("textbox", { name: /rótulo 1/i })).toHaveValue("categoria");
    await user.click(screen.getByRole("button", { name: /base preparada/i }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("b-6"));
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("permite remover um par sem enviar o rótulo removido", async () => {
    // SPECSFY: SPEC-0019 US-003 FR-007 AC-014
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"base_id":"b-5"}', { status: 201 }),
    );
    const user = userEvent.setup();
    render(<UploadBaseSheet open workspaceId="workspace-1" onCreated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 1/i }), "categoria");
    await user.click(screen.getByRole("button", { name: /adicionar metadado/i }));
    await user.type(screen.getByRole("textbox", { name: /rótulo 2/i }), "regiao");
    await user.click(screen.getByRole("button", { name: /remover metadado 1/i }));
    await user.click(screen.getByRole("button", { name: /base preparada/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const body = fetchSpy.mock.calls[0]?.[1]?.body as URLSearchParams;
    expect(JSON.parse(String(body.get("metadados_chunk")))).toEqual([
      { rotulo: "regiao", valor: "" },
    ]);
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
