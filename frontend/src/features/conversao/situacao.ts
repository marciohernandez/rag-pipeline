/**
 * Rótulos e variantes de `Badge` das situações de conversão (SPEC-0023, FR-009).
 *
 * A API devolve valores técnicos (`concluido`, `concluido_com_falhas`); a interface
 * mostra sempre o rótulo em português e nunca o valor cru.
 */

export type VarianteSituacao = "default" | "secondary" | "destructive" | "outline";

export const SITUACOES_ATIVAS = ["fila", "processando"];

export interface AvisoConversao {
  codigo: string;
  pagina: number | null;
  mensagem: string;
}

const ROTULOS_AVISO: Record<string, string> = {
  ocr_pouco_texto: "Pouco texto reconhecido",
  ocr_limite_de_paginas: "Limite de páginas atingido",
  ocr_falhou: "Falha na leitura por OCR",
  ocr_sem_texto_reconhecido: "Nenhum texto reconhecido na imagem",
};

export function motivoAviso(aviso: AvisoConversao): string {
  const motivo = aviso.mensagem || ROTULOS_AVISO[aviso.codigo] || "Confira o documento original";
  return aviso.pagina === null ? motivo : `Página ${aviso.pagina}: ${motivo}`;
}

const ROTULOS: Record<string, string> = {
  aguardando_abas: "Aguardando abas",
  fila: "Na fila",
  processando: "Processando",
  concluido: "Convertido",
  falhou: "Falhou",
  concluido_com_falhas: "Concluído com falhas",
};

export function rotuloSituacao(situacao: string, tipo: "documento" | "lote" = "documento"): string {
  if (tipo === "lote" && situacao === "concluido") return "Concluído";
  return ROTULOS[situacao] ?? situacao;
}

export function variantePorSituacao(situacao: string): VarianteSituacao {
  if (situacao === "concluido") return "default";
  if (situacao === "falhou" || situacao === "concluido_com_falhas") return "destructive";
  if (SITUACOES_ATIVAS.includes(situacao)) return "secondary";
  return "outline";
}
