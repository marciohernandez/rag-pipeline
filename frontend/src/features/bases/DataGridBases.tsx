"use client";

import type { KeyboardEvent } from "react";
import { useRouter } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";

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
}

const COLUNAS = [
  { chave: "id", rotulo: "ID" },
  { chave: "origem", rotulo: "Origem" },
  { chave: "status", rotulo: "Status" },
  { chave: "documentos", rotulo: "Documentos" },
  { chave: "chunks", rotulo: "Chunks" },
  { chave: "ultima_atualizacao", rotulo: "Última atualização" },
] as const;

function formatarData(iso: string): string {
  const data = new Date(iso);
  return Number.isNaN(data.getTime())
    ? iso
    : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

interface DataGridBasesProps {
  bases: BaseResumo[];
  carregando?: boolean;
}

export default function DataGridBases({
  bases,
  carregando = false,
}: DataGridBasesProps) {
  const router = useRouter();

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
    <div className="w-full overflow-x-auto rounded-lg border">
      <table className="w-full border-collapse text-sm">
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
                <td
                  className="px-3 py-2.5 text-right"
                  onClick={(evento) => evento.stopPropagation()}
                >
                  {/* Ação de apagar por linha entra no T027 (ExcluirBaseDialog). */}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
