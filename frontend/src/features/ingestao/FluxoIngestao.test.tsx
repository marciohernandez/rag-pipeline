import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Modulo = { default: ComponentType<{ workspaceId: string }> };

const owner = {
  id: "pessoa-owner", nome: "Pessoa de teste", email: "owner@exemplo.com", papel: "owner" as const,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
};
const padroes = {
  splitter: "header", chunk_size: 1000, chunk_overlap: 200,
  limites: { chunk_size: { min: 200, max: 4000 }, chunk_overlap: { min: 0, max_fracao: 0.5 } },
};
const previa = {
  resumo: { documentos: 2, chunks: 6, tamanho_medio: 420 },
  avisos: [], arquivos_com_configuracao_propria: [], pagina: 1, total: 6,
  chunks: [{ documento: "a.md", posicao: 0, tamanho: 400, texto: "Texto do chunk" }],
};
const md = (nome: string) => new File(["# Título\n\nConteúdo útil."], nome, { type: "text/markdown" });
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

function simularApi() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/ingestao/padroes")) return json(padroes);
    if (url.endsWith("/api/v1/ingestao/previa")) return json(previa);
    if (url.includes("/api/v1/conexoes")) return json([]);
    throw new Error(`URL inesperada: ${url}`);
  });
}

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-owner", owner);
  push.mockReset();
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("FluxoIngestao", () => {
  it("percorre as etapas preservando arquivos e valores ao voltar", async () => {
    // SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015
    const { default: FluxoIngestao } = await exigir<Modulo>("@/features/ingestao/FluxoIngestao");
    simularApi();
    const user = userEvent.setup();
    render(<FluxoIngestao workspaceId="workspace-1" />);

    await user.upload(screen.getByLabelText(/arquivos/i), [md("a.md"), md("b.md")]);
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    const titulo = await screen.findByRole("heading", { name: /divisão/i });
    await waitFor(() => expect(titulo).toHaveFocus());

    const tamanho = screen.getByLabelText(/tamanho do chunk/i);
    await user.clear(tamanho);
    await user.type(tamanho, "5000");
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    expect(await screen.findByText(/máximo de 4000/i)).toBeInTheDocument();
    expect(tamanho).toHaveFocus();

    await user.clear(tamanho);
    await user.type(tamanho, "800");
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    expect(await screen.findByRole("heading", { name: /prévia/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /voltar/i }));

    expect(await screen.findByLabelText(/tamanho do chunk/i)).toHaveValue(800);
    await user.click(screen.getByRole("button", { name: /voltar/i }));
    expect(screen.getByText("a.md")).toBeInTheDocument();
    expect(screen.getByText("b.md")).toBeInTheDocument();
  });

  it("avisa antes de sair com alterações pendentes", async () => {
    // SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015
    const { default: FluxoIngestao } = await exigir<Modulo>("@/features/ingestao/FluxoIngestao");
    simularApi();
    const user = userEvent.setup();
    render(<FluxoIngestao workspaceId="workspace-1" />);

    await user.upload(screen.getByLabelText(/arquivos/i), [md("a.md")]);
    const evento = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(evento);

    expect(evento.defaultPrevented).toBe(true);
  });

  it("mantém Próxima desabilitada sem arquivos e oferece a base preparada", async () => {
    // SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015
    const { default: FluxoIngestao } = await exigir<Modulo>("@/features/ingestao/FluxoIngestao");
    simularApi();
    render(<FluxoIngestao workspaceId="workspace-1" />);

    expect(screen.getByRole("button", { name: /próxima/i })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: /usar base preparada/i })).toBeInTheDocument();
  });
});

describe("FluxoIngestao — saída da página (SPEC-0026)", () => {
  it("pede confirmação ao seguir um link interno com alterações pendentes e respeita a recusa", async () => {
    // SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015
    const { default: FluxoIngestao } = await exigir<Modulo>("@/features/ingestao/FluxoIngestao");
    simularApi();
    const confirmar = vi.spyOn(window, "confirm").mockReturnValue(false);
    const navegou = vi.fn((e: Event) => {
      if ((e.target as HTMLElement).closest("a")) e.preventDefault();
    });
    document.addEventListener("click", navegou);
    const user = userEvent.setup();
    render(
      <>
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- âncora simples para observar o clique */}
        <a href="/pessoas">Pessoas</a>
        <FluxoIngestao workspaceId="workspace-1" />
      </>,
    );

    await user.upload(screen.getByLabelText(/arquivos/i), [md("a.md")]);
    await user.click(screen.getByRole("link", { name: "Pessoas" }));

    expect(confirmar).toHaveBeenCalledTimes(1);
    expect(navegou).toHaveBeenCalledTimes(1);
    document.removeEventListener("click", navegou);
  });
});
