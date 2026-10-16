"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { plural } from "@/features/decisoes/tipos";
import { ApiError, apiJson } from "@/lib/api-client";

const MENSAGEM_FALHA = "Não foi possível liberar a coleção. Tente novamente.";

interface LiberarColecaoDialogProps {
  open: boolean;
  onOpenChange?: (aberto: boolean) => void;
  colecaoId: string;
  abertas: number;
  onLiberada?: () => void;
}

/**
 * Confirmação de "Liberar para a base" (SPEC-0039, FR-007 / NFR-004): marca a coleção como
 * revisada. Com contradições abertas o aviso exige a confirmação explícita.
 */
export default function LiberarColecaoDialog({
  open,
  onOpenChange,
  colecaoId,
  abertas,
  onLiberada,
}: LiberarColecaoDialogProps) {
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function aoMudarAbertura(valor: boolean) {
    if (enviando) return;
    if (!valor) setErro(null);
    onOpenChange?.(valor);
  }

  async function liberar() {
    if (enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      await apiJson(`/api/v1/colecoes/${encodeURIComponent(colecaoId)}/revisar`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ confirmado: true }),
      });
      onOpenChange?.(false);
      onLiberada?.();
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={aoMudarAbertura}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Liberar a coleção para a base?</DialogTitle>
          <DialogDescription>
            {abertas > 0
              ? `Há ${plural(abertas, "contradição aberta", "contradições abertas")}. Você pode liberar mesmo assim: a coleção fica marcada como revisada, com o seu nome e a data.`
              : "A coleção fica marcada como revisada, com o seu nome e a data. A consulta e os envios continuam funcionando."}
          </DialogDescription>
        </DialogHeader>
        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => aoMudarAbertura(false)}
            disabled={enviando}
          >
            Cancelar
          </Button>
          <Button type="button" onClick={liberar} disabled={enviando} aria-busy={enviando}>
            {abertas > 0 ? "Liberar mesmo assim" : "Liberar para a base"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
