"use client";

import { useCallback, useEffect, useState } from "react";

import { apiJson } from "@/lib/api-client";
import {
  PADROES_FALLBACK,
  PROCESSAMENTO_PADRAO,
  serializarProcessamento,
  type Padroes,
  type Processamento,
} from "@/lib/ingestao";

export type EtapaId = "arquivos" | "divisao" | "previa" | "publicacao";

export const ETAPAS: { id: EtapaId; titulo: string }[] = [
  { id: "arquivos", titulo: "Arquivos" },
  { id: "divisao", titulo: "Divisão" },
  { id: "previa", titulo: "Prévia" },
  { id: "publicacao", titulo: "Publicação" },
];

export interface ItemPrevia {
  documento: string;
  posicao: number;
  tamanho: number;
  texto: string;
  tipo?: string;
}

export interface Previa {
  resumo: { documentos: number; chunks: number; tamanho_medio: number };
  avisos: string[];
  arquivos_com_configuracao_propria: string[];
  documentos_excluidos?: string[];
  chunks: ItemPrevia[];
  pagina: number;
  total: number;
}

export interface ValoresPublicacao {
  conexaoEmbeddingsId: string;
  conexaoVectorStoreId: string;
  colecao: string;
  /** Destino escolhido na Publicação (SPEC-0029); ausente, valem os padrões. */
  destino?: Processamento["destino"];
}

export const TAMANHO_PAGINA = 10;

/**
 * Estado do fluxo de ingestão (SPEC-0026, FR-013): tudo vive em memória do
 * navegador. Nada é gravado no servidor antes de publicar; voltar entre etapas
 * preserva arquivos e valores, e qualquer mudança invalida a prévia calculada.
 */
export function useFluxoIngestao(workspaceId: string) {
  const [etapa, setEtapa] = useState<EtapaId>("arquivos");
  const [maisAlta, setMaisAlta] = useState(0);
  const [padroes, setPadroes] = useState<Padroes>(PADROES_FALLBACK);
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [usarPreparada, setUsarPreparada] = useState(false);
  const [splitter, setSplitter] = useState(PADROES_FALLBACK.splitter);
  const [tamanho, setTamanho] = useState(String(PADROES_FALLBACK.chunk_size));
  const [overlap, setOverlap] = useState(String(PADROES_FALLBACK.chunk_overlap));
  const [previa, setPrevia] = useState<Previa | null>(null);
  const [calculando, setCalculando] = useState(false);
  const [erroPrevia, setErroPrevia] = useState<string | null>(null);
  const [documento, setDocumento] = useState<string | null>(null);
  const [processamento, setProcessamento] = useState<Processamento>(PROCESSAMENTO_PADRAO);
  const [tamanhoPagina, setTamanhoPagina] = useState(TAMANHO_PAGINA);

  useEffect(() => {
    let ativo = true;
    apiJson<Padroes>("/api/v1/ingestao/padroes")
      .then((recebidos) => {
        if (!ativo) return;
        // Campos ausentes na resposta caem nos padrões locais.
        const completos = {
          ...PADROES_FALLBACK,
          ...recebidos,
          limites: { ...PADROES_FALLBACK.limites, ...recebidos.limites },
          splitters: recebidos.splitters?.length ? recebidos.splitters : PADROES_FALLBACK.splitters,
        };
        setPadroes(completos);
        setSplitter(completos.splitter);
        setTamanho(String(completos.chunk_size));
        setOverlap(String(completos.chunk_overlap));
      })
      .catch(() => {
        // Sem o endpoint, valem os padrões locais e o backend valida de novo.
      });
    return () => {
      ativo = false;
    };
  }, []);

  const invalidar = useCallback(() => {
    setPrevia(null);
    setErroPrevia(null);
    setDocumento(null);
  }, []);

  const adicionarArquivos = useCallback(
    (novos: File[]) => {
      setArquivos((atuais) => {
        const nomes = new Set(atuais.map((arquivo) => arquivo.name));
        const inedito = novos.filter((arquivo) => !nomes.has(arquivo.name) && nomes.add(arquivo.name));
        return [...atuais, ...inedito];
      });
      invalidar();
    },
    [invalidar],
  );
  const removerArquivo = useCallback(
    (nome: string) => {
      setArquivos((atuais) => atuais.filter((a) => a.name !== nome));
      invalidar();
    },
    [invalidar],
  );
  const alternarPreparada = useCallback(
    (valor: boolean) => {
      setUsarPreparada(valor);
      if (valor) setArquivos([]);
      invalidar();
    },
    [invalidar],
  );
  const alterarDivisao = useCallback(
    (campo: "splitter" | "tamanho" | "overlap", valor: string) => {
      if (campo === "splitter") setSplitter(valor);
      if (campo === "tamanho") setTamanho(valor);
      if (campo === "overlap") setOverlap(valor);
      invalidar();
    },
    [invalidar],
  );

  const alterarProcessamento = useCallback(
    <G extends keyof Processamento>(grupo: G, campo: keyof Processamento[G], valor: Processamento[G][keyof Processamento[G]]) => {
      setProcessamento((atual) => ({ ...atual, [grupo]: { ...atual[grupo], [campo]: valor } }));
      invalidar();
    },
    [invalidar],
  );

  const ir = useCallback((destino: EtapaId) => {
    const indice = ETAPAS.findIndex((e) => e.id === destino);
    setEtapa(destino);
    setMaisAlta((atual) => Math.max(atual, indice));
  }, []);

  const corpo = useCallback(
    (extra: Record<string, string>, escolhas: Processamento = processamento) => {
      const dados = new FormData();
      for (const arquivo of arquivos) dados.append("arquivos", arquivo);
      dados.append("usar_base_preparada", String(usarPreparada));
      dados.append("splitter", splitter);
      dados.append("chunk_size", tamanho);
      dados.append("chunk_overlap", overlap);
      dados.append("processamento", serializarProcessamento(splitter, escolhas));
      for (const [chave, valor] of Object.entries(extra)) dados.append(chave, valor);
      return dados;
    },
    [arquivos, usarPreparada, splitter, tamanho, overlap, processamento],
  );

  const calcularPrevia = useCallback(
    async (pagina = 1, filtro: string | null = documento, tamanho: number = tamanhoPagina) => {
      setCalculando(true);
      setErroPrevia(null);
      try {
        const extra: Record<string, string> = { pagina: String(pagina), tamanho_pagina: String(tamanho) };
        if (filtro) extra.documento = filtro;
        setPrevia(await apiJson<Previa>("/api/v1/ingestao/previa", { method: "POST", body: corpo(extra) }));
        setDocumento(filtro);
      } catch (falha) {
        setErroPrevia(
          falha instanceof Error && falha.message
            ? falha.message
            : "Não foi possível calcular a prévia. Tente novamente.",
        );
      } finally {
        setCalculando(false);
      }
    },
    [corpo, documento, tamanhoPagina],
  );

  /** Troca a quantidade de chunks por página, volta à página 1 e mantém o filtro. */
  const alterarTamanhoPagina = useCallback(
    (tamanho: number) => {
      setTamanhoPagina(tamanho);
      void calcularPrevia(1, documento, tamanho);
    },
    [calcularPrevia, documento],
  );

  const publicar = useCallback(
    (valores: ValoresPublicacao) =>
      apiJson<{ base_id: string; execution_id: string }>("/api/v1/bases", {
        method: "POST",
        body: corpo(
          {
            workspace_id: workspaceId,
            collection_name: valores.colecao,
            conexao_embeddings_id: valores.conexaoEmbeddingsId,
            conexao_vector_store_id: valores.conexaoVectorStoreId,
            iniciar_execucao: "true",
          },
          valores.destino ? { ...processamento, destino: valores.destino } : processamento,
        ),
      }),
    [corpo, workspaceId, processamento],
  );

  const pendente = arquivos.length > 0 || usarPreparada;

  return {
    etapa,
    maisAlta,
    padroes,
    arquivos,
    usarPreparada,
    splitter,
    tamanho,
    overlap,
    previa,
    calculando,
    erroPrevia,
    documento,
    processamento,
    tamanhoPagina,
    pendente,
    ir,
    adicionarArquivos,
    removerArquivo,
    alternarPreparada,
    alterarDivisao,
    alterarProcessamento,
    alterarTamanhoPagina,
    calcularPrevia,
    publicar,
  };
}
