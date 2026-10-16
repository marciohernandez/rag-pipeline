"use client";

import type { KeyboardEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { baixarMarkdown, reenviarDocumento } from "@/features/conversao/acoesDocumento";
import ApagarDocumentoDialog from "@/features/conversao/ApagarDocumentoDialog";
import PainelLoteConversao from "@/features/conversao/PainelLoteConversao";
import { AcaoReprocessarIa } from "@/features/conversao/ReprocessarIaDialog";
import SeloRevisarDocumento from "@/features/conversao/SeloRevisarDocumento";
import type { AvisoConversao } from "@/features/conversao/situacao";
import { rotuloSituacao, SITUACOES_ATIVAS, variantePorSituacao } from "@/features/conversao/situacao";
import { apiJson } from "@/lib/api-client";

/**
 * Listagem de documentos convertidos do Workspace (SPEC-0023, US-005 / FR-009).
 *
 * Uma linha por documento (e não por lote), modelada em `DataGridColecoes`: a
 * coluna `ID` fica sempre visível, a linha inteira abre o painel do lote do
 * documento por mouse e teclado, e as ações Baixar e Reenviar ficam numa célula
 * própria que não propaga a abertura. Não há rota de detalhe do lote (seção 10),
 * então o painel abre num `Sheet`.
 */

export interface DocumentoConversaoResumo {
  id: string;
  nome_arquivo: string;
  formato: string;
  tamanho_bytes: number;
  situacao: "fila" | "processando" | "aguardando_abas" | "concluido" | "falhou";
  abas?: string[] | null;
  abas_selecionadas?: string[] | null;
  origem_url?: string | null;
  reprocessado_ia_em?: string | null;
  reprocessando_ia?: boolean;
  erro: string | null;
  avisos?: AvisoConversao[];
  limpeza_situacao?: string | null;
  exclusoes?: number;
  duvidas?: number;
  limpeza_motivo?: string | null;
  criado_em: string;
  concluido_em: string | null;
}

export interface LoteConversaoResumo {
  id: string;
  workspace_id: string;
  situacao:
    | "processando"
    | "aguardando_dominio"
    | "limpando"
    | "concluido"
    | "concluido_com_falhas";
  limpeza?: { total: number; concluidos: number; falhas: number };
  criado_em: string;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
  documentos: DocumentoConversaoResumo[];
}

const COLUNAS = [
  { chave: "id", rotulo: "ID" },
  { chave: "arquivo", rotulo: "Arquivo" },
  { chave: "formato", rotulo: "Formato" },
  { chave: "situacao", rotulo: "Situação" },
  { chave: "lote", rotulo: "Lote" },
  { chave: "criado_em", rotulo: "Criado em" },
  { chave: "criado_por", rotulo: "Criado por" },
] as const;

const PAPEIS_DE_ESCRITA = ["owner", "admin"];
const INTERVALO_POLLING_MS = 3000;

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

/** Lote sem o documento apagado, com a situação recalculada como no backend (FR-010). */
function semDocumento(lote: LoteConversaoResumo, documentoId: string): LoteConversaoResumo {
  const documentos = lote.documentos.filter((documento) => documento.id !== documentoId);
  const situacoes = documentos.map((documento) => documento.situacao);
  const situacao = situacoes.some((s) => SITUACOES_ATIVAS.includes(s))
    ? "processando"
    : situacoes.includes("falhou")
      ? "concluido_com_falhas"
      : "concluido";
  return { ...lote, documentos, situacao };
}

interface DataGridLotesConversaoProps {
  lotes: LoteConversaoResumo[];
  carregando?: boolean;
  papel?: string;
  onLoteAtualizado?: (lote: LoteConversaoResumo) => void;
  onConverter?: () => void;
}

export default function DataGridLotesConversao({
  lotes,
  carregando = false,
  papel,
  onLoteAtualizado,
  onConverter,
}: DataGridLotesConversaoProps) {
  const [aberto, setAberto] = useState<string | null>(null);
  const [reenviando, setReenviando] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aApagar, setAApagar] = useState<{ lote: LoteConversaoResumo; documento: DocumentoConversaoResumo } | null>(null);
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const onLoteAtualizadoRef = useRef(onLoteAtualizado);
  useEffect(() => {
    onLoteAtualizadoRef.current = onLoteAtualizado;
  }, [onLoteAtualizado]);

  const linhas = useMemo(
    () =>
      [...lotes]
        .sort((a, b) => b.criado_em.localeCompare(a.criado_em))
        .flatMap((lote) => lote.documentos.map((documento) => ({ lote, documento }))),
    [lotes],
  );
  const idsAtivos = lotes
    .filter((lote) => lote.documentos.some((d) => SITUACOES_ATIVAS.includes(d.situacao)))
    .map((lote) => lote.id)
    .join(",");
  const loteAberto = lotes.find((lote) => lote.id === aberto) ?? null;

  // A lista acompanha o processamento sem exigir abrir o lote (US-002 / US-005).
  useEffect(() => {
    if (!idsAtivos) return;
    let cancelado = false;
    const intervalo = setInterval(() => {
      for (const id of idsAtivos.split(",")) {
        apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${id}`)
          .then((atualizado) => {
            if (!cancelado) onLoteAtualizadoRef.current?.(atualizado);
          })
          .catch(() => {
            // Falha pontual de polling; o próximo ciclo tenta de novo.
          });
      }
    }, INTERVALO_POLLING_MS);
    return () => {
      cancelado = true;
      clearInterval(intervalo);
    };
  }, [idsAtivos]);

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, loteId: string) {
    if (evento.target !== evento.currentTarget) return;
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      setAberto(loteId);
    }
  }

  async function baixar(lote: LoteConversaoResumo, documento: DocumentoConversaoResumo) {
    setErro(null);
    try {
      await baixarMarkdown(lote.id, documento.id, documento.nome_arquivo);
    } catch {
      setErro("Não foi possível baixar o Markdown. Tente novamente.");
    }
  }

  async function reenviar(lote: LoteConversaoResumo, documento: DocumentoConversaoResumo) {
    setErro(null);
    setReenviando(documento.id);
    try {
      const atualizado = await reenviarDocumento(lote.id, documento.id);
      onLoteAtualizado?.(atualizado);
    } catch {
      setErro("Não foi possível reenviar o documento. Tente novamente.");
    } finally {
      setReenviando(null);
    }
  }

  return (
    <div className="flex w-full min-w-0 max-w-full flex-col gap-2">
      <div
        className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border"
        style={{ contain: "inline-size paint" }}
      >
        <div className="w-full min-w-0 overflow-x-auto">
          <table className="w-full min-w-[60rem] border-collapse text-sm" aria-busy={carregando}>
            <caption className="sr-only">Documentos convertidos do Workspace</caption>
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
                <th scope="col" className="px-3 py-2 text-right font-medium text-muted-foreground">
                  Ações
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
              ) : linhas.length === 0 ? (
                <tr>
                  <td colSpan={COLUNAS.length + 1} className="px-3 py-10 text-center">
                    <p className="font-medium">Nenhum documento convertido ainda</p>
                    <p className="mt-1 text-muted-foreground">
                      {podeEscrever
                        ? "Converta o primeiro documento para começar."
                        : "Quem tem permissão de escrita pode converter os primeiros documentos."}
                    </p>
                    {podeEscrever && onConverter ? (
                      <Button type="button" className="mt-4" onClick={onConverter}>
                        Converter documentos
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ) : (
                linhas.map(({ lote, documento }) => (
                  <tr
                    key={`${lote.id}:${documento.id}`}
                    tabIndex={0}
                    aria-label={`Documento ${documento.nome_arquivo}`}
                    onClick={() => setAberto(lote.id)}
                    onKeyDown={(evento) => aoTeclar(evento, lote.id)}
                    className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs">{documento.id}</td>
                    <td className="max-w-64 px-3 py-2.5 font-medium [overflow-wrap:anywhere]">
                      {documento.nome_arquivo}
                    </td>
                    <td className="px-3 py-2.5 uppercase">{documento.formato}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant={variantePorSituacao(documento.situacao)}>
                        {documento.reprocessando_ia ? "Reprocessando com IA" : rotuloSituacao(documento.situacao)}
                      </Badge>
                      <SeloRevisarDocumento avisos={documento.avisos ?? []} />
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs">{lote.id}</td>
                    <td className="px-3 py-2.5">{formatarData(documento.criado_em)}</td>
                    <td className="max-w-64 px-3 py-2.5 text-muted-foreground [overflow-wrap:anywhere]">
                      {autor(lote.criado_por)}
                    </td>
                    <td
                      className="px-3 py-2.5 text-right"
                      onClick={(evento) => evento.stopPropagation()}
                      onKeyDown={(evento) => evento.stopPropagation()}
                    >
                      <div className="flex justify-end gap-1">
                        {documento.situacao === "concluido" ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            aria-label={`Baixar ${documento.nome_arquivo}`}
                            onClick={() => baixar(lote, documento)}
                          >
                            Baixar
                          </Button>
                        ) : null}
                        {documento.situacao === "concluido" && podeEscrever && <AcaoReprocessarIa loteId={lote.id} documento={documento} onReprocessado={(atualizado)=>onLoteAtualizado?.(atualizado)} />}
                        {documento.situacao === "falhou" && podeEscrever ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            aria-label={`Reenviar ${documento.nome_arquivo}`}
                            onClick={() => reenviar(lote, documento)}
                            disabled={reenviando === documento.id}
                          >
                            {reenviando === documento.id ? "Reenviando…" : "Reenviar"}
                          </Button>
                        ) : null}
                        {podeEscrever && ["concluido", "falhou"].includes(documento.situacao) ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            aria-label={`Apagar ${documento.nome_arquivo}`}
                            onClick={() => setAApagar({ lote, documento })}
                          >
                            Apagar
                          </Button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {carregando ? <span className="sr-only">Carregando documentos…</span> : null}
        </div>
      </div>
      {erro ? (
        <p role="alert" className="text-sm text-destructive">
          {erro}
        </p>
      ) : null}

      {aApagar ? (
        <ApagarDocumentoDialog
          open
          loteId={aApagar.lote.id}
          documento={aApagar.documento}
          onOpenChange={(aberto) => {
            if (!aberto) setAApagar(null);
          }}
          onDeleted={(documentoId) => {
            const { lote } = aApagar;
            setAApagar(null);
            onLoteAtualizado?.(semDocumento(lote, documentoId));
          }}
        />
      ) : null}

      <Sheet open={loteAberto !== null} onOpenChange={(open) => !open && setAberto(null)}>
        <SheetContent side="right" className="overflow-y-auto sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Lote de conversão</SheetTitle>
            <SheetDescription>
              {loteAberto ? `Lote ${loteAberto.id} — documentos e download do pacote.` : null}
            </SheetDescription>
          </SheetHeader>
          {loteAberto ? (
            <div className="px-4 pb-4">
              <PainelLoteConversao lote={loteAberto} papel={papel} onAtualizado={onLoteAtualizado} />
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}
