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
 * Confirmação de exclusão de um documento da coleção (SPEC-0030, FR-009): informa
 * quantos chunks saem e preserva o histórico de envios. Em falha, o diálogo continua
 * aberto com uma mensagem segura, sem detalhe do provedor.
 */

const MENSAGEM_FALHA = "Não foi possível apagar o documento. Tente novamente.";

interface ApagarDocumentoDialogProps {
  open: boolean;
  colecaoId: string;
  documento: { id: string; nome_arquivo: string; chunks: number };
  onOpenChange?: (open: boolean) => void;
  onDeleted: (id: string) => void;
}

export default function ApagarDocumentoDialog({
  open,
  colecaoId,
  documento,
  onOpenChange,
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
        `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/documentos/${encodeURIComponent(documento.id)}`,
        { method: "DELETE" },
      );
      onDeleted(documento.id);
      onOpenChange?.(false);
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.status === 409 && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setApagando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={aoMudarAbertura}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="[overflow-wrap:anywhere]">Apagar o documento “{documento.nome_arquivo}”?</DialogTitle>
          <DialogDescription>
            {documento.chunks} chunks serão removidos da coleção. O histórico de envios continua como está. Não é
            possível desfazer.
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
          <Button type="button" variant="destructive" onClick={apagar} loading={apagando} disabled={apagando}>
            {apagando ? "Apagando…" : "Apagar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
