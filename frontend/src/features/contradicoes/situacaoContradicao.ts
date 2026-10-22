/**
 * Rótulos e variantes de `Badge` das etiquetas e da situação da análise de contradições
 * (SPEC-0038, FR-004 / FR-007). A API devolve valores técnicos; a interface mostra sempre
 * o rótulo em português.
 */

export type VarianteBadge = "default" | "secondary" | "destructive" | "outline";

export type Etiqueta = "conflito" | "versao_desatualizada" | "duplicado";
export type SituacaoAnalise = "em_andamento" | "concluida" | "incompleta";

export interface TrechoOcorrencia {
  arquivo: string;
  texto: string;
  imagem?: string | null;
}

export interface Ocorrencia {
  id: string;
  assunto: string;
  etiqueta: Etiqueta;
  impacto: "alto" | "baixo";
  trechos: TrechoOcorrencia[];
  explicacao: string;
  arquivo_mais_antigo?: string | null;
}

export interface Analise {
  id: string;
  situacao: SituacaoAnalise;
  motivo: string | null;
  provedor: string | null;
  dominio_versao_id: string | null;
  total_assuntos: number;
  concluidos: number;
  documentos_analisados: number;
  avisos?: string[];
}

export interface RelatorioApi {
  analise: Analise | null;
  ocorrencias: Ocorrencia[];
  nao_classificadas: number;
}

export const ETIQUETAS: Etiqueta[] = ["conflito", "versao_desatualizada", "duplicado"];

const ROTULOS_ETIQUETA: Record<Etiqueta, string> = {
  conflito: "Conflito",
  versao_desatualizada: "Versão desatualizada",
  duplicado: "Duplicado",
};

const VARIANTES_ETIQUETA: Record<Etiqueta, VarianteBadge> = {
  conflito: "destructive",
  versao_desatualizada: "secondary",
  duplicado: "outline",
};

export function rotuloEtiqueta(etiqueta: Etiqueta): string {
  return ROTULOS_ETIQUETA[etiqueta] ?? etiqueta;
}

export function varianteEtiqueta(etiqueta: Etiqueta): VarianteBadge {
  return VARIANTES_ETIQUETA[etiqueta] ?? "outline";
}

/** Valores e prazos (impacto alto) primeiro; a ordem entre iguais é a alfabética do assunto. */
export function ordenarPorImpacto(itens: Ocorrencia[]): Ocorrencia[] {
  return [...itens].sort((a, b) => {
    if (a.impacto !== b.impacto) return a.impacto === "alto" ? -1 : 1;
    return a.assunto.localeCompare(b.assunto, "pt-BR");
  });
}
