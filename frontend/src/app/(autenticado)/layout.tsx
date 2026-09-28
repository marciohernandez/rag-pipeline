"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import AssistenteLauncher from "@/features/assistente/AssistenteLauncher";
import MenuPessoa from "@/features/auth/MenuPessoa";
import { ApiError, apiJson } from "@/lib/api-client";
import { hasSession, saveIdentity, type PessoaSessao } from "@/lib/session";

interface ContextoTrilha {
  pathname: string;
  workspaceId?: string;
  workspaceNome?: string;
  baseNome?: string;
  pessoaNome?: string;
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
  const baseId = segmentos[0] === "execucoes" ? segmentos[1] : undefined;
  const pessoas = segmentos[0] === "pessoas";
  const pessoaId = pessoas ? segmentos[1] : undefined;

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
    if (estado !== "pronto" || (!workspaceId && !baseId && !pessoaId)) return;
    let ativo = true;
    async function carregarTrilha() {
      try {
        if (pessoaId) {
          const detalhe = await apiJson<{ id: string; nome: string }>(`/api/v1/pessoas/${pessoaId}`);
          if (ativo) setContexto({ pathname, pessoaNome: detalhe.nome });
        } else if (baseId) {
          const base = await apiJson<{ id: string; nome: string; workspace_id: string }>(`/api/v1/bases/${baseId}`);
          const workspace = await apiJson<{ id: string; nome: string }>(`/api/v1/workspaces/${base.workspace_id}`);
          if (ativo) setContexto({ pathname, workspaceId: workspace.id, workspaceNome: workspace.nome, baseNome: base.nome || base.id });
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
  }, [estado, pathname, workspaceId, baseId, pessoaId]);

  if (estado === "carregando") {
    return (
      <div
        role="status"
        aria-label="Carregando sessão"
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
  const nomeBase = trilha?.baseNome || (baseId ? `Base ${baseId}` : "Base");
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
              {pessoas ? (
                <>
                  <li>{pessoaId ? <Link href="/pessoas">Pessoas</Link> : <span aria-current="page" className="text-foreground">Pessoas</span>}</li>
                  {pessoaId ? <><li aria-hidden>/</li><li className="min-w-0"><span aria-current="page" title={trilha?.pessoaNome} className="block max-w-32 truncate text-foreground sm:max-w-none sm:overflow-visible sm:text-clip sm:whitespace-normal [overflow-wrap:anywhere]">{trilha?.pessoaNome || "Pessoa"}</span></li></> : null}
                </>
              ) : (
                <>
                  <li>{workspaceId || baseId ? <Link href="/workspaces">Workspaces</Link> : <span aria-current="page" className="text-foreground">Workspaces</span>}</li>
                  {workspaceId || baseId ? <li aria-hidden>/</li> : null}
                  {workspaceId ? <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeWorkspace}</span></li> : null}
                  {baseId ? <li className="max-w-24 truncate sm:max-w-none"><Link href={hrefWorkspace ? `/workspaces/${encodeURIComponent(hrefWorkspace)}` : "/workspaces"}>{nomeWorkspace}</Link></li> : null}
                  {baseId ? <li aria-hidden>/</li> : null}
                  {baseId ? <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeBase}</span></li> : null}
                </>
              )}
            </ol>
          </nav>
          {pessoa ? <MenuPessoa nome={pessoa.nome} papel={pessoa.papel} /> : null}
        </div>
        <nav aria-label="Principal" className="mt-3 flex gap-4 text-sm">
          <Link href="/workspaces" aria-current={pathname.startsWith("/workspaces") ? "page" : undefined}>Workspaces</Link>
          {podeGerirPessoas ? <Link href="/pessoas" aria-current={pessoas ? "page" : undefined}>Pessoas</Link> : null}
        </nav>
      </header>
      <main className="w-full min-w-0 flex-1 overflow-x-hidden p-4">{children}</main>
      {pessoa ? <AssistenteLauncher onSessaoEncerrada={() => replace("/login")} /> : null}
    </div>
  );
}
