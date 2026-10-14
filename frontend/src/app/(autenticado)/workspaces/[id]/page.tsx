"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import DataGridColecoes from "@/features/colecoes/DataGridColecoes";
import type { ColecaoResumo } from "@/features/colecoes/tipos";
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
  const [colecoes, setColecoes] = useState<ColecaoResumo[]>([]);
  const [lotes, setLotes] = useState<LoteConversaoResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [naoEncontrado, setNaoEncontrado] = useState(false);
  const [releituras, setReleituras] = useState(0);
  const [converterAberto, setConverterAberto] = useState(false);
  const [editarAberto, setEditarAberto] = useState(false);
  const [apagarAberto, setApagarAberto] = useState(false);
  const papel = getPapel() ?? undefined;
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  useEffect(() => {
    let ativo = true;

    Promise.all([
      apiJson<WorkspaceResumo>(`/api/v1/workspaces/${workspaceId}`),
      apiJson<ColecaoResumo[]>(`/api/v1/workspaces/${encodeURIComponent(workspaceId)}/colecoes`),
      apiJson<LoteConversaoResumo[]>(
        `/api/v1/conversoes?workspace_id=${encodeURIComponent(workspaceId)}`,
      ),
    ])
      .then(([workspaceLido, colecoesLidas, lotesLidos]) => {
        if (!ativo) return;
        setWorkspace(workspaceLido);
        setColecoes(colecoesLidas);
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
          <Link
            href={`/workspaces/${encodeURIComponent(workspace.id)}/enviar`}
            className={buttonVariants({ variant: "default" })}
          >
            Enviar documentos
          </Link>
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
        description="Coleções de documentos deste Workspace."
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
        <Tabs defaultValue="colecoes" className="w-full min-w-0">
          <TabsList className="max-w-full overflow-x-auto">
            <TabsTrigger value="colecoes">Coleções</TabsTrigger>
            <TabsTrigger value="conversao">Conversão de documentos</TabsTrigger>
          </TabsList>
          <TabsContent value="colecoes">
            <DataGridColecoes
              workspaceId={workspaceId}
              colecoes={colecoes}
              carregando={carregando}
              papel={papel}
              onRenomeada={(salva) =>
                setColecoes((atuais) =>
                  atuais.map((c) => (c.id === salva.id ? { ...c, nome: salva.nome } : c)),
                )
              }
              onApagada={(id) => setColecoes((atuais) => atuais.filter((c) => c.id !== id))}
            />
          </TabsContent>
          <TabsContent value="conversao">
            <DataGridLotesConversao
              lotes={lotes}
              carregando={carregando}
              papel={papel}
              onConverter={() => setConverterAberto(true)}
              onLoteAtualizado={(loteAtualizado) =>
                setLotes((atuais) =>
                  atuais.map((lote) => (lote.id === loteAtualizado.id ? loteAtualizado : lote)),
                )
              }
            />
          </TabsContent>
        </Tabs>
      )}

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
          temColecoes={colecoes.length > 0}
          papel={papel}
          onOpenChange={setApagarAberto}
          onDeleted={() => router.push("/workspaces")}
        />
      ) : null}
    </div>
  );
}
