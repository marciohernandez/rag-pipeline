"use client";

import { useCallback, useEffect, useState } from "react";

import type { PropostasApi, Rodada } from "@/features/decisoes/tipos";
import { apiJson } from "@/lib/api-client";

const INTERVALO_MS = 3000;

/**
 * Carrega as propostas e o resumo da rodada de uma coleção (SPEC-0039). Enquanto a IA
 * interpreta a resposta, relê a cada 3 s; `reler` força uma nova leitura.
 */
export function useDecisoes(colecaoId: string, habilitado: boolean) {
  const [propostas, setPropostas] = useState<PropostasApi | null>(null);
  const [rodada, setRodada] = useState<Rodada | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [leituras, setLeituras] = useState(0);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/decisoes`;
  const interpretando = propostas?.resposta?.situacao === "em_andamento";

  useEffect(() => {
    if (!habilitado) return;
    let ativo = true;
    Promise.all([apiJson<PropostasApi>(`${base}/propostas`), apiJson<Rodada>(`${base}/rodada`)])
      .then(([lidas, resumo]) => {
        if (!ativo) return;
        setPropostas(lidas);
        setRodada(resumo);
        setErro(null);
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar as decisões. Tente novamente.");
      });
    return () => {
      ativo = false;
    };
  }, [base, habilitado, leituras]);

  useEffect(() => {
    if (!interpretando) return;
    const intervalo = setInterval(() => setLeituras((n) => n + 1), INTERVALO_MS);
    return () => clearInterval(intervalo);
  }, [interpretando]);

  const reler = useCallback(() => setLeituras((n) => n + 1), []);
  return { propostas, rodada, erro, reler };
}
