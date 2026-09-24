"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import ExcluirBaseDialog from "@/features/bases/ExcluirBaseDialog";
import FormularioConsulta from "@/features/execucoes/FormularioConsulta";
import PainelProgresso, {
  type Execucao,
} from "@/features/execucoes/PainelProgresso";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

/**
 * Detalhe da base pelo id na URL (SPEC-0013, seção 10).
 *
 * `[id]` é o id da base: a tela mostra a execução mais recente e o histórico.
 * Enquanto a execução mais recente estiver `pending`/`running`, faz polling
 * do backend (FR-005) — nenhuma chamada toca o banco vetorial (AC-008).
 */

interface BaseDetalhe {
  id: string;
  nome: string;
  origem: string;
  documentos: number;
  criado_em: string;
  workspace_id: string;
  collection_name: string;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
  execucoes: Execucao[];
}

interface WorkspaceResumo {
  id: string;
  nome: string;
}

const SITUACOES_ATIVAS = ["pending", "running"];
const INTERVALO_POLLING_MS = 3000;

function autor(criadoPor: BaseDetalhe["criado_por"]): string {
  if (!criadoPor) return "Autor não identificado";
  return `${criadoPor.nome}${criadoPor.desativada ? " (desativada)" : ""}`;
}

export default function ExecucaoDetalhePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const baseId = params.id;

  const [detalhe, setDetalhe] = useState<BaseDetalhe | null>(null);
  const [workspaceNome, setWorkspaceNome] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [releituras, setReleituras] = useState(0);
  const [confirmarExclusao, setConfirmarExclusao] = useState(false);
  const workspaceCache = useRef<WorkspaceResumo | null>(null);

  const papel = getPapel() ?? undefined;
  const podeApagar = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  useEffect(() => {
    let ativo = true;
    apiJson<BaseDetalhe>(`/api/v1/bases/${baseId}`)
      .then(async (dados) => {
        let workspace = workspaceCache.current;
        if (workspace?.id !== dados.workspace_id) {
          try {
            workspace = await apiJson<WorkspaceResumo>(
              `/api/v1/workspaces/${dados.workspace_id}`,
            );
          } catch (causa) {
            if (causa instanceof ApiError && causa.unauthorized) throw causa;
            if (ativo) setErro("Não foi possível carregar o contexto do Workspace.");
            return;
          }
          workspaceCache.current = workspace;
        }
        if (ativo) {
          setDetalhe(dados);
          setWorkspaceNome(workspace.nome);
          setErro(null);
        }
      })
      .catch((causa) => {
        if (ativo && !(causa instanceof ApiError && causa.unauthorized)) {
          setErro(
            causa instanceof ApiError && causa.status === 404
              ? "Base não encontrada."
              : "Não foi possível carregar o detalhe da base.",
          );
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [baseId, releituras]);

  const execucaoAtual = detalhe?.execucoes[0] ?? null;
  const historico = detalhe?.execucoes.slice(1) ?? [];
  const temIndexacao =
    detalhe?.execucoes.some((execucao) => execucao.situacao === "succeeded") ??
    false;
  const emAndamento = execucaoAtual
    ? SITUACOES_ATIVAS.includes(execucaoAtual.situacao)
    : false;

  useEffect(() => {
    if (!emAndamento) return;
    const id = setInterval(
      () => setReleituras((valor) => valor + 1),
      INTERVALO_POLLING_MS,
    );
    return () => clearInterval(id);
  }, [emAndamento]);

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title={detalhe ? `Base ${detalhe.nome || detalhe.id}` : "Detalhe da base"}
        description={
          detalhe && workspaceNome
            ? `Workspace: ${workspaceNome} · Coleção: ${detalhe.collection_name}`
            : "Acompanhe o processamento e consulte a base indexada."
        }
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={detalhe ? `/workspaces/${detalhe.workspace_id}` : "/workspaces"}
              className={buttonVariants({ variant: "outline" })}
            >
              Voltar ao Workspace
            </Link>
            {podeApagar && detalhe ? (
              <Button
                type="button"
                variant="destructive"
                onClick={() => setConfirmarExclusao(true)}
              >
                Apagar base
              </Button>
            ) : null}
          </div>
        }
      />

      {detalhe ? (
        <p className="text-sm text-muted-foreground [overflow-wrap:anywhere]">
          Criada por {autor(detalhe.criado_por)}
        </p>
      ) : null}

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}

      {carregando && !detalhe ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : null}

      {execucaoAtual ? (
        <PainelProgresso
          execucao={execucaoAtual}
          papel={papel}
          onRepetida={() => setReleituras((valor) => valor + 1)}
        />
      ) : null}

      {detalhe && detalhe.execucoes.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Esta base ainda não tem execuções.
        </p>
      ) : null}

      {temIndexacao ? (
        <section className="flex flex-col gap-2 rounded-lg border p-4">
          <h2 className="text-sm font-medium">Consultar a base</h2>
          <FormularioConsulta baseId={baseId} />
        </section>
      ) : null}

      {historico.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium">Histórico de execuções</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {historico.map((execucao) => (
              <li
                key={execucao.id}
                className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
              >
                <span className="font-mono text-xs">{execucao.id}</span>
                <span className="text-muted-foreground">
                  {execucao.situacao} · {execucao.etapa || "—"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {detalhe ? (
        <ExcluirBaseDialog
          open={confirmarExclusao}
          onOpenChange={setConfirmarExclusao}
          base={{ id: detalhe.id, nome: detalhe.nome || detalhe.id }}
          papel={papel}
          onDeleted={() => router.push(`/workspaces/${detalhe.workspace_id}`)}
        />
      ) : null}
      {/* FormularioConsulta (T031) entra na próxima tarefa. */}
    </div>
  );
}
