import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
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

describe("FluxoIngestao — barra de ações da Prévia (SPEC-0029)", () => {
  async function irParaPrevia(fetchMock?: ReturnType<typeof simularApi>) {
    const { default: FluxoIngestao } = await exigir<Modulo>("@/features/ingestao/FluxoIngestao");
    const espiao = fetchMock ?? simularApi();
    const user = userEvent.setup();
    render(<FluxoIngestao workspaceId="workspace-1" />);
    await user.upload(screen.getByLabelText(/arquivos/i), [md("a.md"), md("b.md")]);
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    await screen.findByRole("heading", { name: /divisão/i });
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    await screen.findByRole("heading", { name: /prévia/i });
    return { user, espiao };
  }

  function camposDaUltimaPrevia(espiao: ReturnType<typeof simularApi>) {
    const chamadas = espiao.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/ingestao/previa"));
    const corpo = chamadas.at(-1)?.[1]?.body as FormData;
    return corpo;
  }

  it("mantém as ações da Prévia no topo", async () => {
    // SPECSFY: SPEC-0029 US-004 FR-007 FR-008 NFR-003 AC-016
    await irParaPrevia();

    const barra = screen.getByRole("toolbar", { name: /ações da prévia/i });
    expect(barra.className).toMatch(/sticky/);
    expect(within(barra).getByRole("button", { name: /voltar/i })).toBeInTheDocument();
    expect(within(barra).getByRole("button", { name: /próxima/i })).toBeInTheDocument();
    expect(within(barra).getByLabelText(/chunks por página/i)).toBeInTheDocument();
    const lista = await screen.findByRole("list", { name: /chunks da prévia/i });
    expect(barra.compareDocumentPosition(lista) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("preserva filtro e escolhas ao trocar o tamanho da página", async () => {
    // SPECSFY: SPEC-0029 US-004 FR-007 FR-008 AC-018
    const { user, espiao } = await irParaPrevia();
    await user.selectOptions(await screen.findByLabelText(/filtrar por documento/i), "a.md");
    const tamanho = screen.getByLabelText(/chunks por página/i) as HTMLSelectElement;

    expect(Array.from(tamanho.options).map((o) => o.value)).toEqual(["10", "20", "50", "75", "100"]);
    await user.selectOptions(tamanho, "100");

    await waitFor(() => expect(camposDaUltimaPrevia(espiao).get("tamanho_pagina")).toBe("100"));
    const corpo = camposDaUltimaPrevia(espiao);
    expect(corpo.get("pagina")).toBe("1");
    expect(corpo.get("documento")).toBe("a.md");
    await user.click(screen.getAllByRole("button", { name: /voltar/i })[0]);
    expect(await screen.findByLabelText(/tamanho do chunk/i)).toHaveValue(1000);
  });
});

describe("FluxoIngestao — origem no lote de conversão (SPEC-0043)", () => {
  it("abre com os documentos do lote listados e envia lote_id e documento_ids, sem arquivo", async () => {
    // SPECSFY: SPEC-0043 US-002 FR-003 FR-004 AC-005
    const { default: FluxoIngestao } = await exigir<{
      default: ComponentType<{ workspaceId: string; loteInicial?: { id: string; documentoIds: string[] } }>;
    }>("@/features/ingestao/FluxoIngestao");
    const chamadas: Array<[string, RequestInit | undefined]> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      chamadas.push([url, init]);
      if (url.endsWith("/api/v1/ingestao/padroes")) return json(padroes);
      if (url.endsWith("/api/v1/ingestao/previa")) return json(previa);
      if (url.endsWith("/api/v1/conversoes/lote-1")) {
        return json({
          id: "lote-1", workspace_id: "workspace-1", situacao: "concluido", criado_em: "2026-10-22T10:00:00Z",
          documentos: [
            { id: "d1", nome_arquivo: "a.pdf", situacao: "concluido", formato: "pdf" },
            { id: "d2", nome_arquivo: "b.pdf", situacao: "concluido", formato: "pdf" },
          ],
        });
      }
      if (url.includes("/api/v1/conexoes")) return json([]);
      throw new Error(`URL inesperada: ${url}`);
    });
    const user = userEvent.setup();
    render(<FluxoIngestao workspaceId="workspace-1" loteInicial={{ id: "lote-1", documentoIds: ["d1", "d2"] }} />);

    expect(await screen.findByText("a.md")).toBeInTheDocument();
    expect(screen.getByText("b.md")).toBeInTheDocument();
    expect(screen.queryByLabelText(/arquivos/i)).not.toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: /próxima/i }));
    await user.click(await screen.findByRole("button", { name: /próxima/i }));

    const chamadaPrevia = await waitFor(() => {
      const achada = chamadas.find(([url]) => url.endsWith("/api/v1/ingestao/previa"));
      expect(achada).toBeDefined();
      return achada!;
    });
    const corpo = chamadaPrevia[1]?.body as FormData;
    expect(corpo.get("lote_id")).toBe("lote-1");
    expect(corpo.getAll("documento_ids")).toEqual(["d1", "d2"]);
    expect(corpo.getAll("arquivos")).toHaveLength(0);
  });
});
