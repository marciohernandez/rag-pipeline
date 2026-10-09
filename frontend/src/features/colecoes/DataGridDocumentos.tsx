"use client";

import type { KeyboardEvent } from "react";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ApagarDocumentoDialog from "@/features/colecoes/ApagarDocumentoDialog";
import ChunksDocumentoSheet from "@/features/colecoes/ChunksDocumentoSheet";
import { formatarData, type DocumentoResumo } from "@/features/colecoes/tipos";
import { rotulosSplitter } from "@/lib/ingestao";

/**
 * Documentos da coleção (SPEC-0030, FR-008 / FR-009): `ID`, arquivo, chunks, divisão
 * usada e último envio. A linha abre o painel de chunks por mouse e teclado; Substituir
 * leva ao envio com a coleção pré-selecionada e Apagar pede confirmação. Member só lê.
 */

const COLUNAS = ["ID", "Arquivo", "Chunks", "Divisão", "Último envio"] as const;
const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface DataGridDocumentosProps {
  workspaceId: string;
  colecaoId: string;
  documentos: DocumentoResumo[];
  papel?: string;
  estado?: "carregando" | "erro";
  onTentarNovamente?: () => void;
  onApagado?: (id: string) => void;
}

export default function DataGridDocumentos({
  workspaceId,
  colecaoId,
  documentos,
  papel,
  estado,
  onTentarNovamente,
  onApagado,
}: DataGridDocumentosProps) {
  const router = useRouter();
  const [aVer, setAVer] = useState<DocumentoResumo | null>(null);
  const [aApagar, setAApagar] = useState<DocumentoResumo | null>(null);
  const linhas = useRef(new Map<string, HTMLTableRowElement>());
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const carregando = estado === "carregando";
  const enviar = `/workspaces/${encodeURIComponent(workspaceId)}/enviar?colecao=${encodeURIComponent(colecaoId)}`;

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, documento: DocumentoResumo) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      setAVer(documento);
    }
  }

  function fecharPainel(aberto: boolean) {
    if (aberto || !aVer) return;
    const origem = linhas.current.get(aVer.id);
    setAVer(null);
    // O painel devolve o foco à linha que o abriu (NFR-003).
    requestAnimationFrame(() => origem?.focus());
  }

  if (estado === "erro") {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
          <span>Não foi possível carregar os documentos da coleção.</span>
          <Button type="button" variant="outline" size="sm" onClick={onTentarNovamente}>
            Tentar novamente
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border" style={{ contain: "inline-size paint" }}>
      {carregando ? (
        <IndicadorProcessamento className="px-3 py-2.5">Carregando documentos…</IndicadorProcessamento>
      ) : null}
      <div className="w-full min-w-0 overflow-x-auto">
        <table className="w-full min-w-[56rem] border-collapse text-sm" aria-busy={carregando}>
          <caption className="sr-only">Documentos da coleção</caption>
          <thead>
            <tr className="border-b bg-muted/40 text-left">
              {COLUNAS.map((coluna) => (
                <th key={coluna} scope="col" className="px-3 py-2 font-medium text-muted-foreground">
                  {coluna}
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
                    <td key={coluna} className="px-3 py-2.5">
                      <Skeleton className="h-4 w-24" />
                    </td>
                  ))}
                  <td className="px-3 py-2.5" />
                </tr>
              ))
            ) : documentos.length === 0 ? (
              <tr>
                <td colSpan={COLUNAS.length + 1} className="px-3 py-10 text-center">
                  <p className="font-medium">Nenhum documento</p>
                  <p className="mt-1 text-muted-foreground">
                    {podeEscrever
                      ? "Adicione documentos para que a coleção possa ser consultada."
                      : "Quem tem permissão de escrita pode adicionar documentos."}
                  </p>
                  {podeEscrever ? (
                    <Button type="button" className="mt-4" onClick={() => router.push(enviar)}>
                      Adicionar documentos
                    </Button>
                  ) : null}
                </td>
              </tr>
            ) : (
              documentos.map((documento) => (
                <tr
                  key={documento.id}
                  ref={(no) => {
                    if (no) linhas.current.set(documento.id, no);
                    else linhas.current.delete(documento.id);
                  }}
                  tabIndex={0}
                  aria-label={`Documento ${documento.nome_arquivo}`}
                  onClick={() => setAVer(documento)}
                  onKeyDown={(evento) => aoTeclar(evento, documento)}
                  className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <td className="px-3 py-2.5 font-mono text-xs">{documento.id}</td>
                  <td className="max-w-64 px-3 py-2.5 font-medium [overflow-wrap:anywhere]">{documento.nome_arquivo}</td>
                  <td className="px-3 py-2.5 tabular-nums">{documento.chunks}</td>
                  <td className="px-3 py-2.5">
                    {rotulosSplitter[documento.chunking?.splitter ?? ""] ?? documento.chunking?.splitter ?? "—"}
                  </td>
                  <td className="px-3 py-2.5">{formatarData(documento.ultimo_envio_em)}</td>
                  <td
                    className="px-3 py-2.5 text-right"
                    onClick={(evento) => evento.stopPropagation()}
                    onKeyDown={(evento) => evento.stopPropagation()}
                  >
                    {podeEscrever ? (
                      <div className="flex justify-end gap-1">
                        <Button type="button" variant="ghost" size="xs" onClick={() => router.push(enviar)}>
                          Substituir
                        </Button>
                        <Button type="button" variant="ghost" size="xs" onClick={() => setAApagar(documento)}>
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

      {aVer ? <ChunksDocumentoSheet open colecaoId={colecaoId} documento={aVer} onOpenChange={fecharPainel} /> : null}
      {aApagar ? (
        <ApagarDocumentoDialog
          open
          colecaoId={colecaoId}
          documento={aApagar}
          onOpenChange={(aberto) => {
            if (!aberto) setAApagar(null);
          }}
          onDeleted={(id) => {
            setAApagar(null);
            onApagado?.(id);
          }}
        />
      ) : null}
    </div>
  );
}
