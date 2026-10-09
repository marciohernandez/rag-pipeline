"use client";

import { useEffect, useState } from "react";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChunkDoDocumento } from "@/features/colecoes/tipos";
import { apiJson } from "@/lib/api-client";

/**
 * Painel lateral, somente leitura, com os chunks de um documento (SPEC-0030, FR-008).
 * Mostra até 200 chunks; carregando, vazio e erro têm estado próprio.
 */

interface ChunksDocumentoSheetProps {
  open: boolean;
  colecaoId: string;
  documento: { id: string; nome_arquivo: string };
  onOpenChange?: (open: boolean) => void;
}

export default function ChunksDocumentoSheet({
  open,
  colecaoId,
  documento,
  onOpenChange,
}: ChunksDocumentoSheetProps) {
  const [chunks, setChunks] = useState<ChunkDoDocumento[] | null>(null);
  const [erro, setErro] = useState(false);
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let ativo = true;
    apiJson<ChunkDoDocumento[]>(
      `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/documentos/${encodeURIComponent(documento.id)}/chunks?limite=200`,
    )
      .then((lidos) => {
        if (ativo) setChunks(lidos);
      })
      .catch(() => {
        if (ativo) setErro(true);
      });
    return () => {
      ativo = false;
    };
  }, [colecaoId, documento.id, tentativa]);

  function tentarDeNovo() {
    setErro(false);
    setChunks(null);
    setTentativa((valor) => valor + 1);
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="[overflow-wrap:anywhere]">Chunks de {documento.nome_arquivo}</SheetTitle>
          <SheetDescription>Somente leitura. Para mudar o conteúdo, substitua o arquivo.</SheetDescription>
        </SheetHeader>

        <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 pb-4">
          {erro ? (
            <Alert variant="destructive">
              <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
                <span>Não foi possível ler os chunks do documento.</span>
                <Button type="button" variant="outline" size="sm" onClick={tentarDeNovo}>
                  Tentar novamente
                </Button>
              </AlertDescription>
            </Alert>
          ) : chunks === null ? (
            <div aria-busy="true" className="flex flex-col gap-3">
              <IndicadorProcessamento>Carregando chunks…</IndicadorProcessamento>
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : chunks.length === 0 ? (
            <p className="text-sm text-muted-foreground">Este documento não tem chunks.</p>
          ) : (
            <ol className="flex flex-col gap-3">
              {chunks.map((chunk, indice) => (
                <li key={chunk.chunk_id ?? indice} className="rounded-md border p-3 text-sm">
                  <p className="text-xs text-muted-foreground [overflow-wrap:anywhere]">
                    {indice + 1}. {chunk.secao || "Sem seção"}
                  </p>
                  <p className="mt-1 whitespace-pre-wrap [overflow-wrap:anywhere]">{chunk.texto}</p>
                </li>
              ))}
            </ol>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
