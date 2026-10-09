"use client";

import type { KeyboardEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatarData,
  nomeDoAutor,
  rotulosSituacao,
  type EnvioResumo,
} from "@/features/colecoes/tipos";
import { apiFetch } from "@/lib/api-client";
import { rotulosSplitter } from "@/lib/ingestao";

/**
 * Histórico de envios da coleção (SPEC-0030, FR-012): do mais recente ao mais antigo,
 * com arquivos, divisão, situação, contagens, erro seguro, autor e data. A linha abre o
 * detalhe do envio; Repetir aparece só para owner/admin num envio que falhou.
 */

const COLUNAS = ["ID", "Arquivos", "Divisão", "Situação", "Contagens", "Autor", "Iniciado em"] as const;
const PAPEIS_DE_ESCRITA = ["owner", "admin"];

export function varianteDaSituacao(situacao: string): "default" | "secondary" | "destructive" | "outline" {
  if (situacao === "succeeded") return "default";
  if (situacao === "failed") return "destructive";
  if (situacao === "queued" || situacao === "running") return "secondary";
  return "outline";
}

interface DataGridEnviosProps {
  envios: EnvioResumo[];
  papel?: string;
  estado?: "carregando" | "erro";
  onTentarNovamente?: () => void;
  onRepetido?: (id: string) => void;
}

export default function DataGridEnvios({
  envios,
  papel,
  estado,
  onTentarNovamente,
  onRepetido,
}: DataGridEnviosProps) {
  const router = useRouter();
  const [repetindo, setRepetindo] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const carregando = estado === "carregando";
  const ordenados = [...envios].sort((a, b) => b.iniciado_em.localeCompare(a.iniciado_em));

  function abrir(id: string) {
    router.push(`/envios/${encodeURIComponent(id)}`);
  }

  function aoTeclar(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      abrir(id);
    }
  }

  async function repetir(id: string) {
    setRepetindo(id);
    setErroAcao(null);
    try {
      await apiFetch(`/api/v1/envios/${encodeURIComponent(id)}/retry`, { method: "POST" });
      onRepetido?.(id);
    } catch {
      setErroAcao("Não foi possível repetir o envio. Tente novamente.");
    } finally {
      setRepetindo(null);
    }
  }

  if (estado === "erro") {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
          <span>Não foi possível carregar os envios da coleção.</span>
          <Button type="button" variant="outline" size="sm" onClick={onTentarNovamente}>
            Tentar novamente
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {erroAcao ? (
        <Alert variant="destructive">
          <AlertDescription>{erroAcao}</AlertDescription>
        </Alert>
      ) : null}
      <div className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border" style={{ contain: "inline-size paint" }}>
        {carregando ? (
          <IndicadorProcessamento className="px-3 py-2.5">Carregando envios…</IndicadorProcessamento>
        ) : null}
        <div className="w-full min-w-0 overflow-x-auto">
          <table className="w-full min-w-[72rem] border-collapse text-sm" aria-busy={carregando}>
            <caption className="sr-only">Envios da coleção</caption>
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
              ) : ordenados.length === 0 ? (
                <tr>
                  <td colSpan={COLUNAS.length + 1} className="px-3 py-10 text-center">
                    <p className="font-medium">Nenhum envio ainda</p>
                    <p className="mt-1 text-muted-foreground">Os envios desta coleção aparecem aqui.</p>
                  </td>
                </tr>
              ) : (
                ordenados.map((envio) => (
                  <tr
                    key={envio.id}
                    tabIndex={0}
                    aria-label={`Envio ${envio.id}`}
                    onClick={() => abrir(envio.id)}
                    onKeyDown={(evento) => aoTeclar(evento, envio.id)}
                    className="cursor-pointer border-b align-top outline-none last:border-0 hover:bg-muted/40 focus-visible:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <td className="px-3 py-2.5 font-mono text-xs">{envio.id}</td>
                    <td className="max-w-64 px-3 py-2.5 [overflow-wrap:anywhere]">{envio.arquivos.join(", ")}</td>
                    <td className="px-3 py-2.5">
                      {rotulosSplitter[envio.processamento?.splitter ?? ""] ?? envio.processamento?.splitter ?? "—"}
                    </td>
                    <td className="max-w-72 px-3 py-2.5">
                      <Badge variant={varianteDaSituacao(envio.situacao)}>
                        {rotulosSituacao[envio.situacao] ?? envio.situacao}
                      </Badge>
                      {envio.situacao === "failed" && envio.erro ? (
                        <p className="mt-1 text-xs text-destructive [overflow-wrap:anywhere]">{envio.erro}</p>
                      ) : null}
                    </td>
                    <td className="px-3 py-2.5 text-xs tabular-nums text-muted-foreground">
                      {envio.previstos} previstos · {envio.inseridos} inseridos · {envio.mantidos} mantidos ·{" "}
                      {envio.removidos} removidos
                    </td>
                    <td className="max-w-48 px-3 py-2.5 text-muted-foreground [overflow-wrap:anywhere]">
                      {nomeDoAutor(envio.criado_por)}
                    </td>
                    <td className="px-3 py-2.5">{formatarData(envio.iniciado_em)}</td>
                    <td
                      className="px-3 py-2.5 text-right"
                      onClick={(evento) => evento.stopPropagation()}
                      onKeyDown={(evento) => evento.stopPropagation()}
                    >
                      {podeEscrever && envio.situacao === "failed" ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="xs"
                          onClick={() => void repetir(envio.id)}
                          loading={repetindo === envio.id}
                          disabled={repetindo !== null}
                        >
                          Repetir
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
