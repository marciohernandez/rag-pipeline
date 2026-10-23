"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

/**
 * Atalho do lote da Fase 1 para a indexação da Fase 2, sem baixar e subir arquivos (SPEC-0043).
 *
 * Opcional: o download do pacote e o upload manual continuam existindo. A pessoa marca os
 * documentos aptos (marcados por padrão) e segue para o fluxo de ingestão, que lê os `.md`
 * guardados no servidor. Só owner e admin veem o bloco; a autorização final é do servidor.
 */

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface DocumentoDoLote {
  id: string;
  nome_arquivo: string;
  situacao: string;
  apagado_em?: string | null;
}

interface Props {
  workspaceId: string;
  papel?: string;
  lote: { id: string; situacao: string; documentos: DocumentoDoLote[] };
}

const apto = (documento: DocumentoDoLote) =>
  documento.situacao === "concluido" && !documento.apagado_em;

function motivoDeIndisponibilidade(lote: Props["lote"], aptos: DocumentoDoLote[]): string | null {
  if (lote.situacao === "processando" || lote.situacao === "aguardando_grupos") {
    return "O lote ainda está em processamento.";
  }
  if (lote.situacao === "aguardando_dominio") return "Confirme o domínio do lote antes de seguir.";
  if (lote.situacao === "limpando") return "A limpeza do lote ainda está em andamento.";
  if (aptos.length > 0) return null;
  if (lote.documentos.some((documento) => documento.apagado_em)) {
    return "Os arquivos deste lote já foram apagados (expirados) e não podem ser indexados.";
  }
  return "Nenhum documento apto neste lote.";
}

function nomeMarkdown(nomeArquivo: string): string {
  const ponto = nomeArquivo.lastIndexOf(".");
  return `${ponto > 0 ? nomeArquivo.slice(0, ponto) : nomeArquivo}.md`;
}

export default function SeguirParaIndexacao({ workspaceId, papel, lote }: Props) {
  const router = useRouter();
  const aptos = lote.documentos.filter(apto);
  const [desmarcados, setDesmarcados] = useState<string[]>([]);

  if (papel === undefined || !PAPEIS_DE_ESCRITA.includes(papel)) return null;

  const motivo = motivoDeIndisponibilidade(lote, aptos);
  const marcados = aptos.filter((documento) => !desmarcados.includes(documento.id));
  const pode = motivo === null && marcados.length > 0;

  function alternar(documentoId: string) {
    setDesmarcados((atuais) =>
      atuais.includes(documentoId) ? atuais.filter((id) => id !== documentoId) : [...atuais, documentoId],
    );
  }

  function seguir() {
    if (!pode) return;
    const ids = marcados.map((documento) => documento.id).join(",");
    router.push(
      `/workspaces/${encodeURIComponent(workspaceId)}/enviar` +
        `?lote=${encodeURIComponent(lote.id)}&documentos=${encodeURIComponent(ids)}`,
    );
  }

  const mensagem =
    motivo ??
    (marcados.length === 0
      ? "Nenhum documento marcado."
      : `${marcados.length} ${marcados.length === 1 ? "documento marcado" : "documentos marcados"}.`);

  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-3">
      {motivo === null ? (
        <fieldset className="flex min-w-0 flex-col gap-1.5">
          <legend className="mb-1 text-sm font-medium">Documentos para indexar</legend>
          {aptos.map((documento) => (
            <label key={documento.id} className="flex min-w-0 items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="size-4 shrink-0 accent-primary"
                checked={!desmarcados.includes(documento.id)}
                onChange={() => alternar(documento.id)}
              />
              <span className="min-w-0 [overflow-wrap:anywhere]">{documento.nome_arquivo}</span>
              <span className="sr-only">{nomeMarkdown(documento.nome_arquivo)}</span>
            </label>
          ))}
        </fieldset>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p role="status" className="text-sm text-muted-foreground [overflow-wrap:anywhere]">
          {mensagem}
        </p>
        <Button type="button" size="sm" onClick={seguir} disabled={!pode}>
          Seguir para a indexação
        </Button>
      </div>
    </div>
  );
}
