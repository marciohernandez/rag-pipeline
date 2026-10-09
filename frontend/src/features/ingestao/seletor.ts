/**
 * Classe do select nativo legível nos dois temas (SPEC-0029, FR-011): o
 * navegador desenha a lista de opções com fundo próprio, então as opções usam
 * as cores de popover do tema em vez de herdar um fundo transparente.
 */
export const seletor =
  "h-8 w-full rounded-lg border border-input bg-background px-2.5 py-1 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 [&_option]:bg-popover [&_option]:text-popover-foreground";
