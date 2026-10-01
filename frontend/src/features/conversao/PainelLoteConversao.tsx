"use client";

import { useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import { apiFetch, apiJson } from "@/lib/api-client";

/**
 * Situação por documento, download individual/pacote e reenviar (SPEC-0023, US-002/003/004).
 *
 * Modelado em `PainelProgresso`: mesmas variantes de `Badge` por situação e
 * mesma região `role="status"`/`aria-live` para anunciar a mudança sem exigir
 * foco manual. Usado tanto dentro de `ConversaoSheet` (logo após o envio)
 * quanto na linha expandida de `DataGridLotesConversao` (lote já existente).
 */

const PAPEIS_DE_ESCRITA = ["owner", "admin"];
const SITUACOES_ATIVAS = ["fila", "processando"];
const INTERVALO_POLLING_MS = 3000;

function variantePorSituacao(
  situacao: string,
): "default" | "secondary" | "destructive" | "outline" {
  if (situacao === "concluido") return "default";
  if (situacao === "falhou") return "destructive";
  if (SITUACOES_ATIVAS.includes(situacao)) return "secondary";
  return "outline";
}

async function baixar(caminho: string, nomeArquivo: string) {
  const resposta = await apiFetch(caminho);
  const blob = await resposta.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeArquivo;
  link.click();
  URL.revokeObjectURL(url);
}

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
  const ativo = lote.documentos.some((documento) => SITUACOES_ATIVAS.includes(documento.situacao));
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
      const nomeBase = documento.nome_arquivo.replace(/\.[^.]+$/, "");
      await baixar(
        `/api/v1/conversoes/${lote.id}/documentos/${documento.id}/markdown`,
        `${nomeBase}.md`,
      );
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

  async function reenviar(documentoId: string) {
    setErro(null);
    setReenviando(documentoId);
    try {
      await apiJson(`/api/v1/conversoes/${lote.id}/documentos/${documentoId}/reenviar`, {
        method: "POST",
      });
      const atualizado = await apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${lote.id}`);
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
          <Badge variant={variantePorSituacao(lote.situacao)}>{lote.situacao}</Badge>
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
        </p>
      ) : null}

      <ul className="flex flex-col gap-2">
        {lote.documentos.map((documento) => (
          <li
            key={documento.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2"
          >
            <div className="flex min-w-0 flex-col gap-1">
              <span className="truncate text-sm font-medium [overflow-wrap:anywhere]">
                {documento.nome_arquivo}
              </span>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={variantePorSituacao(documento.situacao)}>
                  {documento.situacao}
                </Badge>
                {documento.situacao === "falhou" && documento.erro ? (
                  <span className="text-xs text-destructive [overflow-wrap:anywhere]">
                    {documento.erro}
                  </span>
                ) : null}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
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

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
    </section>
  );
}
