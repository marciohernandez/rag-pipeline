"use client";

import { useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import AvisosLimpeza from "@/features/conversao/AvisosLimpeza";
import ConfirmarDominio from "@/features/conversao/ConfirmarDominio";
import SelecaoAbas from "@/features/conversao/SelecaoAbas";
import { AcaoReprocessarIa } from "@/features/conversao/ReprocessarIaDialog";
import SeloRevisarDocumento from "@/features/conversao/SeloRevisarDocumento";
import { baixar, baixarMarkdown, reenviarDocumento } from "@/features/conversao/acoesDocumento";
import {
  rotuloLimpeza,
  rotuloSituacao,
  motivoAviso,
  SITUACOES_ATIVAS,
  SITUACOES_LIMPEZA_ATIVAS,
  varianteLimpeza,
  variantePorSituacao,
} from "@/features/conversao/situacao";
import { apiJson } from "@/lib/api-client";

/**
 * Situação por documento, download individual/pacote e reenviar (SPEC-0023, US-002/003/004).
 *
 * Modelado em `PainelProgresso`: mesmas variantes de `Badge` por situação e
 * mesma região `role="status"`/`aria-live` para anunciar a mudança sem exigir
 * foco manual. Usado tanto dentro de `ConversaoSheet` (logo após o envio)
 * quanto na linha expandida de `DataGridLotesConversao` (lote já existente).
 */

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

function plural(quantidade: number, singular: string, mais: string): string {
  return `${quantidade} ${quantidade === 1 ? singular : mais}`;
}
const INTERVALO_POLLING_MS = 3000;

interface PainelLoteConversaoProps {
  lote: LoteConversaoResumo;
  papel?: string;
  onAtualizado?: (lote: LoteConversaoResumo) => void;
}

export default function PainelLoteConversao({
  lote,
  papel,
  onAtualizado,
}: PainelLoteConversaoProps) {
  const [erro, setErro] = useState<string | null>(null);
  const [baixandoTodos, setBaixandoTodos] = useState(false);
  const [reenviando, setReenviando] = useState<string | null>(null);
  const onAtualizadoRef = useRef(onAtualizado);
  useEffect(() => {
    onAtualizadoRef.current = onAtualizado;
  }, [onAtualizado]);

  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const ativo =
    lote.situacao === "limpando" ||
    lote.documentos.some((documento) => SITUACOES_ATIVAS.includes(documento.situacao));
  const aguardandoDominio = lote.situacao === "aguardando_dominio";
  const comLimpeza = lote.documentos.some((documento) => documento.limpeza_situacao);
  const limpezaTerminou =
    comLimpeza &&
    !aguardandoDominio &&
    lote.situacao !== "limpando" &&
    !lote.documentos.some((d) => SITUACOES_LIMPEZA_ATIVAS.includes(d.limpeza_situacao ?? ""));
  const [iaPermitida, setIaPermitida] = useState(true);
  const [baixandoRelatorio, setBaixandoRelatorio] = useState(false);
  const [tentandoDeNovo, setTentandoDeNovo] = useState<string | null>(null);
  const temConcluido = lote.documentos.some((documento) => documento.situacao === "concluido");

  useEffect(() => {
    if (!ativo) return;
    let cancelado = false;
    const intervalo = setInterval(() => {
      apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${lote.id}`)
        .then((atualizado) => {
          if (!cancelado) onAtualizadoRef.current?.(atualizado);
        })
        .catch(() => {
          // Falha pontual de polling; o próximo ciclo tenta de novo.
        });
    }, INTERVALO_POLLING_MS);
    return () => {
      cancelado = true;
      clearInterval(intervalo);
    };
  }, [ativo, lote.id]);

  async function baixarDocumento(documento: LoteConversaoResumo["documentos"][number]) {
    setErro(null);
    try {
      await baixarMarkdown(lote.id, documento.id, documento.nome_arquivo);
    } catch {
      setErro("Não foi possível baixar o Markdown. Tente novamente.");
    }
  }

  async function baixarTodos() {
    setErro(null);
    setBaixandoTodos(true);
    try {
      await baixar(`/api/v1/conversoes/${lote.id}/pacote`, `lote-${lote.id}.zip`);
    } catch {
      setErro("Não foi possível baixar o pacote. Tente novamente.");
    } finally {
      setBaixandoTodos(false);
    }
  }

  useEffect(() => {
    if (!podeEscrever || (!comLimpeza && !aguardandoDominio)) return;
    let cancelado = false;
    (async () => {
      try {
        const analise = await apiJson<{ ia_externa_permitida?: boolean }>(
          `/api/v1/workspaces/${lote.workspace_id}/analise-ia`,
        );
        if (!cancelado && typeof analise?.ia_externa_permitida === "boolean") {
          setIaPermitida(analise.ia_externa_permitida);
        }
      } catch {
        // Sem a configuração o aviso de IA não aparece; a limpeza segue normalmente.
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [podeEscrever, comLimpeza, aguardandoDominio, lote.workspace_id]);

  async function baixarRelatorio() {
    setErro(null);
    setBaixandoRelatorio(true);
    try {
      await baixar(`/api/v1/conversoes/${lote.id}/relatorio`, `relatorio-do-lote-${lote.id}.md`);
    } catch {
      setErro("Não foi possível baixar o relatório. Tente novamente.");
    } finally {
      setBaixandoRelatorio(false);
    }
  }

  async function limparDeNovo(documentoId: string) {
    setErro(null);
    setTentandoDeNovo(documentoId);
    try {
      await apiJson(`/api/v1/conversoes/${lote.id}/documentos/${documentoId}/limpar`, {
        method: "POST",
      });
      onAtualizadoRef.current?.(await apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${lote.id}`));
    } catch {
      setErro("Não foi possível tentar a limpeza de novo. Tente novamente.");
    } finally {
      setTentandoDeNovo(null);
    }
  }

  async function reenviar(documentoId: string) {
    setErro(null);
    setReenviando(documentoId);
    try {
      const atualizado = await reenviarDocumento(lote.id, documentoId);
      onAtualizadoRef.current?.(atualizado);
    } catch {
      setErro("Não foi possível reenviar o documento. Tente novamente.");
    } finally {
      setReenviando(null);
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-lg border p-4" role="status" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Situação do lote</span>
          <Badge variant={variantePorSituacao(lote.situacao)}>{rotuloSituacao(lote.situacao, "lote")}</Badge>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={baixarTodos}
          disabled={!temConcluido || baixandoTodos}
        >
          {baixandoTodos ? "Baixando…" : "Baixar todos"}
        </Button>
      </div>

      {ativo ? (
        <p className="text-sm text-muted-foreground">
          Acompanhando o processamento… a lista é atualizada automaticamente.
          {lote.limpeza?.total
            ? ` Limpeza: ${lote.limpeza.concluidos} de ${lote.limpeza.total} documentos.`
            : ""}
        </p>
      ) : null}

      {podeEscrever && (aguardandoDominio || comLimpeza) ? (
        <AvisosLimpeza
          workspaceId={lote.workspace_id}
          iaPermitida={iaPermitida}
          dominioConfirmado={!aguardandoDominio}
          onConfirmarDominio={() => document.getElementById("confirmar-dominio")?.focus()}
        />
      ) : null}
      {podeEscrever && aguardandoDominio ? (
        <ConfirmarDominio
          loteId={lote.id}
          onConfirmado={(atualizado) => onAtualizadoRef.current?.(atualizado)}
        />
      ) : null}

      <ul className="flex flex-col gap-2">
        {lote.documentos.map((documento) => (
          <li
            key={documento.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2"
          >
            <div className="flex min-w-0 max-w-full flex-col gap-1">
              <span className="text-sm font-medium [overflow-wrap:anywhere]">
                {documento.nome_arquivo}
              </span>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={variantePorSituacao(documento.situacao)}>
                  {documento.reprocessando_ia ? "Reprocessando com IA" : rotuloSituacao(documento.situacao)}
                </Badge>
                <SeloRevisarDocumento avisos={documento.avisos ?? []} />
                {documento.situacao === "falhou" && documento.erro ? (
                  <span className="text-xs text-destructive [overflow-wrap:anywhere]">
                    {documento.erro}
                  </span>
                ) : null}
              </div>
              {documento.situacao === "aguardando_abas" && podeEscrever && <SelecaoAbas abas={documento.abas ?? []} onConfirmar={async (abas) => {
                await apiJson(`/api/v1/conversoes/${lote.id}/documentos/${documento.id}/abas`, {method: "POST", body: JSON.stringify({abas}), headers: {"Content-Type": "application/json"}});
                onAtualizadoRef.current?.(await apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${lote.id}`));
              }} />}
              {documento.limpeza_situacao ? (
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant={varianteLimpeza(documento.limpeza_situacao)}>
                    {rotuloLimpeza(documento.limpeza_situacao)}
                  </Badge>
                  <span>{plural(documento.exclusoes ?? 0, "exclusão", "exclusões")}</span>
                  <span>{plural(documento.duvidas ?? 0, "dúvida", "dúvidas")}</span>
                  {documento.limpeza_motivo ? (
                    <span className={documento.limpeza_situacao === "falhou" ? "text-destructive" : ""}>
                      {documento.limpeza_motivo}
                    </span>
                  ) : null}
                </div>
              ) : null}
              {documento.avisos?.length ? (
                <ul aria-label="Motivos para revisar" className="flex flex-col gap-1 text-xs text-muted-foreground [overflow-wrap:anywhere]">
                  {documento.avisos.map((aviso, indice) => <li key={indice}>{motivoAviso(aviso)}</li>)}
                </ul>
              ) : null}
            </div>
            <div className="flex max-w-full flex-wrap items-center gap-2">
              {documento.situacao === "concluido" ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => baixarDocumento(documento)}
                >
                  Baixar
                </Button>
              ) : null}
              {documento.situacao === "concluido" && podeEscrever && <AcaoReprocessarIa loteId={lote.id} documento={documento} onReprocessado={(atualizado)=>onAtualizadoRef.current?.(atualizado)} />}
              {documento.limpeza_situacao === "falhou" && podeEscrever ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => limparDeNovo(documento.id)}
                  disabled={tentandoDeNovo === documento.id}
                >
                  {tentandoDeNovo === documento.id ? "Tentando…" : "Tentar de novo"}
                </Button>
              ) : null}
              {documento.situacao === "falhou" && podeEscrever ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => reenviar(documento.id)}
                  disabled={reenviando === documento.id}
                >
                  {reenviando === documento.id ? "Reenviando…" : "Reenviar"}
                </Button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>

      {podeEscrever && limpezaTerminou ? (
        <div className="flex justify-end">
          <Button type="button" variant="outline" size="sm" onClick={baixarRelatorio} disabled={baixandoRelatorio}>
            Baixar relatório do lote
          </Button>
        </div>
      ) : null}

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
    </section>
  );
}
