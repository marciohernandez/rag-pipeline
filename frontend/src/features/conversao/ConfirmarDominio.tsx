"use client";

import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import FormularioDominio from "@/features/workspaces/FormularioDominio";
import { apiJson } from "@/lib/api-client";

/**
 * Passo de confirmação do domínio dentro do lote (SPEC-0037, FR-003): mostra a proposta da
 * IA, permite editar e, ao confirmar, libera a limpeza do lote.
 */
export default function ConfirmarDominio({
  loteId,
  onConfirmado,
}: {
  loteId: string;
  onConfirmado: (lote: LoteConversaoResumo) => void;
}) {
  const [proposta, setProposta] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    apiJson<{ texto: string }>(`/api/v1/conversoes/${loteId}/dominio-proposto`)
      .then((r) => {
        if (!cancelado) setProposta(r?.texto ?? "");
      })
      .catch(() => {
        if (!cancelado) setProposta("");
      });
    return () => {
      cancelado = true;
    };
  }, [loteId]);

  if (proposta === null) return <Skeleton aria-busy="true" className="h-24 w-full" />;
  return (
    <FormularioDominio
      idCampo="confirmar-dominio"
      valorInicial={proposta}
      rotuloSalvar="Confirmar domínio"
      mensagemSucesso="Domínio confirmado; a limpeza vai começar."
      onSalvar={async (texto) => {
        const lote = await apiJson<LoteConversaoResumo>(
          `/api/v1/conversoes/${loteId}/dominio/confirmar`,
          {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ texto }),
          },
        );
        onConfirmado(lote);
      }}
    />
  );
}
