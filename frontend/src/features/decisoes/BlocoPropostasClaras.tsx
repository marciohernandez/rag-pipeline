"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PropostaCorrecao } from "@/features/decisoes/tipos";

interface BlocoPropostasClarasProps {
  propostas: PropostaCorrecao[];
  onConfirmar: () => void;
  ocupado?: boolean;
  somenteLeitura?: boolean;
}

/**
 * Bloco pré-aprovado das propostas claras (SPEC-0039, FR-003): nada muda no documento até a
 * pessoa clicar em "Confirmar todas".
 */
export default function BlocoPropostasClaras({
  propostas,
  onConfirmar,
  ocupado,
  somenteLeitura,
}: BlocoPropostasClarasProps) {
  if (propostas.length === 0) return null;
  return (
    <section
      aria-labelledby="titulo-propostas-claras"
      className="flex min-w-0 flex-col gap-3 rounded-lg border bg-card p-4"
    >
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h3 id="titulo-propostas-claras" className="text-base font-medium">
          Propostas claras <Badge variant="secondary">{propostas.length}</Badge>
        </h3>
        {somenteLeitura ? null : (
          <Button type="button" onClick={onConfirmar} disabled={ocupado} aria-busy={ocupado}>
            Confirmar todas
          </Button>
        )}
      </header>
      <ul className="flex min-w-0 flex-col gap-3">
        {propostas.map((proposta) => (
          <li key={proposta.id} className="flex min-w-0 flex-col gap-1">
            <span className="break-words text-sm font-medium">{proposta.arquivo}</span>
            <p className="break-words rounded-md bg-muted p-3 text-sm [overflow-wrap:anywhere]">
              {proposta.trecho_alvo}
            </p>
            <p className="break-words text-sm [overflow-wrap:anywhere]">
              <span className="text-muted-foreground">Passa a ser: </span>
              {proposta.texto_corrigido}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
