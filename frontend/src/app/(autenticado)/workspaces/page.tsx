"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import DataGridWorkspaces, {
  type WorkspaceResumo,
} from "@/features/workspaces/DataGridWorkspaces";
import WorkspaceFormSheet from "@/features/workspaces/WorkspaceFormSheet";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<WorkspaceResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [criarAberto, setCriarAberto] = useState(false);
  const [releituras, setReleituras] = useState(0);
  const papel = getPapel();
  const podeCriar = papel !== null && PAPEIS_DE_ESCRITA.includes(papel);

  useEffect(() => {
    let ativo = true;

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
  }, [releituras]);

  function reler() {
    setCarregando(true);
    setErro(null);
    setReleituras((valor) => valor + 1);
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Workspaces"
        description="Organize as Bases por contexto e acesse cada coleção de conhecimento."
        actions={
          podeCriar ? (
            <Button
              type="button"
              aria-haspopup="dialog"
              onClick={() => setCriarAberto(true)}
            >
              Criar Workspace
            </Button>
          ) : undefined
        }
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={reler}>
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

      {podeCriar && criarAberto ? (
        <WorkspaceFormSheet
          open
          onOpenChange={setCriarAberto}
          onSaved={(salvo) => {
            setWorkspaces((atuais) => [...atuais, salvo]);
            setCriarAberto(false);
          }}
        />
      ) : null}
    </div>
  );
}
