"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { apiJson } from "@/lib/api-client";
import { clearSession, hasSession } from "@/lib/session";

/**
 * Shell das telas autenticadas (SPEC-0013, seção 10).
 *
 * Sem sessão válida, qualquer rota redireciona para `/login`. O cabeçalho
 * traz a trilha (Equipe → Workspaces → Workspace → Base) e a ação "Sair",
 * que limpa a sessão (AC-003). Não há menu lateral: a jornada é linear.
 *
 * `pronto` começa `false` no SSR e no primeiro render do cliente (evita
 * divergência de hidratação, já que `sessionStorage` não existe no servidor);
 * o efeito decide entre liberar o shell ou redirecionar ao Login.
 */
interface ContextoTrilha {
  pathname: string;
  workspaceId: string;
  workspaceNome: string;
  baseNome?: string;
}

export default function LayoutAutenticado({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [pronto, setPronto] = useState(false);
  const [contexto, setContexto] = useState<ContextoTrilha | null>(null);

  const segmentos = pathname.split("/").filter(Boolean);
  const workspaceId = segmentos[0] === "workspaces" ? segmentos[1] : undefined;
  const baseId = segmentos[0] === "execucoes" ? segmentos[1] : undefined;

  useEffect(() => {
    if (!hasSession()) {
      router.replace("/login");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- detecção única de cliente
    setPronto(true);
  }, [router]);

  useEffect(() => {
    if (!pronto || (!workspaceId && !baseId)) return;
    let ativo = true;

    async function carregarTrilha() {
      try {
        if (baseId) {
          const base = await apiJson<{ id: string; nome: string; workspace_id: string }>(
            `/api/v1/bases/${baseId}`,
          );
          const workspace = await apiJson<{ id: string; nome: string }>(
            `/api/v1/workspaces/${base.workspace_id}`,
          );
          if (ativo) {
            setContexto({
              pathname,
              workspaceId: workspace.id,
              workspaceNome: workspace.nome,
              baseNome: base.nome || base.id,
            });
          }
        } else if (workspaceId) {
          const workspace = await apiJson<{ id: string; nome: string }>(
            `/api/v1/workspaces/${workspaceId}`,
          );
          if (ativo) {
            setContexto({
              pathname,
              workspaceId: workspace.id,
              workspaceNome: workspace.nome,
            });
          }
        }
      } catch {
        // O detalhe da página mostra o erro; a trilha mantém rótulos seguros.
      }
    }

    void carregarTrilha();
    return () => {
      ativo = false;
    };
  }, [pronto, pathname, workspaceId, baseId]);

  if (!pronto) {
    return null;
  }

  function sair() {
    clearSession();
    router.replace("/login");
  }

  const trilha = contexto?.pathname === pathname ? contexto : null;
  const nomeWorkspace = trilha?.workspaceNome || (workspaceId ? `Workspace ${workspaceId}` : "Workspace");
  const nomeBase = trilha?.baseNome || (baseId ? `Base ${baseId}` : "Base");
  const hrefWorkspace = trilha?.workspaceId || workspaceId;

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-start justify-between gap-3 border-b px-4 py-3">
        <nav aria-label="Trilha" className="min-w-0 flex-1">
          <ol className="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground">
            <li><Link href="/workspaces" className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">Equipe</Link></li>
            <li aria-hidden>/</li>
            <li>
              {workspaceId || baseId ? (
                <Link href="/workspaces" className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">Workspaces</Link>
              ) : (
                <span aria-current="page" className="text-foreground">Workspaces</span>
              )}
            </li>
            {workspaceId || baseId ? <li aria-hidden>/</li> : null}
            {workspaceId ? (
              <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeWorkspace}</span></li>
            ) : null}
            {baseId ? (
              <li className="max-w-24 truncate sm:max-w-none">
                <Link href={hrefWorkspace ? `/workspaces/${encodeURIComponent(hrefWorkspace)}` : "/workspaces"} className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">{nomeWorkspace}</Link>
              </li>
            ) : null}
            {baseId ? <li aria-hidden>/</li> : null}
            {baseId ? (
              <li className="min-w-0"><span aria-current="page" className="text-foreground [overflow-wrap:anywhere]">{nomeBase}</span></li>
            ) : null}
          </ol>
        </nav>
        <Button variant="ghost" size="sm" onClick={sair}>
          Sair
        </Button>
      </header>
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}
