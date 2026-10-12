/** Apoio dos testes da SPEC-0030: dados e respostas HTTP de coleções, sem rede. */
import { vi } from "vitest";

export const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

export const documentosExemplo = [
  { id: "doc-a", nome_arquivo: "a.md", chunks: 12, chunking: { splitter: "header" }, ultimo_envio_em: "2026-10-09T10:00:00Z" },
  { id: "doc-b", nome_arquivo: "b.md", chunks: 5, chunking: { splitter: "character_split" }, ultimo_envio_em: "2026-10-09T11:00:00Z" },
];

export const enviosExemplo = [
  {
    id: "env-1", arquivos: ["a.md"], processamento: { splitter: "header" }, situacao: "succeeded",
    previstos: 12, inseridos: 12, mantidos: 0, removidos: 0, erro: null,
    iniciado_em: "2026-10-09T10:00:00Z", concluido_em: "2026-10-09T10:01:00Z",
    criado_por: { id: "p1", nome: "Ana Souza", desativada: false },
  },
  {
    id: "env-2", arquivos: ["b.md"], processamento: { splitter: "character_split" }, situacao: "succeeded",
    previstos: 5, inseridos: 5, mantidos: 0, removidos: 0, erro: null,
    iniciado_em: "2026-10-09T11:00:00Z", concluido_em: "2026-10-09T11:01:00Z",
    criado_por: { id: "p1", nome: "Ana Souza", desativada: false },
  },
  {
    id: "env-3", arquivos: ["a.md"], processamento: { splitter: "recursive" }, situacao: "failed",
    previstos: 12, inseridos: 0, mantidos: 0, removidos: 0,
    erro: "Falha ao processar o envio; ver logs do worker para detalhes.",
    iniciado_em: "2026-10-09T12:00:00Z", concluido_em: "2026-10-09T12:01:00Z",
    criado_por: { id: "p1", nome: "Ana Souza", desativada: false },
  },
];

export function simularFetch(rotas: Record<string, () => Response>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const chave = `${init?.method ?? "GET"} ${String(input)}`;
    for (const [padrao, resposta] of Object.entries(rotas)) {
      if (new RegExp(padrao).test(chave)) return resposta();
    }
    throw new Error(`Requisição inesperada: ${chave}`);
  });
}
