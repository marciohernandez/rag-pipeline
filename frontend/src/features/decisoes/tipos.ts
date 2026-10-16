/**
 * Tipos e rótulos da decisão da empresa (SPEC-0039). A API devolve valores técnicos; a
 * interface mostra sempre o rótulo em português.
 */

export type SituacaoProposta =
  | "clara"
  | "incerta"
  | "sem_decisao"
  | "aceita"
  | "editada"
  | "mantida";

export interface PropostaCorrecao {
  id: string;
  ocorrencia_id: string | null;
  situacao: SituacaoProposta | string;
  arquivo: string | null;
  documento_id?: string | null;
  trecho_alvo: string;
  texto_corrigido: string;
  motivo: string | null;
}

export interface RespostaEmpresa {
  id: string;
  situacao: "em_andamento" | "concluida" | "incompleta";
  motivo: string | null;
}

export interface PropostasApi {
  resposta: RespostaEmpresa | null;
  propostas: PropostaCorrecao[];
}

export interface Rodada {
  resolvidas: number;
  novas: number;
  abertas: number;
  revisada_em?: string | null;
}

export interface VersaoDoDocumento {
  numero: number;
  hash: string;
  criado_em: string;
  expira_em: string | null;
  atual: boolean;
}

export type AcaoDecisao = "aceitar" | "editar" | "manter";

export interface LocalManual {
  arquivo: string;
  trecho_alvo: string;
}

export const APLICADAS = ["aceita", "editada"];

export function plural(quantidade: number, singular: string, pluralTexto: string): string {
  return `${quantidade} ${quantidade === 1 ? singular : pluralTexto}`;
}
