import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import { apiFetch, apiJson } from "@/lib/api-client";

/**
 * Ações de um documento de conversão compartilhadas entre a linha da lista e o
 * painel do lote (SPEC-0023, FR-005 / FR-006 / FR-009).
 */

export async function baixar(caminho: string, nomeArquivo: string) {
  const resposta = await apiFetch(caminho);
  const blob = await resposta.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeArquivo;
  link.click();
  URL.revokeObjectURL(url);
}

export async function baixarMarkdown(loteId: string, documentoId: string, nomeArquivo: string) {
  const nomeBase = nomeArquivo.replace(/\.[^.]+$/, "");
  await baixar(`/api/v1/conversoes/${loteId}/documentos/${documentoId}/markdown`, `${nomeBase}.md`);
}

export async function reenviarDocumento(
  loteId: string,
  documentoId: string,
): Promise<LoteConversaoResumo> {
  await apiJson(`/api/v1/conversoes/${loteId}/documentos/${documentoId}/reenviar`, {
    method: "POST",
  });
  return apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${loteId}`);
}
