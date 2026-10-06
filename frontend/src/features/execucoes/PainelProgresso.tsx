"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { apiJson } from "@/lib/api-client";

/**
 * Progresso de uma execução do pipeline (SPEC-0013, US-003).
 *
 * Mostra etapa, situação e as contagens previstos/inseridos/mantidos/removidos
 * (AC-008). "Repetir" só aparece para uma execução `failed` e para owner/admin
 * (AC-009 / AC-021 / AC-019). Quando há execução `pending`/`running`, o painel
 * avisa que já existe uma execução ativa e não oferece nova ação (AC-010).
 */

export interface Execucao {
  id: string;
  base_id: string;
  situacao: string;
  etapa: string;
  previstos: number;
  inseridos: number;
  mantidos: number;
  removidos: number;
  erro: string | null;
  iniciado_em: string;
  concluido_em: string | null;
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
}

const PAPEIS_DE_ESCRITA = ["owner", "admin"];
const SITUACOES_ATIVAS = ["pending", "running"];

function autor(criadoPor: Execucao["criado_por"]): string {
  if (!criadoPor) return "Autor não identificado";
  return `${criadoPor.nome}${criadoPor.desativada ? " (desativada)" : ""}`;
}

function variantePorSituacao(
  situacao: string,
): "default" | "secondary" | "destructive" | "outline" {
  if (situacao === "succeeded") return "default";
  if (situacao === "failed") return "destructive";
  if (SITUACOES_ATIVAS.includes(situacao)) return "secondary";
  return "outline";
}

interface PainelProgressoProps {
  execucao: Execucao;
  papel?: string;
  onRepetida?: (novaExecucaoId: string) => void;
}

export default function PainelProgresso({
  execucao,
  papel,
  onRepetida,
}: PainelProgressoProps) {
  const [repetindo, setRepetindo] = useState(false);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  const ativa = SITUACOES_ATIVAS.includes(execucao.situacao);
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const podeRepetir = execucao.situacao === "failed" && podeEscrever;

  const contagens = [
    ["Previstos", execucao.previstos],
    ["Inseridos", execucao.inseridos],
    ["Mantidos", execucao.mantidos],
    ["Removidos", execucao.removidos],
  ] as const;

  async function repetir() {
    setRepetindo(true);
    setErroAcao(null);
    try {
      const resposta = await apiJson<{ execution_id: string }>(
        `/api/v1/executions/${execucao.id}/retry`,
        { method: "POST" },
      );
      onRepetida?.(resposta.execution_id);
    } catch {
      setErroAcao("Não foi possível repetir a execução. Tente novamente.");
    } finally {
      setRepetindo(false);
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-lg border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">Etapa</span>
        <span className="text-sm font-medium">{execucao.etapa || "—"}</span>
        <Badge variant={variantePorSituacao(execucao.situacao)}>
          {execucao.situacao}
        </Badge>
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {contagens.map(([rotulo, valor]) => (
          <div key={rotulo} className="flex flex-col">
            <dt className="text-xs text-muted-foreground">{rotulo}</dt>
            <dd className="text-lg font-semibold tabular-nums">{valor}</dd>
          </div>
        ))}
      </dl>

      <p className="text-sm text-muted-foreground [overflow-wrap:anywhere]">
        Iniciada por {autor(execucao.criado_por)}
      </p>

      {ativa ? (
        <IndicadorProcessamento>
          Já existe uma execução ativa para esta base. Acompanhe até a
          conclusão antes de iniciar outra.
        </IndicadorProcessamento>
      ) : null}

      {execucao.situacao === "failed" && execucao.erro ? (
        <Alert variant="destructive">
          <AlertDescription>{execucao.erro}</AlertDescription>
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
