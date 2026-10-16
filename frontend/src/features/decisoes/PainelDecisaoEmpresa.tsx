"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import BlocoPropostasClaras from "@/features/decisoes/BlocoPropostasClaras";
import CaixaRespostaEmpresa from "@/features/decisoes/CaixaRespostaEmpresa";
import PropostaIncerta from "@/features/decisoes/PropostaIncerta";
import ResumoRodada from "@/features/decisoes/ResumoRodada";
import type {
  AcaoDecisao,
  LocalManual,
  PropostasApi,
  Rodada,
} from "@/features/decisoes/tipos";
import { ApiError, apiJson } from "@/lib/api-client";

const MENSAGEM_FALHA = "Não foi possível registrar a decisão. Tente novamente.";

interface PainelDecisaoEmpresaProps {
  colecaoId: string;
  provedor: string | null;
  iaPermitida: boolean;
  podeEscrever: boolean;
  propostas: PropostasApi | null;
  rodada: Rodada | null;
  onMudou: () => void;
}

/**
 * Compõe a decisão da empresa na rota do relatório (SPEC-0039): caixa da resposta, bloco das
 * propostas claras, decisão individual das incertas e resumo da rodada. Toda escrita passa por
 * uma confirmação da pessoa; o member só consulta.
 */
export default function PainelDecisaoEmpresa({
  colecaoId,
  provedor,
  iaPermitida,
  podeEscrever,
  propostas,
  rodada,
  onMudou,
}: PainelDecisaoEmpresaProps) {
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/decisoes/propostas`;
  const lista = propostas?.propostas ?? [];
  const claras = lista.filter((p) => p.situacao === "clara");
  const pendentes = lista.filter((p) => p.situacao === "incerta" || p.situacao === "sem_decisao");
  const resposta = propostas?.resposta ?? null;
  const podeColar = podeEscrever && (rodada?.abertas ?? 1) > 0;

  async function enviar(caminho: string, corpo: Record<string, unknown>) {
    if (ocupado) return;
    setOcupado(true);
    setErro(null);
    try {
      await apiJson(caminho, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(corpo),
      });
      onMudou();
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setOcupado(false);
    }
  }

  function decidir(id: string, acao: AcaoDecisao, texto?: string, local?: LocalManual) {
    void enviar(`${base}/${encodeURIComponent(id)}/decisao`, {
      acao,
      ...(texto !== undefined ? { texto_corrigido: texto } : {}),
      ...(local ?? {}),
    });
  }

  return (
    <section aria-label="Decisão da empresa" className="flex min-w-0 flex-col gap-3">
      {podeColar ? (
        <CaixaRespostaEmpresa
          colecaoId={colecaoId}
          provedor={provedor}
          iaPermitida={iaPermitida}
          onInterpretada={onMudou}
        />
      ) : null}
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      {resposta?.situacao === "em_andamento" ? (
        <Alert role="status" aria-live="polite" aria-busy="true">
          <AlertDescription>Interpretando a resposta da empresa…</AlertDescription>
        </Alert>
      ) : null}
      {resposta?.situacao === "incompleta" ? (
        <Alert variant="destructive">
          <AlertDescription>
            {resposta.motivo ?? "A interpretação não terminou."} Nenhum documento foi alterado.
          </AlertDescription>
        </Alert>
      ) : null}
      {resposta === null && podeColar ? (
        <p className="text-sm text-muted-foreground">
          Cole a resposta da empresa para receber uma proposta por contradição.
        </p>
      ) : null}
      <BlocoPropostasClaras
        propostas={claras}
        ocupado={ocupado}
        somenteLeitura={!podeEscrever}
        onConfirmar={() => void enviar(`${base}/confirmar`, { confirmado: true })}
      />
      {pendentes.length > 0 ? (
        <section aria-label="Propostas que pedem decisão" className="flex min-w-0 flex-col gap-3">
          <h3 className="text-base font-medium">Pedem a sua decisão ({pendentes.length})</h3>
          {pendentes.map((proposta) => (
            <PropostaIncerta
              key={proposta.id}
              proposta={proposta}
              ocupado={ocupado}
              somenteLeitura={!podeEscrever}
              onDecidir={(acao, texto, local) => decidir(proposta.id, acao, texto, local)}
            />
          ))}
        </section>
      ) : null}
      {rodada && (rodada.resolvidas > 0 || rodada.novas > 0) ? (
        <ResumoRodada
          resolvidas={rodada.resolvidas}
          novas={rodada.novas}
          abertas={rodada.abertas}
        />
      ) : null}
    </section>
  );
}
