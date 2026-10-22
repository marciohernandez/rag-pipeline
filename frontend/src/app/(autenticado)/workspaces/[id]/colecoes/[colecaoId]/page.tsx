"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import AbasColecao from "@/features/colecoes/AbasColecao";
import ApagarColecaoDialog from "@/features/colecoes/ApagarColecaoDialog";
import RenomearColecaoSheet from "@/features/colecoes/RenomearColecaoSheet";
import BotaoAnalisarContradicoes from "@/features/contradicoes/BotaoAnalisarContradicoes";
import type { ColecaoDetalhe, DocumentoResumo, EnvioResumo } from "@/features/colecoes/tipos";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];
const INTERVALO_POLLING_MS = 3000;

function DetalheColecao() {
  const params = useParams<{ id: string; colecaoId: string }>();
  const router = useRouter();
  const { id: workspaceId, colecaoId } = params;
  const [colecao, setColecao] = useState<ColecaoDetalhe | null>(null);
  const [documentos, setDocumentos] = useState<DocumentoResumo[]>([]);
  const [envios, setEnvios] = useState<EnvioResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [naoEncontrada, setNaoEncontrada] = useState(false);
  const [releituras, setReleituras] = useState(0);
  const [renomearAberto, setRenomearAberto] = useState(false);
  const [apagarAberto, setApagarAberto] = useState(false);
  const papel = getPapel() ?? undefined;
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const base = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}`;

  useEffect(() => {
    let ativo = true;
    Promise.all([
      apiJson<ColecaoDetalhe>(base),
      apiJson<DocumentoResumo[]>(`${base}/documentos`),
      apiJson<EnvioResumo[]>(`${base}/envios`),
    ])
      .then(([lida, docs, envs]) => {
        if (!ativo) return;
        setColecao(lida);
        setDocumentos(docs);
        setEnvios(envs);
        setErro(null);
      })
      .catch((causa) => {
        if (!ativo || (causa instanceof ApiError && causa.unauthorized)) return;
        if (causa instanceof ApiError && causa.status === 404) {
          setNaoEncontrada(true);
          setErro("Coleção não encontrada.");
        } else {
          setErro("Não foi possível carregar a coleção. Tente novamente.");
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [base, releituras]);

  const emAndamento = envios.some((envio) => envio.situacao === "queued" || envio.situacao === "running");
  useEffect(() => {
    if (!emAndamento) return;
    const intervalo = setInterval(() => setReleituras((valor) => valor + 1), INTERVALO_POLLING_MS);
    return () => clearInterval(intervalo);
  }, [emAndamento]);

  function reler() {
    setCarregando(true);
    setErro(null);
    setNaoEncontrada(false);
    setReleituras((valor) => valor + 1);
  }

  const acoes = (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Link href={`/workspaces/${encodeURIComponent(workspaceId)}`} className={buttonVariants({ variant: "outline" })}>
        Voltar ao Workspace
      </Link>
      {colecao ? (
        <Link
          href={`/workspaces/${encodeURIComponent(workspaceId)}/colecoes/${encodeURIComponent(colecao.id)}/contradicoes`}
          className={buttonVariants({ variant: "outline" })}
        >
          Ver contradições
        </Link>
      ) : null}
      {podeEscrever && colecao ? (
        <>
          <BotaoAnalisarContradicoes
            colecaoId={colecao.id}
            provedor={null}
            onIniciada={() =>
              router.push(
                `/workspaces/${encodeURIComponent(workspaceId)}/colecoes/${encodeURIComponent(colecao.id)}/contradicoes`,
              )
            }
          />
          <Link
            href={`/workspaces/${encodeURIComponent(workspaceId)}/enviar?colecao=${encodeURIComponent(colecao.id)}`}
            className={buttonVariants({ variant: "default" })}
          >
            Adicionar documentos
          </Link>
          <Button type="button" variant="outline" onClick={() => setRenomearAberto(true)}>
            Renomear
          </Button>
          <Button type="button" variant="destructive" onClick={() => setApagarAberto(true)}>
            Apagar
          </Button>
        </>
      ) : null}
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title={colecao?.nome ?? (naoEncontrada ? "Coleção não encontrada" : "Coleção")}
        description={
          colecao
            ? `Embeddings: ${colecao.conexao_embeddings.nome} · Qdrant: ${colecao.conexao_vector_store.nome} · ${colecao.dimensao} dimensões`
            : "Documentos, envios e consulta desta coleção."
        }
        actions={acoes}
      />

      {erro && (naoEncontrada || !colecao) ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            {!naoEncontrada ? (
              <Button type="button" variant="outline" size="sm" onClick={reler}>
                Tentar novamente
              </Button>
            ) : null}
          </AlertDescription>
        </Alert>
      ) : colecao ? (
        <AbasColecao
          workspaceId={workspaceId}
          colecao={{ id: colecao.id, nome: colecao.nome }}
          papel={papel}
          documentos={documentos}
          envios={envios}
          estado={carregando ? "carregando" : undefined}
          onTentarNovamente={reler}
          onDocumentoApagado={(id) => setDocumentos((atuais) => atuais.filter((d) => d.id !== id))}
          onEnvioRepetido={reler}
        />
      ) : (
        <IndicadorProcessamento>Carregando a coleção…</IndicadorProcessamento>
      )}

      {colecao && renomearAberto ? (
        <RenomearColecaoSheet
          open
          colecao={colecao}
          onOpenChange={setRenomearAberto}
          onSaved={(salva) => {
            setColecao({ ...colecao, nome: salva.nome });
            setRenomearAberto(false);
          }}
        />
      ) : null}
      {colecao && apagarAberto ? (
        <ApagarColecaoDialog
          open
          colecao={colecao}
          onOpenChange={setApagarAberto}
          onDeleted={() => router.push(`/workspaces/${encodeURIComponent(workspaceId)}`)}
        />
      ) : null}
    </div>
  );
}

export default function ColecaoDetalhePage() {
  return (
    <Suspense fallback={<IndicadorProcessamento>Carregando a coleção…</IndicadorProcessamento>}>
      <DetalheColecao />
    </Suspense>
  );
}
