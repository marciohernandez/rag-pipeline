"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Skeleton } from "@/components/ui/skeleton";
import AssistenteLauncher from "@/features/assistente/AssistenteLauncher";
import MenuPessoa from "@/features/auth/MenuPessoa";
import { ApiError, apiJson } from "@/lib/api-client";
import { hasSession, saveIdentity, type PessoaSessao } from "@/lib/session";

interface ContextoTrilha {
  pathname: string;
  workspaceId?: string;
  workspaceNome?: string;
  colecaoId?: string;
  colecaoNome?: string;
  pessoaNome?: string;
  conexaoNome?: string;
}

type EstadoShell = "carregando" | "pronto" | "erro";

export default function LayoutAutenticado({ children }: { children: ReactNode }) {
  const { replace } = useRouter();
  const pathname = usePathname();
  const [estado, setEstado] = useState<EstadoShell>("carregando");
  const [pessoa, setPessoa] = useState<PessoaSessao | null>(null);
  const [contexto, setContexto] = useState<ContextoTrilha | null>(null);
  const [releiturasIdentidade, setReleiturasIdentidade] = useState(0);

  const segmentos = pathname.split("/").filter(Boolean);
  const workspaceId = segmentos[0] === "workspaces" ? segmentos[1] : undefined;
  const envioId = segmentos[0] === "envios" ? segmentos[1] : undefined;
  const colecaoId = workspaceId !== undefined && segmentos[2] === "colecoes" ? segmentos[3] : undefined;
  const pessoas = segmentos[0] === "pessoas";
  const pessoaId = pessoas ? segmentos[1] : undefined;
  const conexoes = segmentos[0] === "conexoes";
  const conexaoId = conexoes ? segmentos[1] : undefined;
  const enviar = workspaceId !== undefined && segmentos[2] === "enviar";

  useEffect(() => {
    if (!hasSession()) {
      replace("/login");
      return;
    }
    let ativo = true;
    apiJson<PessoaSessao>("/api/v1/auth/me")
      .then((identidade) => {
        if (!ativo) return;
        saveIdentity(identidade);
        if (identidade.precisa_trocar_senha) {
          replace("/nova-senha");
          return;
        }
        setPessoa(identidade);
        setEstado("pronto");
      })
      .catch((falha) => {
        if (!ativo) return;
        if (falha instanceof ApiError && falha.unauthorized) {
          replace("/login");
          return;
        }
        setEstado("erro");
      });
    return () => { ativo = false; };
  }, [replace, releiturasIdentidade]);

  useEffect(() => {
    if (estado !== "pronto" || (!workspaceId && !envioId && !pessoaId && !conexaoId)) return;
    let ativo = true;
    async function carregarTrilha() {
      try {
        if (conexaoId) {
          const conexao = await apiJson<{ id: string; nome: string }>(`/api/v1/conexoes/${conexaoId}`);
          if (ativo) setContexto({ pathname, conexaoNome: conexao.nome });
        } else if (pessoaId) {
          const detalhe = await apiJson<{ id: string; nome: string }>(`/api/v1/pessoas/${pessoaId}`);
          if (ativo) setContexto({ pathname, pessoaNome: detalhe.nome });
        } else if (envioId) {
          const envio = await apiJson<{ colecao: { id: string; nome: string; workspace_id: string } }>(`/api/v1/envios/${envioId}`);
          const workspace = await apiJson<{ id: string; nome: string }>(`/api/v1/workspaces/${envio.colecao.workspace_id}`);
          if (ativo) setContexto({ pathname, workspaceId: workspace.id, workspaceNome: workspace.nome, colecaoId: envio.colecao.id, colecaoNome: envio.colecao.nome });
        } else if (colecaoId) {
          const colecao = await apiJson<{ nome: string; workspace_id: string; workspace_nome: string }>(`/api/v1/colecoes/${colecaoId}`);
          if (ativo) setContexto({ pathname, workspaceId: colecao.workspace_id, workspaceNome: colecao.workspace_nome, colecaoNome: colecao.nome });
        } else if (workspaceId) {
          const workspace = await apiJson<{ id: string; nome: string }>(`/api/v1/workspaces/${workspaceId}`);
          if (ativo) setContexto({ pathname, workspaceId: workspace.id, workspaceNome: workspace.nome });
        }
      } catch {
        // A página mostra a falha; a trilha conserva identificadores seguros.
      }
    }
    void carregarTrilha();
    return () => { ativo = false; };
  }, [estado, pathname, workspaceId, envioId, colecaoId, pessoaId, conexaoId]);

  if (estado === "carregando") {
    return (
      <div
        className="flex min-h-dvh flex-col"
      >
        <header className="border-b px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-7 w-36" />
          </div>
          <div className="mt-3 flex gap-4">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
          </div>
        </header>
        <main className="flex flex-1 flex-col gap-3 p-4">
          <IndicadorProcessamento>Carregando sessão</IndicadorProcessamento>
          <Skeleton className="h-7 w-40" />
          <Skeleton className="h-4 w-full max-w-md" />
          <Skeleton className="h-40 w-full" />
        </main>
      </div>
    );
  }

  if (estado === "erro") {
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-3xl items-start p-4 sm:p-6">
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>Não foi possível validar sua sessão. Tente novamente.</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setPessoa(null);
                setEstado("carregando");
                setReleiturasIdentidade((valor) => valor + 1);
              }}
            >
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </main>
    );
  }

  const trilha = contexto?.pathname === pathname ? contexto : null;
  const nomeWorkspace = trilha?.workspaceNome || (workspaceId ? `Workspace ${workspaceId}` : "Workspace");
  const nomeColecao = trilha?.colecaoNome || (colecaoId ? `Coleção ${colecaoId}` : "Coleção");
  const hrefWorkspace = trilha?.workspaceId || workspaceId;
  const podeGerirPessoas = pessoa?.papel === "owner" || pessoa?.papel === "admin";

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-b px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <nav aria-label="Trilha" className="min-w-0 flex-1">
            <ol className="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground">
              <li><Link href="/workspaces" className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">Equipe</Link></li>
              <li aria-hidden>/</li>
              {conexoes ? (
                <>
                  <li>{conexaoId ? <Link href="/conexoes">Conexões</Link> : <span aria-current="page" className="text-foreground">Conexões</span>}</li>
                  {conexaoId ? <><li aria-hidden>/</li><li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{trilha?.conexaoNome || "Conexão"}</span></li></> : null}
                </>
              ) : pessoas ? (
                <>
                  <li>{pessoaId ? <Link href="/pessoas">Pessoas</Link> : <span aria-current="page" className="text-foreground">Pessoas</span>}</li>
                  {pessoaId ? <><li aria-hidden>/</li><li className="min-w-0"><span aria-current="page" title={trilha?.pessoaNome} className="block max-w-32 truncate text-foreground sm:max-w-none sm:overflow-visible sm:text-clip sm:whitespace-normal [overflow-wrap:anywhere]">{trilha?.pessoaNome || "Pessoa"}</span></li></> : null}
                </>
              ) : (
                <>
                  <li>{workspaceId || envioId ? <Link href="/workspaces">Workspaces</Link> : <span aria-current="page" className="text-foreground">Workspaces</span>}</li>
                  {workspaceId || envioId ? <li aria-hidden>/</li> : null}
                  {workspaceId && (enviar || colecaoId) ? <li className="min-w-0"><Link href={`/workspaces/${encodeURIComponent(workspaceId)}`} className="[overflow-wrap:anywhere]">{nomeWorkspace}</Link></li> : null}
                  {workspaceId && (enviar || colecaoId) ? <li aria-hidden>/</li> : null}
                  {workspaceId && enviar ? <li className="min-w-0"><span aria-current="page" className="text-foreground">Enviar documentos</span></li> : null}
                  {workspaceId && colecaoId ? <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeColecao}</span></li> : null}
                  {workspaceId && !enviar && !colecaoId ? <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeWorkspace}</span></li> : null}
                  {envioId ? <li className="max-w-24 truncate sm:max-w-none"><Link href={hrefWorkspace ? `/workspaces/${encodeURIComponent(hrefWorkspace)}` : "/workspaces"}>{nomeWorkspace}</Link></li> : null}
                  {envioId ? <li aria-hidden>/</li> : null}
                  {envioId ? <li className="min-w-0"><Link href={hrefWorkspace && trilha?.colecaoId ? `/workspaces/${encodeURIComponent(hrefWorkspace)}/colecoes/${encodeURIComponent(trilha.colecaoId)}` : "/workspaces"} className="[overflow-wrap:anywhere]">{nomeColecao}</Link></li> : null}
                  {envioId ? <li aria-hidden>/</li> : null}
                  {envioId ? <li className="min-w-0"><span aria-current="page" className="text-foreground">Envio</span></li> : null}
                </>
              )}
            </ol>
          </nav>
          {pessoa ? <MenuPessoa nome={pessoa.nome} papel={pessoa.papel} /> : null}
        </div>
        <nav aria-label="Principal" className="mt-3 flex gap-4 text-sm">
          <Link href="/workspaces" aria-current={pathname.startsWith("/workspaces") ? "page" : undefined}>Workspaces</Link>
          {podeGerirPessoas ? <Link href="/pessoas" aria-current={pessoas ? "page" : undefined}>Pessoas</Link> : null}
          {podeGerirPessoas ? <Link href="/conexoes" aria-current={conexoes ? "page" : undefined}>Conexões</Link> : null}
        </nav>
      </header>
      <main className="w-full min-w-0 flex-1 overflow-x-hidden p-4">{children}</main>
      {pessoa ? <AssistenteLauncher onSessaoEncerrada={() => replace("/login")} /> : null}
    </div>
  );
}
