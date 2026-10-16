"use client";

import { useCallback, useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import type { VersaoDoDocumento } from "@/features/decisoes/tipos";
import { ApiError, apiJson } from "@/lib/api-client";

interface VersoesDocumentoSheetProps {
  open: boolean;
  colecaoId: string;
  documento: { id: string; nome_arquivo: string };
  podeEscrever: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onRestaurada?: () => void;
}

const MENSAGEM_FALHA = "Não foi possível voltar a esta versão. Tente novamente.";

/**
 * Painel lateral com as versões de um documento e a volta a uma versão anterior com
 * confirmação (SPEC-0039, FR-005 / FR-008). O member só consulta.
 */
export default function VersoesDocumentoSheet({
  open,
  colecaoId,
  documento,
  podeEscrever,
  onOpenChange,
  onRestaurada,
}: VersoesDocumentoSheetProps) {
  const [versoes, setVersoes] = useState<VersaoDoDocumento[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [alvo, setAlvo] = useState<VersaoDoDocumento | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [tentativa, setTentativa] = useState(0);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/documentos/${encodeURIComponent(documento.id)}/versoes`;

  useEffect(() => {
    if (!open) return;
    let ativo = true;
    apiJson<VersaoDoDocumento[]>(base)
      .then((lidas) => {
        if (ativo) setVersoes(lidas);
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar as versões. Tente novamente.");
      });
    return () => {
      ativo = false;
    };
  }, [base, open, tentativa]);

  const recarregar = useCallback(() => {
    setErro(null);
    setVersoes(null);
    setTentativa((n) => n + 1);
  }, []);

  async function restaurar() {
    if (!alvo || enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      await apiJson(`${base}/${alvo.numero}/restaurar`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ confirmado: true }),
      });
      setAlvo(null);
      recarregar();
      onRestaurada?.();
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Versões de {documento.nome_arquivo}</SheetTitle>
            <SheetDescription>
              Cada correção cria uma versão nova e preserva a anterior por 90 dias.
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-w-0 flex-col gap-3 px-4 pb-4">
            {erro ? (
              <Alert variant="destructive">
                <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
                  <span>{erro}</span>
                  <Button type="button" variant="outline" size="sm" onClick={recarregar}>
                    Tentar novamente
                  </Button>
                </AlertDescription>
              </Alert>
            ) : null}
            {versoes === null && !erro ? <Skeleton aria-busy="true" className="h-16 w-full" /> : null}
            {versoes && versoes.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Este documento ainda não foi corrigido: não há versões anteriores.
              </p>
            ) : null}
            <ul className="flex min-w-0 flex-col gap-2">
              {(versoes ?? []).map((versao) => (
                <li
                  key={versao.numero}
                  className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex min-w-0 flex-col">
                    <span className="text-sm font-medium">
                      Versão {versao.numero}{" "}
                      {versao.atual ? <Badge variant="secondary">Atual</Badge> : null}
                    </span>
                    <span className="break-words text-xs text-muted-foreground">
                      {new Date(versao.criado_em).toLocaleString("pt-BR")}
                    </span>
                  </div>
                  {podeEscrever && !versao.atual ? (
                    <Button type="button" variant="outline" size="sm" onClick={() => setAlvo(versao)}>
                      Voltar a esta versão
                    </Button>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        </SheetContent>
      </Sheet>
      <Dialog open={alvo !== null} onOpenChange={(valor) => !valor && !enviando && setAlvo(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Voltar à versão {alvo?.numero}?</DialogTitle>
            <DialogDescription>
              A versão {alvo?.numero} de {documento.nome_arquivo} passa a ser a atual, como uma
              versão nova, e o documento é publicado de novo na coleção. A volta fica no registro.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setAlvo(null)} disabled={enviando}>
              Cancelar
            </Button>
            <Button type="button" onClick={restaurar} disabled={enviando} aria-busy={enviando}>
              Confirmar e voltar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
