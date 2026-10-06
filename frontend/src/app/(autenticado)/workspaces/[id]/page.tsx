"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import DataGridBases, { type BaseResumo } from "@/features/bases/DataGridBases";
import type { WorkspaceResumo } from "@/features/workspaces/DataGridWorkspaces";
import ExcluirWorkspaceDialog from "@/features/workspaces/ExcluirWorkspaceDialog";
import WorkspaceFormSheet from "@/features/workspaces/WorkspaceFormSheet";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

export default function WorkspaceDetalhePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<WorkspaceResumo | null>(null);
  const [bases, setBases] = useState<BaseResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [naoEncontrado, setNaoEncontrado] = useState(false);
  const [releituras, setReleituras] = useState(0);
  const [editarAberto, setEditarAberto] = useState(false);
  const [apagarAberto, setApagarAberto] = useState(false);
  const papel = getPapel() ?? undefined;
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  useEffect(() => {
    let ativo = true;

    Promise.all([
      apiJson<WorkspaceResumo>(`/api/v1/workspaces/${workspaceId}`),
      apiJson<BaseResumo[]>(`/api/v1/bases?workspace_id=${encodeURIComponent(workspaceId)}`),
    ])
      .then(([workspaceLido, basesLidas]) => {
        if (!ativo) return;
        setWorkspace(workspaceLido);
        setBases(basesLidas);
      })
      .catch((causa) => {
        if (!ativo || (causa instanceof ApiError && causa.unauthorized)) return;
        if (causa instanceof ApiError && causa.status === 404) {
          setNaoEncontrado(true);
          setErro("Workspace não encontrado.");
        } else {
          setErro("Não foi possível carregar o Workspace. Tente novamente.");
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });

    return () => {
      ativo = false;
    };
  }, [workspaceId, releituras]);

  function reler() {
    setCarregando(true);
    setErro(null);
    setNaoEncontrado(false);
    setReleituras((valor) => valor + 1);
  }

  const acoes = (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Link href="/workspaces" className={buttonVariants({ variant: "outline" })}>
        Voltar aos Workspaces
      </Link>
      {podeEscrever && workspace ? (
        <>
          <Button type="button" variant="outline" onClick={() => setEditarAberto(true)}>
            Editar nome
          </Button>
          <Link
            href={`/workspaces/${encodeURIComponent(workspace.id)}/bases/nova`}
            className={buttonVariants({ variant: "default" })}
          >
            Nova Base
          </Link>
          <Button
            type="button"
            variant="destructive"
            onClick={() => setApagarAberto(true)}
          >
            Apagar Workspace
          </Button>
        </>
      ) : null}
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title={workspace?.nome ?? (naoEncontrado ? "Workspace não encontrado" : "Workspace")}
        description="Bases e coleções de conhecimento deste Workspace."
        actions={acoes}
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            {!naoEncontrado ? (
              <Button type="button" variant="outline" size="sm" onClick={reler}>
                Tentar novamente
              </Button>
            ) : null}
          </AlertDescription>
        </Alert>
      ) : (
        <DataGridBases
          bases={bases}
          carregando={carregando}
          papel={papel}
          onBaseApagada={(id) => setBases((atuais) => atuais.filter((base) => base.id !== id))}
        />
      )}

      {workspace && editarAberto ? (
        <WorkspaceFormSheet
          open
          workspace={workspace}
          onOpenChange={setEditarAberto}
          onSaved={(salvo) => {
            setWorkspace(salvo);
            setEditarAberto(false);
          }}
        />
      ) : null}

      {workspace && apagarAberto ? (
        <ExcluirWorkspaceDialog
          open
          workspace={workspace}
          temBases={bases.length > 0}
          papel={papel}
          onOpenChange={setApagarAberto}
          onDeleted={() => router.push("/workspaces")}
        />
      ) : null}
    </div>
  );
}
