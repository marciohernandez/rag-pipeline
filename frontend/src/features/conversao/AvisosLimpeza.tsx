"use client";

import Link from "next/link";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface AvisosLimpezaProps {
  workspaceId: string;
  iaPermitida: boolean;
  dominioConfirmado: boolean;
  onConfirmarDominio?: () => void;
}

/**
 * Avisos do painel do lote sobre a limpeza de conteúdo (SPEC-0037, FR-008).
 *
 * IA externa desligada: a limpeza segue só com as regras fixas. Domínio não
 * confirmado: a limpeza não começa. Sem nenhum dos dois, nada é exibido.
 */
export default function AvisosLimpeza({
  workspaceId,
  iaPermitida,
  dominioConfirmado,
  onConfirmarDominio,
}: AvisosLimpezaProps) {
  if (iaPermitida && dominioConfirmado) return null;
  return (
    <Alert role="status" aria-live="polite" className="min-w-0 [overflow-wrap:anywhere]">
      <AlertDescription className="flex flex-col gap-2">
        {!dominioConfirmado ? (
          <span>
            A limpeza não começa até o domínio da empresa ser confirmado. Revise o resumo e
            confirme para continuar.
          </span>
        ) : null}
        {!iaPermitida ? (
          <span>
            A análise por IA externa está desligada neste Workspace: a limpeza seguirá somente as
            regras fixas.
          </span>
        ) : null}
        <span className="flex flex-wrap items-center gap-2">
          {!dominioConfirmado ? (
            <Button type="button" size="sm" onClick={onConfirmarDominio}>
              Confirmar domínio
            </Button>
          ) : null}
          <Link
            href={`/workspaces/${workspaceId}#dominio-da-empresa`}
            className="text-sm underline underline-offset-2"
          >
            Domínio da empresa
          </Link>
        </span>
      </AlertDescription>
    </Alert>
  );
}
