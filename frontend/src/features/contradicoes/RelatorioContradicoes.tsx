"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { baixar } from "@/features/conversao/acoesDocumento";
import BotaoAnalisarContradicoes from "@/features/contradicoes/BotaoAnalisarContradicoes";
import AvisoAnalise from "@/features/contradicoes/AvisoAnalise";
import CartaoOcorrencia from "@/features/contradicoes/CartaoOcorrencia";
import FiltroEtiquetas from "@/features/contradicoes/FiltroEtiquetas";
import {
  type Etiqueta,
  ordenarPorImpacto,
  type RelatorioApi,
} from "@/features/contradicoes/situacaoContradicao";
import LiberarColecaoDialog from "@/features/decisoes/LiberarColecaoDialog";
import PainelDecisaoEmpresa from "@/features/decisoes/PainelDecisaoEmpresa";
import { APLICADAS } from "@/features/decisoes/tipos";
import { useDecisoes } from "@/features/decisoes/useDecisoes";
import VersoesDocumentoSheet from "@/features/decisoes/VersoesDocumentoSheet";
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
  const [liberando, setLiberando] = useState(false);
  const [versoesDe, setVersoesDe] = useState<{ id: string; nome_arquivo: string } | null>(null);
  const [iaPermitida, setIaPermitida] = useState(true);
  const papel = getPapel();
  const podeEscrever = papel !== null && PAPEIS_DE_ESCRITA.includes(papel);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/contradicoes`;
  const emAndamento = dados?.analise?.situacao === "em_andamento";
  const decisoes = useDecisoes(colecaoId, dados?.analise != null);

  useEffect(() => {
    if (!podeEscrever || !workspaceId) return;
    let ativo = true;
    apiJson<{ ia_externa_permitida: boolean }>(
      `/api/v1/workspaces/${encodeURIComponent(workspaceId)}/analise-ia`,
    )
      .then((ajustes) => {
        if (ativo) setIaPermitida(ajustes.ia_externa_permitida);
      })
      .catch(() => undefined);
    return () => {
      ativo = false;
    };
  }, [podeEscrever, workspaceId]);

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
      {podeEscrever ? (
        <BotaoAnalisarContradicoes
          colecaoId={colecaoId}
          provedor={dados?.analise?.provedor ?? null}
          onIniciada={reler}
        />
      ) : null}
      {podeEscrever && dados?.analise ? (
        <>
          <Button type="button" onClick={() => setLiberando(true)}>
            Liberar para a base
          </Button>
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

  const corrigidas = new Map<string, string[]>();
  const documentosPorArquivo = new Map<string, string>();
  for (const proposta of decisoes.propostas?.propostas ?? []) {
    if (proposta.arquivo && proposta.documento_id) {
      documentosPorArquivo.set(proposta.arquivo, proposta.documento_id);
    }
    if (proposta.ocorrencia_id && proposta.arquivo && APLICADAS.includes(proposta.situacao)) {
      corrigidas.set(proposta.ocorrencia_id, [
        ...(corrigidas.get(proposta.ocorrencia_id) ?? []),
        proposta.arquivo,
      ]);
    }
  }

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
          {dados.ocorrencias.length > 0 ||
          (decisoes.rodada && (decisoes.rodada.resolvidas > 0 || decisoes.rodada.novas > 0)) ? (
            <PainelDecisaoEmpresa
                colecaoId={colecaoId}
                provedor={dados.analise.provedor}
                iaPermitida={iaPermitida}
                podeEscrever={podeEscrever}
                propostas={decisoes.propostas}
                rodada={decisoes.rodada}
                onMudou={() => {
                  decisoes.reler();
                  reler();
                }}
              />
          ) : null}
          {dados.ocorrencias.length > 0 ? (
            <>
              <FiltroEtiquetas valor={filtro} onChange={setFiltro} />
              <div className="flex flex-col gap-3">
                {ocorrencias.map((ocorrencia) => (
                  <CartaoOcorrencia
                    key={ocorrencia.id}
                    ocorrencia={ocorrencia}
                    corrigidoEm={corrigidas.get(ocorrencia.id)}
                    onVerVersoes={(arquivo) => {
                      const id = documentosPorArquivo.get(arquivo);
                      if (id) setVersoesDe({ id, nome_arquivo: arquivo });
                    }}
                  />
                ))}
              </div>
            </>
          ) : null}
          {decisoes.rodada?.revisada_em ? (
            <Alert role="status">
              <AlertDescription>
                Coleção revisada em {new Date(decisoes.rodada.revisada_em).toLocaleString("pt-BR")}.
              </AlertDescription>
            </Alert>
          ) : null}
        </>
      ) : null}
      <LiberarColecaoDialog
        open={liberando}
        onOpenChange={setLiberando}
        colecaoId={colecaoId}
        abertas={decisoes.rodada?.abertas ?? 0}
        onLiberada={decisoes.reler}
      />
      {versoesDe ? (
        <VersoesDocumentoSheet
          open
          colecaoId={colecaoId}
          documento={versoesDe}
          podeEscrever={podeEscrever}
          onOpenChange={(aberto) => {
            if (!aberto) setVersoesDe(null);
          }}
          onRestaurada={decisoes.reler}
        />
      ) : null}
    </div>
  );
}
