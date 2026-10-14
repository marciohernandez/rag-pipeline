/**
 * Rótulos e variantes de `Badge` das situações de conversão (SPEC-0023, FR-009).
 *
 * A API devolve valores técnicos (`concluido`, `concluido_com_falhas`); a interface
 * mostra sempre o rótulo em português e nunca o valor cru.
 */

export type VarianteSituacao = "default" | "secondary" | "destructive" | "outline";

export const SITUACOES_ATIVAS = ["fila", "processando"];

const ROTULOS: Record<string, string> = {
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
