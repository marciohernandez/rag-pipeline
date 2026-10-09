"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import type { EnvioDetalhe } from "@/features/colecoes/tipos";
import DetalheEnvio from "@/features/envios/DetalheEnvio";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

const INTERVALO_POLLING_MS = 3000;

/** Detalhe do envio (SPEC-0030, seção 10): acompanha o progresso e permite Repetir. */
export default function EnvioDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [envio, setEnvio] = useState<EnvioDetalhe | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [releituras, setReleituras] = useState(0);
  const papel = getPapel() ?? undefined;

  useEffect(() => {
    let ativo = true;
    apiJson<EnvioDetalhe>(`/api/v1/envios/${encodeURIComponent(id)}`)
      .then((lido) => {
        if (!ativo) return;
        setEnvio(lido);
        setErro(null);
      })
      .catch((causa) => {
        if (!ativo || (causa instanceof ApiError && causa.unauthorized)) return;
        setErro(
          causa instanceof ApiError && causa.status === 404
            ? "Envio não encontrado."
            : "Não foi possível carregar o envio. Tente novamente.",
        );
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [id, releituras]);

  const emAndamento = envio?.situacao === "queued" || envio?.situacao === "running";
  useEffect(() => {
    if (!emAndamento) return;
    const intervalo = setInterval(() => setReleituras((valor) => valor + 1), INTERVALO_POLLING_MS);
    return () => clearInterval(intervalo);
  }, [emAndamento]);

  const naoEncontrado = erro === "Envio não encontrado.";

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Envio"
        description={
          envio ? `Coleção: ${envio.colecao.nome}` : "Acompanhe o processamento dos documentos enviados."
        }
        actions={
          <Link
            href={envio ? `/workspaces/${encodeURIComponent(envio.colecao.workspace_id)}/colecoes/${encodeURIComponent(envio.colecao.id)}` : "/workspaces"}
            className={buttonVariants({ variant: "outline" })}
          >
            {envio ? "Ver coleção" : "Voltar aos Workspaces"}
          </Link>
        }
      />

      {erro && !envio ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            {!naoEncontrado ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setCarregando(true);
                  setReleituras((valor) => valor + 1);
                }}
              >
                Tentar novamente
              </Button>
            ) : null}
          </AlertDescription>
        </Alert>
      ) : null}

      {carregando && !envio ? <IndicadorProcessamento>Carregando o envio…</IndicadorProcessamento> : null}

      {envio ? (
        <DetalheEnvio envio={envio} papel={papel} onRepetido={() => setReleituras((valor) => valor + 1)} />
      ) : null}
    </div>
  );
}
