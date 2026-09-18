"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import DataGridWorkspaces, {
  type WorkspaceResumo,
} from "@/features/workspaces/DataGridWorkspaces";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<WorkspaceResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const papel = getPapel();
  const podeCriar = papel !== null && PAPEIS_DE_ESCRITA.includes(papel);

  const carregar = useCallback(() => {
    let ativo = true;
    setCarregando(true);
    setErro(null);

    apiJson<WorkspaceResumo[]>("/api/v1/workspaces")
      .then((dados) => {
        if (ativo) setWorkspaces(dados);
      })
      .catch((causa) => {
        // O api-client já trata 401 limpando a sessão.
        if (ativo && !(causa instanceof ApiError && causa.unauthorized)) {
          setErro("Não foi possível carregar os Workspaces. Tente novamente.");
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });

    return () => {
      ativo = false;
    };
  }, []);

  useEffect(() => carregar(), [carregar]);

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Workspaces"
        description="Organize as Bases por contexto e acesse cada coleção de conhecimento."
        actions={
          podeCriar ? (
            <Button type="button" aria-haspopup="dialog">
              Criar Workspace
            </Button>
          ) : undefined
        }
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={carregar}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <DataGridWorkspaces
          workspaces={workspaces}
          carregando={carregando}
          podeCriar={podeCriar}
        />
      )}
    </div>
  );
}
