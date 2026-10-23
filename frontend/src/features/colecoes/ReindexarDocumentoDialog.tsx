"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * Confirmação de reindexação de um documento cujo `.md` do lote mudou (SPEC-0043, FR-008).
 * Não indexa nada por conta própria: confirma e leva ao fluxo de ingestão com a coleção e o
 * documento do lote já escolhidos, onde a pessoa ainda publica. Embeddings têm custo, por
 * isso a reindexação nunca é automática.
 */

interface ReindexarDocumentoDialogProps {
  open: boolean;
  documento: { nome_arquivo: string };
  onOpenChange?: (open: boolean) => void;
  onConfirmar: () => void;
}

export default function ReindexarDocumentoDialog({
  open,
  documento,
  onOpenChange,
  onConfirmar,
}: ReindexarDocumentoDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="[overflow-wrap:anywhere]">Reindexar “{documento.nome_arquivo}”?</DialogTitle>
          <DialogDescription>
            O arquivo do lote mudou depois da indexação. Reindexar gera novos embeddings e substitui a versão
            atual do documento nesta coleção. Você ainda confirma a publicação no passo seguinte.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange?.(false)}>
            Cancelar
          </Button>
          <Button type="button" onClick={onConfirmar}>
            Continuar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
