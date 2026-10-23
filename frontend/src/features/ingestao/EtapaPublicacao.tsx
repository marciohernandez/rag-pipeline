"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ColecaoDetalhe, ColecaoResumo } from "@/features/colecoes/tipos";
import ConexaoFormSheet from "@/features/conexoes/ConexaoFormSheet";
import type { ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import type { ValoresPublicacao } from "@/features/ingestao/useFluxoIngestao";
import { ApiError, apiJson } from "@/lib/api-client";
import { seletor } from "@/features/ingestao/seletor";
import { slugFisico } from "@/lib/ingestao";

interface Props {
  resumo: { arquivos: number; chunks: number; origemLote?: boolean };
  workspaceId: string;
  /** Coleção pré-selecionada por "Adicionar documentos" ou "Substituir" (SPEC-0030, FR-002). */
  colecaoInicial?: string;
  onPublicar: (valores: ValoresPublicacao) => Promise<{ envio_id: string; colecao_id: string }>;
}

type Modo = "existente" | "nova";


/**
 * Etapa Publicação (SPEC-0026, SPEC-0030): escolhe uma coleção existente, com as
 * conexões dela travadas, ou cria uma nova com nome e conexões. Resumo e Publicar
 * bloqueado com a razão visível; a garantia final (nome único, conexões fixas e
 * dimensão) continua no servidor, antes de gravar qualquer coisa.
 */
export default function EtapaPublicacao({ resumo, workspaceId, colecaoInicial, onPublicar }: Props) {
  const router = useRouter();
  const [conexoes, setConexoes] = useState<ConexaoResumo[] | null>(null);
  const [erroCarga, setErroCarga] = useState(false);
  const [embeddingsId, setEmbeddingsId] = useState("");
  const [vectorStoreId, setVectorStoreId] = useState("");
  const [modo, setModo] = useState<Modo>(colecaoInicial ? "existente" : "nova");
  const [nomeNova, setNomeNova] = useState("");
  const [colecoes, setColecoes] = useState<ColecaoResumo[] | null>(null);
  const [colecaoId, setColecaoId] = useState(colecaoInicial ?? "");
  const [detalhe, setDetalhe] = useState<ColecaoDetalhe | null>(null);
  const [publicando, setPublicando] = useState(false);
  const [publicado, setPublicado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [painelConexao, setPainelConexao] = useState(false);
  const [testesFalhos, setTestesFalhos] = useState<Set<string>>(new Set());
  const [avisoTeste, setAvisoTeste] = useState<string | null>(null);
  const [avancadoAberto, setAvancadoAberto] = useState(false);
  const [lote, setLote] = useState("50");

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

  /** Conexão cadastrada no painel: recarrega a lista e já a deixa selecionada (SPEC-0029). */
  async function aoSalvarConexao(salva: ConexaoResumo) {
    if (salva.teste && !salva.teste.sucesso) {
      setTestesFalhos((atual) => new Set(atual).add(salva.id));
      setAvisoTeste(null);
    } else {
      setAvisoTeste(salva.teste?.mensagem ?? `Conexão ${salva.nome} salva.`);
    }
    try {
      setConexoes(await apiJson<ConexaoResumo[]>("/api/v1/conexoes"));
      setErroCarga(false);
    } catch {
      setErroCarga(true);
    }
    if (salva.tipo === "qdrant") setVectorStoreId(salva.id);
    else setEmbeddingsId(salva.id);
  }

  useEffect(() => {
    let ativo = true;
    apiJson<ColecaoResumo[]>(`/api/v1/workspaces/${encodeURIComponent(workspaceId)}/colecoes`)
      .then((lista) => {
        if (ativo) setColecoes(lista);
      })
      .catch(() => {
        if (ativo) setColecoes([]);
      });
    return () => {
      ativo = false;
    };
  }, [workspaceId]);

  useEffect(() => {
    if (!colecaoId) return;
    let ativo = true;
    apiJson<ColecaoDetalhe>(`/api/v1/colecoes/${encodeURIComponent(colecaoId)}`)
      .then((lido) => {
        if (ativo) setDetalhe(lido);
      })
      .catch(() => {
        if (ativo) setDetalhe(null);
      });
    return () => {
      ativo = false;
    };
  }, [colecaoId]);

  function escolherColecao(id: string) {
    setDetalhe(null);
    setColecaoId(id);
  }

  const semConexoes = conexoes !== null && (listaEmbeddings.length === 0 || listaQdrant.length === 0);
  const slugNova = slugFisico(nomeNova);
  const razao = (() => {
    if (resumo.chunks === 0) return "Não há chunks para publicar.";
    const valorLote = Number(lote);
    if (!Number.isInteger(valorLote) || valorLote < 1 || valorLote > 500) {
      return "O tamanho do lote de embeddings deve ficar entre 1 e 500.";
    }
    if (modo === "existente") {
      if (colecoes === null) return "Carregando as coleções.";
      if (!colecaoId) return "Escolha a coleção para publicar.";
      if (!detalhe) return "Carregando a coleção.";
      return null;
    }
    if (conexoes === null) return erroCarga ? "Não foi possível ler as conexões." : "Carregando as conexões.";
    if (semConexoes) return "Publicar bloqueado: faltam conexões ativas.";
    if (!embeddingsId || !vectorStoreId) return "Escolha as duas conexões para publicar.";
    if (!nomeNova.trim()) return "Informe o nome da coleção para publicar.";
    if (!/[A-Za-z0-9]/.test(slugNova)) return "Corrija o nome da coleção para publicar.";
    if (nomeNova.trim().length > 80) return "O nome da coleção deve ter até 80 caracteres.";
    return null;
  })();

  async function publicar() {
    setPublicando(true);
    setErro(null);
    try {
      const destino = { batch_size: Number(lote) };
      const resposta = await onPublicar(
        modo === "existente"
          ? { colecaoId, destino }
          : {
              novaColecao: nomeNova.trim(),
              conexaoEmbeddingsId: embeddingsId,
              conexaoVectorStoreId: vectorStoreId,
              destino,
            },
      );
      setPublicado(true);
      router.push(`/envios/${resposta.envio_id}`);
    } catch (falha) {
      setErro(
        falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível publicar. Tente novamente.",
      );
    } finally {
      setPublicando(false);
    }
  }

  const nomeEmbeddings =
    modo === "existente" ? detalhe?.conexao_embeddings.nome : listaEmbeddings.find((c) => c.id === embeddingsId)?.nome;
  const nomeQdrant =
    modo === "existente" ? detalhe?.conexao_vector_store.nome : listaQdrant.find((c) => c.id === vectorStoreId)?.nome;

  return (
    <div className="flex flex-col gap-4">
      {conexoes === null && !erroCarga ? <IndicadorProcessamento>Carregando conexões</IndicadorProcessamento> : null}
      {erroCarga ? (
        <Alert variant="destructive">
          <AlertDescription>Não foi possível ler as conexões. Recarregue a página para tentar de novo.</AlertDescription>
        </Alert>
      ) : null}
      <fieldset role="radiogroup" className="flex flex-col gap-2" disabled={publicando}>
        <legend className="mb-1 text-sm font-medium">Coleção de destino</legend>
        <div className="flex flex-wrap gap-4">
          {([
            ["existente", "Coleção existente"],
            ["nova", "Nova coleção"],
          ] as const).map(([valor, rotulo]) => (
            <label key={valor} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="modo-colecao"
                value={valor}
                checked={modo === valor}
                onChange={() => setModo(valor)}
                className="size-4 accent-primary"
              />
              {rotulo}
            </label>
          ))}
        </div>
      </fieldset>
      {modo === "existente" ? (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="publicacao-colecao-existente">Coleção</Label>
            <select
              id="publicacao-colecao-existente"
              value={colecaoId}
              onChange={(e) => escolherColecao(e.target.value)}
              className={seletor}
              disabled={publicando || colecoes === null || colecoes.length === 0}
            >
              <option value="">Escolha uma coleção</option>
              {(colecoes ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
            {colecoes !== null && colecoes.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Este Workspace ainda não tem coleções. Escolha Nova coleção.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Os arquivos novos são somados, os idênticos são mantidos e os de mesmo nome substituem a versão anterior.
              </p>
            )}
          </div>
          <p className="self-end text-sm text-muted-foreground">
            As conexões são as da coleção e não podem ser trocadas.
          </p>
        </div>
      ) : (
        <>
          {semConexoes ? (
            <Alert>
              <AlertDescription>
                Nenhuma conexão ativa de embeddings ou de Qdrant está disponível. Use Cadastrar conexão abaixo,
                sem sair desta etapa, ou cadastre em{" "}
                <Link href="/conexoes" className="font-medium text-primary underline">
                  Conexões
                </Link>
                .
              </AlertDescription>
            </Alert>
          ) : null}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-1.5 md:col-span-2">
              <Label htmlFor="publicacao-nome-colecao">Nome da coleção</Label>
              <Input
                id="publicacao-nome-colecao"
                value={nomeNova}
                onChange={(e) => setNomeNova(e.target.value)}
                disabled={publicando}
                maxLength={80}
                placeholder="Ex.: manuais"
              />
              {nomeNova.trim() ? (
                <p className="text-xs text-muted-foreground [overflow-wrap:anywhere]">
                  {/[A-Za-z0-9]/.test(slugNova)
                    ? `Nome no Qdrant: ${slugNova}`
                    : "O nome da coleção precisa ter ao menos uma letra ou número."}
                </p>
              ) : null}
              <p className="text-xs text-muted-foreground">
                O nome exibido pode ser alterado depois; o nome no Qdrant não muda depois.
              </p>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="publicacao-embeddings">Conexão de embeddings</Label>
              <select id="publicacao-embeddings" value={embeddingsId} onChange={(e) => setEmbeddingsId(e.target.value)} className={seletor} disabled={publicando || listaEmbeddings.length === 0}>
                <option value="">Escolha uma conexão</option>
                {listaEmbeddings.map((c) => (
                  <option key={c.id} value={c.id}>
                    {testesFalhos.has(c.id) ? `${c.nome} (teste falhou)` : c.nome}
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
                    {testesFalhos.has(c.id) ? `${c.nome} (teste falhou)` : c.nome}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col items-start gap-2 md:col-span-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setPainelConexao(true)} disabled={publicando}>
                Cadastrar conexão
              </Button>
              <div role="status" aria-live="polite" className="text-sm text-muted-foreground">
                {avisoTeste}
              </div>
            </div>
          </div>
        </>
      )}
      <div className="flex flex-col gap-3 rounded-lg border p-3">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="self-start"
          aria-expanded={avancadoAberto}
          aria-controls="publicacao-avancado"
          onClick={() => setAvancadoAberto((aberto) => !aberto)}
        >
          {avancadoAberto ? "Ocultar Avançado" : "Avançado"}
        </Button>
        {avancadoAberto ? (
          <div id="publicacao-avancado" className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="publicacao-lote">Tamanho do lote de embeddings</Label>
              <Input
                id="publicacao-lote"
                type="number"
                min={1}
                max={500}
                value={lote}
                onChange={(e) => setLote(e.target.value)}
                disabled={publicando}
              />
              <p className="text-xs text-muted-foreground">Textos enviados por chamada ao provedor, de 1 a 500.</p>
            </div>
          </div>
        ) : null}
      </div>
      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border bg-border text-sm sm:grid-cols-4">
        {[
          ["Arquivos", resumo.arquivos],
          ["Chunks", resumo.chunks],
          ["Embeddings", nomeEmbeddings ?? "—"],
          ["Destino", nomeQdrant ?? "—"],
        ].map(([rotulo, valor]) => (
          <div key={String(rotulo)} className="flex min-w-0 flex-col gap-1 bg-background p-3">
            <dt className="text-muted-foreground">{rotulo}</dt>
            <dd className="font-medium [overflow-wrap:anywhere]">{valor}</dd>
          </div>
        ))}
      </dl>
      {resumo.origemLote ? (
        <Alert>
          <AlertDescription>
            A indexação gera embeddings de {resumo.arquivos}{" "}
            {resumo.arquivos === 1 ? "documento" : "documentos"} do lote
            {nomeQdrant ? ` e grava em ${nomeQdrant}` : ""}. Nada é indexado antes de você publicar.
          </AlertDescription>
        </Alert>
      ) : null}
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
            Publicação iniciada. Levando você ao envio para acompanhar o processamento.
          </p>
        ) : null}
      </div>
      {painelConexao ? (
        <ConexaoFormSheet
          open
          onOpenChange={(aberto) => !aberto && setPainelConexao(false)}
          onSaved={(salva) => void aoSalvarConexao(salva)}
        />
      ) : null}
    </div>
  );
}
