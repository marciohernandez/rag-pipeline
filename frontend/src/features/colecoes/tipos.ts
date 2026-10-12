/** Tipos das respostas de coleções, documentos e envios (SPEC-0030, seção 10). */

export interface Autor {
  id: string;
  nome: string;
  desativada: boolean;
}

export interface ColecaoResumo {
  id: string;
  nome: string;
  documentos: number;
  chunks: number;
  ultimo_envio_em: string | null;
}

export interface ColecaoDetalhe {
  id: string;
  nome: string;
  workspace_id: string;
  workspace_nome: string;
  dimensao: number;
  conexao_embeddings: { id: string; nome: string };
  conexao_vector_store: { id: string; nome: string };
  documentos: number;
  chunks: number;
  criado_em: string;
  criado_por: Autor | null;
}

export interface DocumentoResumo {
  id: string;
  nome_arquivo: string;
  chunks: number;
  chunking: { splitter?: string } & Record<string, unknown>;
  ultimo_envio_em: string | null;
}

export interface ChunkDoDocumento {
  chunk_id: string;
  secao: string;
  texto: string;
}

export interface EnvioResumo {
  id: string;
  colecao_id?: string;
  arquivos: string[];
  processamento: { splitter?: string } & Record<string, unknown>;
  situacao: "queued" | "running" | "succeeded" | "failed" | string;
  etapa?: string;
  previstos: number;
  inseridos: number;
  mantidos: number;
  removidos: number;
  erro: string | null;
  iniciado_em: string;
  concluido_em: string | null;
  criado_por: Autor | null;
}

export interface EnvioDetalhe extends EnvioResumo {
  colecao: { id: string; nome: string; workspace_id: string };
}

export const rotulosSituacao: Record<string, string> = {
  queued: "Na fila",
  running: "Em processamento",
  succeeded: "Concluído",
  failed: "Falhou",
};

export function formatarData(iso: string | null): string {
  if (!iso) return "—";
  const data = new Date(iso);
  return Number.isNaN(data.getTime())
    ? iso
    : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function nomeDoAutor(autor: Autor | null | undefined): string {
  if (!autor) return "Autor não identificado";
  return `${autor.nome}${autor.desativada ? " (desativada)" : ""}`;
}
