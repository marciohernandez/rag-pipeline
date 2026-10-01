"use client";

import type { KeyboardEvent } from "react";
import { Fragment, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import PainelLoteConversao from "@/features/conversao/PainelLoteConversao";

/**
 * Listagem de lotes de conversão de documentos do Workspace (SPEC-0023, US-002).
 *
 * Tabela semântica modelada em `DataGridBases`: a coluna `ID` fica sempre
 * visível e a largura é contida com rolagem horizontal interna no mobile.
 * Diferente de `DataGridBases`, a linha não navega — não há rota própria
 * para o detalhe de um lote (seção 10) — ela expande para mostrar
 * `PainelLoteConversao` logo abaixo, dentro da própria tabela.
 */

export interface DocumentoConversaoResumo {
  id: string;
  nome_arquivo: string;
  formato: string;
  tamanho_bytes: number;
  situacao: "fila" | "processando" | "concluido" | "falhou";
  erro: string | null;
  criado_em: string;
  concluido_em: string | null;
}

export interface LoteConversaoResumo {
  id: string;
  workspace_id: string;
  situacao: "processando" | "concluido" | "concluido_com_falhas";
  criado_em: string;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
  documentos: DocumentoConversaoResumo[];
}

const COLUNAS = [
  { chave: "id", rotulo: "ID" },
  { chave: "situacao", rotulo: "Situação" },
  { chave: "documentos", rotulo: "Documentos" },
  { chave: "criado_em", rotulo: "Criado em" },
  { chave: "criado_por", rotulo: "Criado por" },
] as const;

function formatarData(iso: string): string {
  const data = new Date(iso);
  return Number.isNaN(data.getTime())
    ? iso
    : data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function autor(criadoPor: LoteConversaoResumo["criado_por"]): string {
  if (!criadoPor) return "Autor não identificado";
  return `${criadoPor.nome}${criadoPor.desativada ? " (desativada)" : ""}`;
}

interface DataGridLotesConversaoProps {
  lotes: LoteConversaoResumo[];
  carregando?: boolean;
  papel?: string;
  onLoteAtualizado?: (lote: LoteConversaoResumo) => void;
}

export default function DataGridLotesConversao({
  lotes,
  carregando = false,
  papel,
  onLoteAtualizado,
}: DataGridLotesConversaoProps) {
  const [expandido, setExpandido] = useState<string | null>(null);

  function alternar(id: string) {
    setExpandido((atual) => (atual === id ? null : id));
  }

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      alternar(id);
    }
  }

  return (
    <div
      className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border"
      style={{ contain: "inline-size paint" }}
    >
      <div className="w-full min-w-0 overflow-x-auto">
        <table className="w-full min-w-[60rem] border-collapse text-sm" aria-busy={carregando}>
          <caption className="sr-only">Lotes de conversão de documentos do Workspace</caption>
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
                </tr>
              ))
            ) : lotes.length === 0 ? (
              <tr>
                <td
                  colSpan={COLUNAS.length}
                  className="px-3 py-10 text-center text-muted-foreground"
                >
                  Nenhum documento convertido ainda. Converta o primeiro documento para começar.
                </td>
              </tr>
            ) : (
              lotes.map((lote) => (
                <Fragment key={lote.id}>
                  <tr
                    tabIndex={0}
                    aria-expanded={expandido === lote.id}
                    aria-controls={`lote-painel-${lote.id}`}
                    aria-label={`Lote ${lote.id}`}
                    onClick={() => alternar(lote.id)}
                    onKeyDown={(evento) => aoTeclar(evento, lote.id)}
                    className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <td className="px-3 py-2.5 font-mono text-xs">{lote.id}</td>
                    <td className="px-3 py-2.5">{lote.situacao}</td>
                    <td className="px-3 py-2.5 tabular-nums">{lote.documentos.length}</td>
                    <td className="px-3 py-2.5">{formatarData(lote.criado_em)}</td>
                    <td className="max-w-64 px-3 py-2.5 text-muted-foreground [overflow-wrap:anywhere]">
                      {autor(lote.criado_por)}
                    </td>
                  </tr>
                  {expandido === lote.id ? (
                    <tr className="border-b last:border-0">
                      <td colSpan={COLUNAS.length} id={`lote-painel-${lote.id}`} className="px-3 py-3">
                        <PainelLoteConversao
                          lote={lote}
                          papel={papel}
                          onAtualizado={onLoteAtualizado}
                        />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
        {carregando ? <span className="sr-only">Carregando lotes de conversão…</span> : null}
      </div>
    </div>
  );
}
