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
import { apiFetch } from "@/lib/api-client";

/**
 * Confirmação de exclusão de base (SPEC-0013, US-003 / FR-007).
 *
 * Mostra o nome da base e a consequência explícita antes de executar
 * (AC-011). A ação "Apagar" só é oferecida a owner/admin — para member ela
 * simplesmente não aparece (AC-019); o backend ainda recusa uma chamada
 * direta com 403.
 */

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface ExcluirBaseDialogProps {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  base: { id: string; nome: string };
  papel?: string;
  onDeleted: (id: string) => void;
}

export default function ExcluirBaseDialog({
  open,
  onOpenChange,
  base,
  papel,
  onDeleted,
}: ExcluirBaseDialogProps) {
  const [apagando, setApagando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const podeApagar = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  async function apagar() {
    setApagando(true);
    setErro(null);
    try {
      await apiFetch(`/api/v1/bases/${base.id}`, { method: "DELETE" });
      onDeleted(base.id);
      onOpenChange?.(false);
    } catch {
      setErro("Não foi possível apagar a base. Tente novamente.");
    } finally {
      setApagando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Apagar a base “{base.nome}”?</DialogTitle>
          <DialogDescription>
            Esta ação remove a base, suas execuções, consultas e os vetores
            associados. Não é possível desfazer.
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
            onClick={() => onOpenChange?.(false)}
            disabled={apagando}
          >
            Cancelar
          </Button>
          {podeApagar ? (
            <Button
              type="button"
              variant="destructive"
              onClick={apagar}
              loading={apagando}
              disabled={apagando}
            >
              {apagando ? "Apagando…" : "Apagar"}
            </Button>
          ) : null}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
