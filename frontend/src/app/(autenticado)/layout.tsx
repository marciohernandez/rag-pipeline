"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import MenuPessoa from "@/features/auth/MenuPessoa";
import { ApiError, apiJson } from "@/lib/api-client";
import { hasSession, saveIdentity, type PessoaSessao } from "@/lib/session";

interface ContextoTrilha {
  pathname: string;
  workspaceId: string;
  workspaceNome: string;
  baseNome?: string;
}

export default function LayoutAutenticado({ children }: { children: ReactNode }) {
  const { replace } = useRouter();
  const pathname = usePathname();
  const [pronto, setPronto] = useState(false);
  const [pessoa, setPessoa] = useState<PessoaSessao | null>(null);
  const [contexto, setContexto] = useState<ContextoTrilha | null>(null);

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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- libera o shell só no cliente
    setPronto(true);
    apiJson<PessoaSessao>("/api/v1/auth/me")
      .then((identidade) => {
        if (!ativo) return;
        saveIdentity(identidade);
        setPessoa(identidade);
        if (identidade.precisa_trocar_senha) replace("/nova-senha");
      })
      .catch((falha) => {
        if (falha instanceof ApiError && falha.unauthorized) replace("/login");
      });
    return () => { ativo = false; };
  }, [replace]);

  useEffect(() => {
    if (!pronto || (!workspaceId && !baseId)) return;
    let ativo = true;
    async function carregarTrilha() {
      try {
        if (baseId) {
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
  }, [pronto, pathname, workspaceId, baseId]);

  if (!pronto) return null;

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
                  {pessoaId ? <><li aria-hidden>/</li><li><span aria-current="page" className="text-foreground">Pessoa</span></li></> : null}
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
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}
