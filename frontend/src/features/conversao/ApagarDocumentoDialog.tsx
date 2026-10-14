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
import { ApiError, apiFetch } from "@/lib/api-client";

/**
 * Confirmação de exclusão de um documento da lista de conversão (SPEC-0023, FR-010).
 *
 * Modelado em `ApagarColecaoDialog`, sem a digitação do nome: o impacto é um único
 * arquivo. Informa a consequência irreversível; em falha o diálogo continua aberto
 * com uma mensagem segura.
 */

const MENSAGEM_FALHA = "Não foi possível apagar o documento. Tente novamente.";

interface ApagarDocumentoDialogProps {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  loteId: string;
  documento: { id: string; nome_arquivo: string };
  onDeleted: (documentoId: string) => void;
}

export default function ApagarDocumentoDialog({
  open,
  onOpenChange,
  loteId,
  documento,
  onDeleted,
}: ApagarDocumentoDialogProps) {
  const [apagando, setApagando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function aoMudarAbertura(aberto: boolean) {
    if (apagando) return;
    if (!aberto) setErro(null);
    onOpenChange?.(aberto);
  }

  async function apagar() {
    if (apagando) return;
    setApagando(true);
    setErro(null);
    try {
      await apiFetch(
        `/api/v1/conversoes/${encodeURIComponent(loteId)}/documentos/${encodeURIComponent(documento.id)}`,
        { method: "DELETE" },
      );
      onDeleted(documento.id);
      onOpenChange?.(false);
    } catch (causa) {
      setErro(
        causa instanceof ApiError && causa.status === 409 && causa.detail ? causa.detail : MENSAGEM_FALHA,
      );
    } finally {
      setApagando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={aoMudarAbertura}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="[overflow-wrap:anywhere]">
            Apagar “{documento.nome_arquivo}”?
          </DialogTitle>
          <DialogDescription>
            Serão apagados o original, o Markdown gerado e o registro deste documento. Não é possível
            desfazer.
          </DialogDescription>
        </DialogHeader>
        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => aoMudarAbertura(false)} disabled={apagando}>
            Cancelar
          </Button>
          <Button type="button" variant="destructive" onClick={apagar} disabled={apagando}>
            {apagando ? "Apagando…" : "Apagar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
