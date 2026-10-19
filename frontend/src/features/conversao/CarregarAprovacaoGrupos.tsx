"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import AprovacaoGrupos, { type PropostaDeGrupos } from "@/features/conversao/AprovacaoGrupos";
import { apiJson } from "@/lib/api-client";

interface CarregarAprovacaoGruposProps {
  loteId: string;
  podeEscrever: boolean;
  onConfirmada?: () => void;
}

/** Busca a proposta de grupos do lote e mostra o passo de aprovação (SPEC-0040). */
export default function CarregarAprovacaoGrupos({
  loteId,
  podeEscrever,
  onConfirmada,
}: CarregarAprovacaoGruposProps) {
  const [proposta, setProposta] = useState<PropostaDeGrupos | null>(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    let ativo = true;
    apiJson<PropostaDeGrupos>(`/api/v1/conversoes/${encodeURIComponent(loteId)}/grupos`)
      .then((lida) => {
        if (ativo) setProposta(lida);
      })
      .catch(() => {
        if (ativo) setErro(true);
      });
    return () => {
      ativo = false;
    };
  }, [loteId]);

  if (erro) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Não foi possível carregar os grupos. Tente novamente.</AlertDescription>
      </Alert>
    );
  }
  if (!proposta) return <Skeleton aria-busy="true" className="h-24 w-full" />;
  return <AprovacaoGrupos loteId={loteId} proposta={proposta} podeEscrever={podeEscrever} onConfirmada={onConfirmada} />;
}
