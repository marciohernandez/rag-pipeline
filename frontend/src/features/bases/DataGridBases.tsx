"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ExcluirBaseDialog from "@/features/bases/ExcluirBaseDialog";

/**
 * Listagem de bases do projeto ativo (SPEC-0013, US-002 / AC-004 / AC-017).
 *
 * Tabela semântica em largura total: a coluna `ID` fica sempre visível, cada
 * linha é um destino acessível para o detalhe (mouse e teclado) e as ações
 * por linha (apagar, T027) ficam numa célula própria que não propaga a
 * navegação.
 *
 * O catálogo gratuito ReUI traz um Data Grid sobre TanStack Table voltado a
 * grandes volumes (virtualização, DnD, seleção); para esta demonstração —
 * poucas bases por projeto e o requisito de linha inteira como link acessível
 * por teclado (AC-017) — uma tabela semântica entrega o mesmo contrato com
 * menos superfície. Registrado em `INTERFACE.md`.
 */

export interface BaseResumo {
  id: string;
  origem: string;
  status: string;
  documentos: number;
  chunks: number;
  ultima_atualizacao: string;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
}

const COLUNAS = [
  { chave: "id", rotulo: "ID" },
  { chave: "origem", rotulo: "Origem" },
  { chave: "status", rotulo: "Status" },
  { chave: "documentos", rotulo: "Documentos" },
  { chave: "chunks", rotulo: "Chunks" },
  { chave: "ultima_atualizacao", rotulo: "Última atualização" },
  { chave: "criado_por", rotulo: "Criada por" },
] as const;

function formatarData(iso: string): string {
  const data = new Date(iso);
  return Number.isNaN(data.getTime())
    ? iso
    : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

function autor(criadoPor: BaseResumo["criado_por"]): string {
  if (!criadoPor) return "Autor não identificado";
  return `${criadoPor.nome}${criadoPor.desativada ? " (desativada)" : ""}`;
}

interface DataGridBasesProps {
  bases: BaseResumo[];
  carregando?: boolean;
  papel?: string;
  onBaseApagada?: (id: string) => void;
}

export default function DataGridBases({
  bases,
  carregando = false,
  papel,
  onBaseApagada,
}: DataGridBasesProps) {
  const router = useRouter();
  const [aApagar, setAApagar] = useState<BaseResumo | null>(null);

  const podeApagar = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  function abrir(id: string) {
    router.push(`/execucoes/${id}`);
  }

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      abrir(id);
    }
  }

  return (
    <div
      className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border"
      style={{ contain: "inline-size paint" }}
    >
      <div className="w-full min-w-0 overflow-x-auto">
      <table className="w-full min-w-[72rem] border-collapse text-sm" aria-busy={carregando}>
        <caption className="sr-only">Bases do projeto ativo</caption>
        <thead>
          <tr className="border-b bg-muted/40 text-left">
            {COLUNAS.map((coluna) => (
              <th
                key={coluna.chave}
                scope="col"
                className="px-3 py-2 font-medium text-muted-foreground"
              >
                {coluna.rotulo}
              </th>
            ))}
            <th scope="col" className="px-3 py-2 font-medium text-muted-foreground">
              <span className="sr-only">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {carregando ? (
            Array.from({ length: 3 }).map((_, indice) => (
              <tr key={indice} className="border-b last:border-0">
                {COLUNAS.map((coluna) => (
                  <td key={coluna.chave} className="px-3 py-2.5">
                    <Skeleton className="h-4 w-24" />
                  </td>
                ))}
                <td className="px-3 py-2.5" />
              </tr>
            ))
          ) : bases.length === 0 ? (
            <tr>
              <td
                colSpan={COLUNAS.length + 1}
                className="px-3 py-10 text-center text-muted-foreground"
              >
                Nenhuma base ainda. Envie a primeira base para começar.
              </td>
            </tr>
          ) : (
            bases.map((base) => (
              <tr
                key={base.id}
                tabIndex={0}
                aria-label={`Base ${base.id}`}
                onClick={() => abrir(base.id)}
                onKeyDown={(evento) => aoTeclar(evento, base.id)}
                className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
              >
                <td className="px-3 py-2.5 font-mono text-xs">{base.id}</td>
                <td className="px-3 py-2.5">{base.origem}</td>
                <td className="px-3 py-2.5">{base.status}</td>
                <td className="px-3 py-2.5 tabular-nums">{base.documentos}</td>
                <td className="px-3 py-2.5 tabular-nums">{base.chunks}</td>
                <td className="px-3 py-2.5">{formatarData(base.ultima_atualizacao)}</td>
                <td className="max-w-64 px-3 py-2.5 text-muted-foreground [overflow-wrap:anywhere]">
                  {autor(base.criado_por)}
                </td>
                <td
                  className="px-3 py-2.5 text-right"
                  onClick={(evento) => evento.stopPropagation()}
                  onKeyDown={(evento) => evento.stopPropagation()}
                >
                  {podeApagar ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      onClick={() => setAApagar(base)}
                    >
                      Apagar
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {carregando ? <span className="sr-only">Carregando Bases…</span> : null}
      </div>

      {aApagar ? (
        <ExcluirBaseDialog
          open
          onOpenChange={(aberto) => {
            if (!aberto) setAApagar(null);
          }}
          base={{ id: aApagar.id, nome: aApagar.id }}
          papel={papel}
          onDeleted={(id) => {
            setAApagar(null);
            onBaseApagada?.(id);
          }}
        />
      ) : null}
    </div>
  );
}
