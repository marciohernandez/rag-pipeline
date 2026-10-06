"use client";

import { useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { WorkspaceResumo } from "@/features/workspaces/DataGridWorkspaces";
import { apiJson } from "@/lib/api-client";

interface WorkspaceFormSheetProps {
  open: boolean;
  workspace?: WorkspaceResumo;
  onOpenChange?: (open: boolean) => void;
  onSaved: (workspace: WorkspaceResumo) => void;
}

export default function WorkspaceFormSheet({
  open,
  workspace,
  onOpenChange,
  onSaved,
}: WorkspaceFormSheetProps) {
  const [nome, setNome] = useState(workspace?.nome ?? "");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const campoNome = useRef<HTMLInputElement>(null);
  const editando = workspace !== undefined;

  function aoMudarAbertura(aberto: boolean) {
    if (salvando) return;
    if (!aberto) {
      setNome(workspace?.nome ?? "");
      setErro(null);
    }
    onOpenChange?.(aberto);
  }

  async function salvar() {
    if (salvando) return;
    const nomeNormalizado = nome.trim();
    if (!nomeNormalizado) {
      setErro("Informe um nome para o Workspace.");
      campoNome.current?.focus();
      return;
    }

    setSalvando(true);
    setErro(null);
    try {
      const salvo = await apiJson<WorkspaceResumo>(
        editando ? `/api/v1/workspaces/${workspace.id}` : "/api/v1/workspaces",
        {
          method: editando ? "PATCH" : "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ nome: nomeNormalizado }),
        },
      );
      onSaved(salvo);
    } catch {
      setErro("Não foi possível salvar o Workspace. Tente novamente.");
      campoNome.current?.focus();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={aoMudarAbertura}>
      <SheetContent side="right" className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{editando ? "Editar Workspace" : "Criar Workspace"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Atualize o nome usado para identificar este contexto de Bases."
              : "Dê um nome claro ao contexto que reunirá suas Bases."}
          </SheetDescription>
        </SheetHeader>

        <form
          className="flex min-h-0 flex-1 flex-col gap-4"
          onSubmit={(evento) => {
            evento.preventDefault();
            void salvar();
          }}
        >
          <div className="flex flex-col gap-1.5 px-4">
            <Label htmlFor="workspace-nome">Nome</Label>
            <Input
              ref={campoNome}
              id="workspace-nome"
              value={nome}
              onChange={(evento) => {
                setNome(evento.target.value);
                if (erro) setErro(null);
              }}
              aria-invalid={erro ? true : undefined}
              aria-describedby={erro ? "workspace-form-erro" : undefined}
              disabled={salvando}
            />
            {erro ? (
              <Alert id="workspace-form-erro" variant="destructive" className="mt-1">
                <AlertDescription>{erro}</AlertDescription>
              </Alert>
            ) : null}
          </div>

          <SheetFooter className="flex-row justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => aoMudarAbertura(false)}
              disabled={salvando}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={salvando} disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
