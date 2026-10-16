"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { baixar } from "@/features/conversao/acoesDocumento";
import AvisoAnalise from "@/features/contradicoes/AvisoAnalise";
import CartaoOcorrencia from "@/features/contradicoes/CartaoOcorrencia";
import FiltroEtiquetas from "@/features/contradicoes/FiltroEtiquetas";
import {
  type Etiqueta,
  ordenarPorImpacto,
  type RelatorioApi,
} from "@/features/contradicoes/situacaoContradicao";
import { apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];
const INTERVALO_POLLING_MS = 3000;

interface RelatorioContradicoesProps {
  colecaoId: string;
  workspaceId?: string;
  nomeColecao?: string;
}

/**
 * Relatório de contradições da coleção (SPEC-0038, FR-007 / FR-008): aviso de andamento,
 * filtro por etiqueta, cartões ordenados por impacto e download em Markdown e PDF (owner e
 * admin). O member só consulta.
 */
export default function RelatorioContradicoes({
  colecaoId,
  workspaceId,
  nomeColecao,
}: RelatorioContradicoesProps) {
  const [dados, setDados] = useState<RelatorioApi | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Etiqueta | null>(null);
  const [releituras, setReleituras] = useState(0);
  const papel = getPapel();
  const podeEscrever = papel !== null && PAPEIS_DE_ESCRITA.includes(papel);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/contradicoes`;
  const emAndamento = dados?.analise?.situacao === "em_andamento";

  useEffect(() => {
    let ativo = true;
    apiJson<RelatorioApi>(base)
      .then((resposta) => {
        if (!ativo) return;
        setDados(resposta);
        setErro(null);
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar o relatório. Tente novamente.");
      });
    return () => {
      ativo = false;
    };
  }, [base, releituras]);

  useEffect(() => {
    if (!emAndamento) return;
    const intervalo = setInterval(() => setReleituras((n) => n + 1), INTERVALO_POLLING_MS);
    return () => clearInterval(intervalo);
  }, [emAndamento]);

  const reler = useCallback(() => setReleituras((n) => n + 1), []);

  async function continuar() {
    if (!dados?.analise) return;
    setErro(null);
    try {
      await apiJson(`${base}/analises/${encodeURIComponent(dados.analise.id)}/continuar`, {
        method: "POST",
      });
      reler();
    } catch {
      setErro("Não foi possível continuar a análise. Tente novamente.");
    }
  }

  async function baixarRelatorio(formato: "md" | "pdf") {
    setErro(null);
    try {
      await baixar(`${base}/relatorio?formato=${formato}`, `contradicoes.${formato}`);
    } catch {
      setErro("Não foi possível baixar o relatório. Tente novamente.");
    }
  }

  const acoes = (
    <div className="flex flex-wrap items-center justify-end gap-2">
      {workspaceId ? (
        <Link
          href={`/workspaces/${encodeURIComponent(workspaceId)}/colecoes/${encodeURIComponent(colecaoId)}`}
          className={buttonVariants({ variant: "outline" })}
        >
          Voltar à coleção
        </Link>
      ) : null}
      {podeEscrever && dados?.analise ? (
        <>
          <Button type="button" variant="outline" onClick={() => baixarRelatorio("md")}>
            Baixar Markdown
          </Button>
          <Button type="button" variant="outline" onClick={() => baixarRelatorio("pdf")}>
            Baixar PDF
          </Button>
        </>
      ) : null}
    </div>
  );

  const ocorrencias = dados
    ? ordenarPorImpacto(dados.ocorrencias).filter((o) => filtro === null || o.etiqueta === filtro)
    : [];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Contradições"
        description={
          nomeColecao
            ? `Divergências entre os documentos da coleção ${nomeColecao}.`
            : "Divergências entre os documentos desta coleção."
        }
        actions={acoes}
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={reler}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {dados === null && !erro ? (
        <Skeleton aria-busy="true" className="h-24 w-full" />
      ) : null}

      {dados && dados.analise === null ? (
        <p className="text-sm text-muted-foreground">
          Nenhuma análise foi feita nesta coleção ainda.
        </p>
      ) : null}

      {dados?.analise ? (
        <>
          <AvisoAnalise
            situacao={dados.analise.situacao}
            concluidos={dados.analise.concluidos}
            total={dados.analise.total_assuntos}
            motivo={dados.analise.motivo}
            podeContinuar={podeEscrever}
            onContinuar={continuar}
          />
          {(dados.analise.avisos ?? []).map((aviso) => (
            <Alert key={aviso}>
              <AlertDescription>{aviso}</AlertDescription>
            </Alert>
          ))}
          {dados.nao_classificadas > 0 ? (
            <p className="text-sm text-muted-foreground">
              {dados.nao_classificadas} afirmações sem assunto claro não foram comparadas.
            </p>
          ) : null}
          {dados.ocorrencias.length === 0 && dados.analise.situacao === "concluida" ? (
            <div className="flex flex-col gap-1">
              <p className="font-medium">Nenhuma contradição encontrada</p>
              <p className="text-sm text-muted-foreground">
                {dados.analise.documentos_analisados} documentos foram analisados.
              </p>
            </div>
          ) : null}
          {dados.ocorrencias.length > 0 ? (
            <>
              <FiltroEtiquetas valor={filtro} onChange={setFiltro} />
              <div className="flex flex-col gap-3">
                {ocorrencias.map((ocorrencia) => (
                  <CartaoOcorrencia key={ocorrencia.id} ocorrencia={ocorrencia} />
                ))}
              </div>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
