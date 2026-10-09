"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ApagarColecaoDialog from "@/features/colecoes/ApagarColecaoDialog";
import RenomearColecaoSheet from "@/features/colecoes/RenomearColecaoSheet";
import { formatarData, type ColecaoResumo } from "@/features/colecoes/tipos";

/**
 * Listagem de coleções do Workspace (SPEC-0030, FR-001 / FR-015).
 *
 * Mesmo padrão de tabela semântica em largura total das demais listagens: a coluna
 * `ID` fica sempre visível, a linha inteira é um destino por mouse e teclado e as
 * ações de Renomear e Apagar ficam numa célula própria que não propaga a navegação.
 */

const COLUNAS = [
  { chave: "id", rotulo: "ID" },
  { chave: "nome", rotulo: "Nome" },
  { chave: "documentos", rotulo: "Documentos" },
  { chave: "chunks", rotulo: "Chunks" },
  { chave: "ultimo_envio_em", rotulo: "Último envio" },
] as const;

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface DataGridColecoesProps {
  workspaceId: string;
  colecoes: ColecaoResumo[];
  carregando?: boolean;
  papel?: string;
  onRenomeada?: (colecao: { id: string; nome: string }) => void;
  onApagada?: (id: string) => void;
}

export default function DataGridColecoes({
  workspaceId,
  colecoes,
  carregando = false,
  papel,
  onRenomeada,
  onApagada,
}: DataGridColecoesProps) {
  const router = useRouter();
  const [aRenomear, setARenomear] = useState<ColecaoResumo | null>(null);
  const [aApagar, setAApagar] = useState<ColecaoResumo | null>(null);
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);

  function abrir(id: string) {
    router.push(`/workspaces/${encodeURIComponent(workspaceId)}/colecoes/${encodeURIComponent(id)}`);
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
      {carregando ? (
        <IndicadorProcessamento className="px-3 py-2.5">Carregando coleções…</IndicadorProcessamento>
      ) : null}
      <div className="w-full min-w-0 overflow-x-auto">
        <table className="w-full min-w-[56rem] border-collapse text-sm" aria-busy={carregando}>
          <caption className="sr-only">Coleções do Workspace</caption>
          <thead>
            <tr className="border-b bg-muted/40 text-left">
              {COLUNAS.map((coluna) => (
                <th key={coluna.chave} scope="col" className="px-3 py-2 font-medium text-muted-foreground">
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
            ) : colecoes.length === 0 ? (
              <tr>
                <td colSpan={COLUNAS.length + 1} className="px-3 py-10 text-center">
                  <p className="font-medium">Nenhuma coleção ainda</p>
                  <p className="mt-1 text-muted-foreground">
                    {podeEscrever
                      ? "Envie os primeiros documentos para criar a coleção."
                      : "Quem tem permissão de escrita pode enviar os primeiros documentos."}
                  </p>
                  {podeEscrever ? (
                    <Button
                      type="button"
                      className="mt-4"
                      onClick={() => router.push(`/workspaces/${encodeURIComponent(workspaceId)}/enviar`)}
                    >
                      Enviar documentos
                    </Button>
                  ) : null}
                </td>
              </tr>
            ) : (
              colecoes.map((colecao) => (
                <tr
                  key={colecao.id}
                  tabIndex={0}
                  aria-label={`Coleção ${colecao.nome}`}
                  onClick={() => abrir(colecao.id)}
                  onKeyDown={(evento) => aoTeclar(evento, colecao.id)}
                  className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <td className="px-3 py-2.5 font-mono text-xs">{colecao.id}</td>
                  <td className="max-w-64 px-3 py-2.5 font-medium [overflow-wrap:anywhere]">{colecao.nome}</td>
                  <td className="px-3 py-2.5 tabular-nums">{colecao.documentos}</td>
                  <td className="px-3 py-2.5 tabular-nums">{colecao.chunks}</td>
                  <td className="px-3 py-2.5">{formatarData(colecao.ultimo_envio_em)}</td>
                  <td
                    className="px-3 py-2.5 text-right"
                    onClick={(evento) => evento.stopPropagation()}
                    onKeyDown={(evento) => evento.stopPropagation()}
                  >
                    {podeEscrever ? (
                      <div className="flex justify-end gap-1">
                        <Button type="button" variant="ghost" size="xs" onClick={() => setARenomear(colecao)}>
                          Renomear
                        </Button>
                        <Button type="button" variant="ghost" size="xs" onClick={() => setAApagar(colecao)}>
                          Apagar
                        </Button>
                      </div>
                    ) : null}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {aRenomear ? (
        <RenomearColecaoSheet
          open
          colecao={aRenomear}
          onOpenChange={(aberto) => {
            if (!aberto) setARenomear(null);
          }}
          onSaved={(salva) => {
            setARenomear(null);
            onRenomeada?.(salva);
          }}
        />
      ) : null}
      {aApagar ? (
        <ApagarColecaoDialog
          open
          colecao={aApagar}
          onOpenChange={(aberto) => {
            if (!aberto) setAApagar(null);
          }}
          onDeleted={(id) => {
            setAApagar(null);
            onApagada?.(id);
          }}
        />
      ) : null}
    </div>
  );
}
