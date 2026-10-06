"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import type { ValoresPublicacao } from "@/features/ingestao/useFluxoIngestao";
import { ApiError, apiJson } from "@/lib/api-client";

interface Props {
  resumo: { arquivos: number; chunks: number };
  onPublicar: (valores: ValoresPublicacao) => Promise<{ base_id: string; execution_id: string }>;
}

interface Dimensao {
  embeddings: number;
  colecao: number | null;
  compativel: boolean;
}

const seletor =
  "h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";

/**
 * Etapa Publicação (SPEC-0026): conexões ativas, coleção, dimensões em linha,
 * resumo e Publicar bloqueado com a razão visível. A garantia final continua no
 * servidor, que repete a verificação de dimensão antes de gravar qualquer coisa.
 */
export default function EtapaPublicacao({ resumo, onPublicar }: Props) {
  const router = useRouter();
  const [conexoes, setConexoes] = useState<ConexaoResumo[] | null>(null);
  const [erroCarga, setErroCarga] = useState(false);
  const [embeddingsId, setEmbeddingsId] = useState("");
  const [vectorStoreId, setVectorStoreId] = useState("");
  const [colecao, setColecao] = useState("");
  const [dimensao, setDimensao] = useState<Dimensao | null>(null);
  const [publicando, setPublicando] = useState(false);
  const [publicado, setPublicado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const ativas = (tipo: string) => (conexoes ?? []).filter((c) => c.tipo === tipo && c.situacao === "ativa");
  const listaEmbeddings = ativas("embeddings_openai");
  const listaQdrant = ativas("qdrant");

  useEffect(() => {
    let ativo = true;
    apiJson<ConexaoResumo[]>("/api/v1/conexoes")
      .then((lista) => {
        if (!ativo) return;
        setConexoes(lista);
        const emb = lista.filter((c) => c.tipo === "embeddings_openai" && c.situacao === "ativa");
        const qd = lista.filter((c) => c.tipo === "qdrant" && c.situacao === "ativa");
        if (emb.length === 1) setEmbeddingsId(emb[0].id);
        if (qd.length === 1) setVectorStoreId(qd[0].id);
      })
      .catch(() => {
        if (ativo) setErroCarga(true);
      });
    return () => {
      ativo = false;
    };
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- limpa a verificação ao mudar a escolha
    setDimensao(null);
    if (!embeddingsId || !vectorStoreId || !colecao.trim()) return;
    let ativo = true;
    const espera = setTimeout(() => {
      const consulta = new URLSearchParams({
        conexao_embeddings_id: embeddingsId,
        conexao_vector_store_id: vectorStoreId,
        collection_name: colecao.trim(),
      });
      apiJson<Dimensao>(`/api/v1/ingestao/dimensao?${consulta}`)
        .then((resposta) => {
          if (ativo) setDimensao(resposta);
        })
        .catch(() => {
          // Sem a verificação em linha, o servidor ainda recusa uma divergência.
        });
    }, 250);
    return () => {
      ativo = false;
      clearTimeout(espera);
    };
  }, [embeddingsId, vectorStoreId, colecao]);

  const semConexoes = conexoes !== null && (listaEmbeddings.length === 0 || listaQdrant.length === 0);
  const razao = (() => {
    if (conexoes === null) return erroCarga ? "Não foi possível ler as conexões." : "Carregando as conexões.";
    if (semConexoes) return "Publicar bloqueado: faltam conexões ativas.";
    if (!embeddingsId || !vectorStoreId) return "Escolha as duas conexões para publicar.";
    if (!colecao.trim()) return "Informe a coleção para publicar.";
    if (resumo.chunks === 0) return "Não há chunks para publicar.";
    if (dimensao && !dimensao.compativel) return "Publicar bloqueado: dimensões incompatíveis.";
    return null;
  })();

  async function publicar() {
    setPublicando(true);
    setErro(null);
    try {
      const resposta = await onPublicar({
        conexaoEmbeddingsId: embeddingsId,
        conexaoVectorStoreId: vectorStoreId,
        colecao: colecao.trim(),
      });
      setPublicado(true);
      router.push(`/execucoes/${resposta.base_id}`);
    } catch (falha) {
      setErro(
        falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível publicar. Tente novamente.",
      );
    } finally {
      setPublicando(false);
    }
  }

  const nomeEmbeddings = listaEmbeddings.find((c) => c.id === embeddingsId);
  const nomeQdrant = listaQdrant.find((c) => c.id === vectorStoreId);

  return (
    <div className="flex flex-col gap-4">
      {conexoes === null && !erroCarga ? <IndicadorProcessamento>Carregando conexões</IndicadorProcessamento> : null}
      {erroCarga ? (
        <Alert variant="destructive">
          <AlertDescription>Não foi possível ler as conexões. Recarregue a página para tentar de novo.</AlertDescription>
        </Alert>
      ) : null}
      {semConexoes ? (
        <Alert>
          <AlertDescription>
            Nenhuma conexão ativa de embeddings ou de Qdrant está disponível. Cadastre em{" "}
            <Link href="/conexoes" className="font-medium text-primary underline">
              Conexões
            </Link>{" "}
            e volte para publicar.
          </AlertDescription>
        </Alert>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="publicacao-embeddings">Conexão de embeddings</Label>
          <select id="publicacao-embeddings" value={embeddingsId} onChange={(e) => setEmbeddingsId(e.target.value)} className={seletor} disabled={publicando || listaEmbeddings.length === 0}>
            <option value="">Escolha uma conexão</option>
            {listaEmbeddings.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="publicacao-qdrant">Conexão do Qdrant</Label>
          <select id="publicacao-qdrant" value={vectorStoreId} onChange={(e) => setVectorStoreId(e.target.value)} className={seletor} disabled={publicando || listaQdrant.length === 0}>
            <option value="">Escolha uma conexão</option>
            {listaQdrant.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5 md:col-span-2">
          <Label htmlFor="publicacao-colecao">Coleção</Label>
          <Input id="publicacao-colecao" value={colecao} onChange={(e) => setColecao(e.target.value)} disabled={publicando} placeholder="produtos" />
          <p className="text-xs text-muted-foreground">Nome da coleção no Qdrant; é criada se ainda não existir.</p>
          {dimensao ? (
            <p className={`text-sm ${dimensao.compativel ? "text-muted-foreground" : "text-destructive"}`}>
              {!dimensao.compativel
                ? `Dimensões incompatíveis: modelo ${dimensao.embeddings}, coleção ${dimensao.colecao}.`
                : dimensao.colecao === null
                  ? `Coleção nova: será criada com ${dimensao.embeddings} dimensões.`
                  : `Dimensões compatíveis: ${dimensao.embeddings}.`}
            </p>
          ) : null}
        </div>
      </div>
      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border bg-border text-sm sm:grid-cols-4">
        {[
          ["Arquivos", resumo.arquivos],
          ["Chunks", resumo.chunks],
          ["Modelo", nomeEmbeddings ? (nomeEmbeddings.configuracao?.modelo ?? nomeEmbeddings.nome) : "—"],
          ["Destino", nomeQdrant ? nomeQdrant.nome : "—"],
        ].map(([rotulo, valor]) => (
          <div key={String(rotulo)} className="flex min-w-0 flex-col gap-1 bg-background p-3">
            <dt className="text-muted-foreground">{rotulo}</dt>
            <dd className="font-medium [overflow-wrap:anywhere]">{valor}</dd>
          </div>
        ))}
      </dl>
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void publicar()} disabled={publicando}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
      <div className="flex flex-col items-start gap-2">
        <Button type="button" onClick={() => void publicar()} loading={publicando} disabled={razao !== null || publicando || publicado} aria-describedby={razao ? "razao-publicacao" : undefined}>
          Publicar
        </Button>
        {razao ? (
          <p id="razao-publicacao" className="text-sm text-muted-foreground">
            {razao}
          </p>
        ) : null}
        {publicado ? (
          <p role="status" className="text-sm text-muted-foreground">
            Publicação iniciada. Levando você à página da Base para acompanhar o processamento.
          </p>
        ) : null}
      </div>
    </div>
  );
}
