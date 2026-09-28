"use client";

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

/**
 * Confirma a consequência antes de apagar uma conversa (SPEC-0021, FR-002).
 * Padrão de `ExcluirBaseDialog`: nome do alvo, consequência explícita e erro
 * recuperável sem fechar o diálogo.
 */

interface ApagarConversaDialogProps {
  open: boolean;
  titulo: string;
  apagando: boolean;
  erro: string | null;
  onConfirmar: () => void;
  onCancelar: () => void;
}

export default function ApagarConversaDialog({
  open,
  titulo,
  apagando,
  erro,
  onConfirmar,
  onCancelar,
}: ApagarConversaDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(aberto) => (aberto ? undefined : onCancelar())}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Apagar a conversa “{titulo}”?</DialogTitle>
          <DialogDescription>
            Esta ação remove a conversa e todas as suas mensagens. Não é possível desfazer.
          </DialogDescription>
        </DialogHeader>
        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancelar} disabled={apagando}>
            Cancelar
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirmar} disabled={apagando}>
            Apagar conversa
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
