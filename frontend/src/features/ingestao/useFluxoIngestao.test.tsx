import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";

import { useFluxoIngestao } from "@/features/ingestao/useFluxoIngestao";

const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });
const md = (nome: string) => new File(["# T"], nome, { type: "text/markdown" });
const previa = {
  resumo: { documentos: 1, chunks: 2, tamanho_medio: 10 }, avisos: [],
  arquivos_com_configuracao_propria: [], chunks: [], pagina: 1, total: 2,
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("useFluxoIngestao", () => {
  it("preserva arquivos e valores ao voltar e invalida a prévia quando algo muda", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-013 FR-014 NFR-004 AC-015 AC-017
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) =>
      String(url).endsWith("/padroes")
        ? json({ splitter: "header", chunk_size: 900, chunk_overlap: 100, splitters: ["header"], limites: { chunk_size: { min: 200, max: 4000 }, chunk_overlap: { min: 0, max_fracao: 0.5 } } })
        : json(previa),
    );
    const { result } = renderHook(() => useFluxoIngestao("ws-1"));
    await waitFor(() => expect(result.current.tamanho).toBe("900"));

    act(() => result.current.adicionarArquivos([md("a.md"), md("b.md"), md("a.md")]));
    act(() => result.current.ir("previa"));
    await act(() => result.current.calcularPrevia());
    expect(result.current.previa?.resumo.chunks).toBe(2);
    expect(result.current.arquivos.map((a) => a.name)).toEqual(["a.md", "b.md"]);
    expect(result.current.maisAlta).toBe(2);

    act(() => result.current.ir("divisao"));
    expect(result.current.arquivos).toHaveLength(2);
    act(() => result.current.alterarDivisao("tamanho", "800"));
    expect(result.current.previa).toBeNull();
    expect(result.current.tamanho).toBe("800");
    expect(result.current.pendente).toBe(true);
  });

  it("envia os arquivos e os parâmetros na prévia e na publicação, sem segredo", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-013 FR-014 NFR-004 AC-015 AC-017
    const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
      if (String(url).endsWith("/padroes")) return json({}, 500);
      if (String(url).endsWith("/envios")) return json({ envio_id: "e-1", colecao_id: "c-1" }, 201);
      return json(previa);
    });
    const { result } = renderHook(() => useFluxoIngestao("ws-1"));
    act(() => result.current.adicionarArquivos([md("a.md")]));
    await act(() => result.current.calcularPrevia(2, "a.md"));
    const resposta = await act(() =>
      result.current.publicar({ conexaoEmbeddingsId: "ce", conexaoVectorStoreId: "cq", novaColecao: "produtos" }),
    );

    const [, previaInit] = spy.mock.calls.find(([u]) => String(u).endsWith("/previa")) as [string, RequestInit];
    const corpoPrevia = previaInit.body as FormData;
    expect(corpoPrevia.get("pagina")).toBe("2");
    expect(corpoPrevia.get("documento")).toBe("a.md");
    expect(corpoPrevia.getAll("arquivos")).toHaveLength(1);
    const [, baseInit] = spy.mock.calls.find(([u]) => String(u).endsWith("/envios")) as [string, RequestInit];
    const corpoBase = baseInit.body as FormData;
    expect(corpoBase.get("workspace_id")).toBe("ws-1");
    expect(corpoBase.get("nova_colecao")).toBe("produtos");
    expect(corpoBase.get("conexao_embeddings_id")).toBe("ce");
    expect(corpoBase.get("sync_mode")).toBeNull();
    expect(JSON.parse(String(corpoBase.get("processamento"))).destino).toEqual({ batch_size: 50 });
    expect(resposta).toEqual({ envio_id: "e-1", colecao_id: "c-1" });
  });
});
