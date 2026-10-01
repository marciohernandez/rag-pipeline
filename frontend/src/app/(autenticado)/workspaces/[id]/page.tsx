"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import DataGridBases, { type BaseResumo } from "@/features/bases/DataGridBases";
import UploadBaseSheet from "@/features/bases/UploadBaseSheet";
import ConversaoSheet from "@/features/conversao/ConversaoSheet";
import DataGridLotesConversao, {
  type LoteConversaoResumo,
} from "@/features/conversao/DataGridLotesConversao";
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
  const [lotes, setLotes] = useState<LoteConversaoResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [naoEncontrado, setNaoEncontrado] = useState(false);
  const [releituras, setReleituras] = useState(0);
  const [enviarAberto, setEnviarAberto] = useState(false);
  const [converterAberto, setConverterAberto] = useState(false);
  const [editarAberto, setEditarAberto] = useState(false);
  const [apagarAberto, setApagarAberto] = useState(false);
  const papel = getPapel() ?? undefined;
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  useEffect(() => {
    let ativo = true;

    Promise.all([
      apiJson<WorkspaceResumo>(`/api/v1/workspaces/${workspaceId}`),
      apiJson<BaseResumo[]>(`/api/v1/bases?workspace_id=${encodeURIComponent(workspaceId)}`),
      apiJson<LoteConversaoResumo[]>(
        `/api/v1/conversoes?workspace_id=${encodeURIComponent(workspaceId)}`,
      ),
    ])
      .then(([workspaceLido, basesLidas, lotesLidos]) => {
        if (!ativo) return;
        setWorkspace(workspaceLido);
        setBases(basesLidas);
        setLotes(lotesLidos);
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
          <Button type="button" onClick={() => setEnviarAberto(true)}>
            Enviar base
          </Button>
          <Button type="button" variant="outline" onClick={() => setConverterAberto(true)}>
            Converter documentos
          </Button>
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
        <Tabs defaultValue="bases" className="w-full min-w-0">
          <TabsList className="max-w-full overflow-x-auto">
            <TabsTrigger value="bases">Bases</TabsTrigger>
            <TabsTrigger value="conversao">Conversão de documentos</TabsTrigger>
          </TabsList>
          <TabsContent value="bases">
            <DataGridBases
              bases={bases}
              carregando={carregando}
              papel={papel}
              onBaseApagada={(id) =>
                setBases((atuais) => atuais.filter((base) => base.id !== id))
              }
            />
          </TabsContent>
          <TabsContent value="conversao">
            <DataGridLotesConversao
              lotes={lotes}
              carregando={carregando}
              papel={papel}
              onLoteAtualizado={(loteAtualizado) =>
                setLotes((atuais) =>
                  atuais.map((lote) => (lote.id === loteAtualizado.id ? loteAtualizado : lote)),
                )
              }
            />
          </TabsContent>
        </Tabs>
      )}

      {workspace && enviarAberto ? (
        <UploadBaseSheet
          open
          workspaceId={workspace.id}
          onOpenChange={setEnviarAberto}
          onCreated={() => {
            setEnviarAberto(false);
            reler();
          }}
        />
      ) : null}

      {workspace && converterAberto ? (
        <ConversaoSheet
          open
          workspaceId={workspace.id}
          papel={papel}
          onOpenChange={setConverterAberto}
          onCriado={(loteCriadoOuAtualizado) =>
            setLotes((atuais) => {
              const existe = atuais.some((lote) => lote.id === loteCriadoOuAtualizado.id);
              if (existe) {
                return atuais.map((lote) =>
                  lote.id === loteCriadoOuAtualizado.id ? loteCriadoOuAtualizado : lote,
                );
              }
              return [loteCriadoOuAtualizado, ...atuais];
            })
          }
        />
      ) : null}

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
