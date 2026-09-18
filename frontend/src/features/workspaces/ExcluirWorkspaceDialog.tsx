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
import type { WorkspaceResumo } from "@/features/workspaces/DataGridWorkspaces";
import { apiFetch } from "@/lib/api-client";

interface ExcluirWorkspaceDialogProps {
  open: boolean;
  workspace: WorkspaceResumo;
  temBases: boolean;
  papel?: string;
  onOpenChange?: (open: boolean) => void;
  onDeleted: (id: string) => void;
}

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

export default function ExcluirWorkspaceDialog({
  open,
  workspace,
  temBases,
  papel,
  onOpenChange,
  onDeleted,
}: ExcluirWorkspaceDialogProps) {
  const [apagando, setApagando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const podeApagar = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  async function apagar() {
    setApagando(true);
    setErro(null);
    try {
      await apiFetch(`/api/v1/workspaces/${workspace.id}`, { method: "DELETE" });
      onDeleted(workspace.id);
    } catch {
      setErro("Não foi possível apagar o Workspace. Tente novamente.");
    } finally {
      setApagando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Apagar Workspace</DialogTitle>
          <DialogDescription>
            Você está prestes a apagar “{workspace.nome}”.
          </DialogDescription>
        </DialogHeader>

        {temBases ? (
          <Alert>
            <AlertDescription>
              Apague ou mova as Bases deste Workspace antes de continuar.
            </AlertDescription>
          </Alert>
        ) : (
          <p className="text-sm text-muted-foreground">
            O Workspace deixará de aparecer na listagem. Esta ação exige confirmação.
          </p>
        )}

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
              disabled={apagando || temBases}
            >
              {apagando ? "Apagando…" : "Apagar Workspace"}
            </Button>
          ) : null}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
