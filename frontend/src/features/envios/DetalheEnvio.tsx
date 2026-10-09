"use client";

import { useState } from "react";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { varianteDaSituacao } from "@/features/colecoes/DataGridEnvios";
import {
  formatarData,
  nomeDoAutor,
  rotulosSituacao,
  type EnvioDetalhe,
} from "@/features/colecoes/tipos";
import { apiFetch } from "@/lib/api-client";
import { rotulosSplitter } from "@/lib/ingestao";

/**
 * Progresso de um envio (SPEC-0030, FR-012): etapa, situação, contagens, arquivos, erro
 * seguro e Repetir. A página faz o polling enquanto o envio está na fila ou em
 * processamento; "Repetir" só aparece para owner/admin num envio que falhou.
 */

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface DetalheEnvioProps {
  envio: EnvioDetalhe;
  papel?: string;
  onRepetido?: () => void;
}

export default function DetalheEnvio({ envio, papel, onRepetido }: DetalheEnvioProps) {
  const [repetindo, setRepetindo] = useState(false);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const ativo = envio.situacao === "queued" || envio.situacao === "running";
  const podeRepetir = envio.situacao === "failed" && papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const contagens = [
    ["Previstos", envio.previstos],
    ["Inseridos", envio.inseridos],
    ["Mantidos", envio.mantidos],
    ["Removidos", envio.removidos],
  ] as const;

  async function repetir() {
    setRepetindo(true);
    setErroAcao(null);
    try {
      await apiFetch(`/api/v1/envios/${encodeURIComponent(envio.id)}/retry`, { method: "POST" });
      onRepetido?.();
    } catch {
      setErroAcao("Não foi possível repetir o envio. Tente novamente.");
    } finally {
      setRepetindo(false);
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-lg border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">Etapa</span>
        <span className="text-sm font-medium">{envio.etapa || "—"}</span>
        <Badge variant={varianteDaSituacao(envio.situacao)}>{rotulosSituacao[envio.situacao] ?? envio.situacao}</Badge>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {contagens.map(([rotulo, valor]) => (
          <div key={rotulo} className="flex flex-col">
            <dt className="text-xs text-muted-foreground">{rotulo}</dt>
            <dd className="text-lg font-semibold tabular-nums">{valor}</dd>
          </div>
        ))}
      </dl>

      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div className="flex min-w-0 flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">Arquivos</dt>
          <dd className="[overflow-wrap:anywhere]">{envio.arquivos.join(", ") || "—"}</dd>
        </div>
        <div className="flex min-w-0 flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">Divisão</dt>
          <dd>{rotulosSplitter[envio.processamento?.splitter ?? ""] ?? envio.processamento?.splitter ?? "—"}</dd>
        </div>
        <div className="flex min-w-0 flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">Iniciado em</dt>
          <dd>{formatarData(envio.iniciado_em)}</dd>
        </div>
        <div className="flex min-w-0 flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">Concluído em</dt>
          <dd>{formatarData(envio.concluido_em)}</dd>
        </div>
      </dl>

      <p className="text-sm text-muted-foreground [overflow-wrap:anywhere]">
        Iniciado por {nomeDoAutor(envio.criado_por)}
      </p>

      {ativo ? (
        <IndicadorProcessamento>Envio em andamento. Acompanhe até a conclusão.</IndicadorProcessamento>
      ) : null}

      {envio.situacao === "failed" && envio.erro ? (
        <Alert variant="destructive">
          <AlertDescription>{envio.erro}</AlertDescription>
        </Alert>
      ) : null}

      {erroAcao ? (
        <Alert variant="destructive">
          <AlertDescription>{erroAcao}</AlertDescription>
        </Alert>
      ) : null}

      {podeRepetir ? (
        <div>
          <Button type="button" onClick={repetir} loading={repetindo} disabled={repetindo}>
            {repetindo ? "Repetindo…" : "Repetir"}
          </Button>
        </div>
      ) : null}
    </section>
  );
}
