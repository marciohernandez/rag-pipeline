"use client";

import type { KeyboardEvent } from "react";
import { useRouter } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";

export interface WorkspaceResumo {
  id: string;
  nome: string;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
}

function autor(criadoPor: WorkspaceResumo["criado_por"]): string {
  if (!criadoPor) return "Autor não identificado";
  return criadoPor.desativada ? `${criadoPor.nome} (desativada)` : criadoPor.nome;
}

interface DataGridWorkspacesProps {
  workspaces: WorkspaceResumo[];
  carregando?: boolean;
  podeCriar?: boolean;
}

/**
 * Lista de Workspaces do tenant/projeto ativo (SPEC-0019, US-001/US-004).
 *
 * Mantém a coluna ID sempre visível e abre o detalhe por clique, Enter ou
 * Espaço. A tabela usa a mesma densidade e os mesmos tokens de DataGridBases,
 * evitando introduzir outra linguagem visual para o mesmo tipo de navegação.
 */
export default function DataGridWorkspaces({
  workspaces,
  carregando = false,
  podeCriar = false,
}: DataGridWorkspacesProps) {
  const router = useRouter();

  function abrir(id: string) {
    router.push(`/workspaces/${id}`);
  }

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      abrir(id);
    }
  }

  return (
    <div className="w-full overflow-x-auto rounded-lg border">
      <table
        className="w-full border-collapse text-sm"
        aria-busy={carregando}
      >
        <caption className="sr-only">Workspaces do projeto ativo</caption>
        <thead>
          <tr className="border-b bg-muted/40 text-left">
            <th
              scope="col"
              className="w-[22rem] px-3 py-2 font-medium text-muted-foreground"
            >
              ID
            </th>
            <th scope="col" className="px-3 py-2 font-medium text-muted-foreground">
              Nome
            </th>
            <th scope="col" className="px-3 py-2 font-medium text-muted-foreground">
              Criada por
            </th>
          </tr>
        </thead>
        <tbody>
          {carregando ? (
            Array.from({ length: 3 }).map((_, indice) => (
              <tr key={indice} className="border-b last:border-0">
                <td className="px-3 py-2.5">
                  <Skeleton className="h-4 w-48 max-w-full" />
                </td>
                <td className="px-3 py-2.5">
                  <Skeleton className="h-4 w-56 max-w-full" />
                </td>
                <td className="px-3 py-2.5"><Skeleton className="h-4 w-32" /></td>
              </tr>
            ))
          ) : workspaces.length === 0 ? (
            <tr>
              <td colSpan={3} className="px-3 py-10 text-center text-muted-foreground">
                <span className="block font-medium text-foreground">
                  Nenhum Workspace ainda
                </span>
                <span className="mt-1 block">
                  {podeCriar
                    ? "Crie o primeiro Workspace para organizar suas Bases."
                    : "Quando um Workspace for criado, ele aparecerá aqui."}
                </span>
              </td>
            </tr>
          ) : (
            workspaces.map((workspace) => (
              <tr
                key={workspace.id}
                tabIndex={0}
                aria-label={`Workspace ${workspace.nome}`}
                onClick={() => abrir(workspace.id)}
                onKeyDown={(evento) => aoTeclar(evento, workspace.id)}
                className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
              >
                <td className="px-3 py-2.5 font-mono text-xs">{workspace.id}</td>
                <td className="px-3 py-2.5 font-medium">{workspace.nome}</td>
                <td className="px-3 py-2.5 text-muted-foreground">{autor(workspace.criado_por)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {carregando ? <span className="sr-only">Carregando Workspaces…</span> : null}
    </div>
  );
}
