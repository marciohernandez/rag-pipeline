"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import FluxoIngestao from "@/features/ingestao/FluxoIngestao";
import { apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

type Estado = "carregando" | "permitido" | "negado" | "erro";

function EnviarDocumentos() {
  const { id } = useParams<{ id: string }>();
  const colecaoInicial = useSearchParams().get("colecao") ?? undefined;
  const [estado, setEstado] = useState<Estado>("carregando");
  const [leituras, setLeituras] = useState(0);

  useEffect(() => {
    let ativo = true;
    apiJson<PessoaSessao>("/api/v1/auth/me")
      .then((eu) => {
        if (ativo) setEstado(eu.papel === "owner" || eu.papel === "admin" ? "permitido" : "negado");
      })
      .catch(() => {
        if (ativo) setEstado("erro");
      });
    return () => {
      ativo = false;
    };
  }, [leituras]);

  const voltar = (
    <Link href={`/workspaces/${encodeURIComponent(id)}`} className={buttonVariants({ variant: "outline" })}>
      Voltar ao Workspace
    </Link>
  );

  return (
    <section className="mx-auto flex w-full min-w-0 max-w-5xl flex-col gap-5">
      <PageHeader
        title="Enviar documentos"
        description="Envie os arquivos, escolha como dividi-los, revise os chunks e publique em uma coleção do Workspace."
        actions={voltar}
      />
      {estado === "carregando" ? <IndicadorProcessamento>Verificando permissão</IndicadorProcessamento> : null}
      {estado === "negado" ? (
        <Alert>
          <AlertDescription>Somente owner e admin podem enviar documentos.</AlertDescription>
        </Alert>
      ) : null}
      {estado === "erro" ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>Não foi possível validar sua permissão. Tente novamente.</span>
            <Button type="button" variant="outline" size="sm" onClick={() => { setEstado("carregando"); setLeituras((v) => v + 1); }}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
      {estado === "permitido" ? <FluxoIngestao workspaceId={id} colecaoInicial={colecaoInicial} /> : null}
    </section>
  );
}

export default function EnviarDocumentosPage() {
  return (
    <Suspense fallback={<IndicadorProcessamento>Carregando</IndicadorProcessamento>}>
      <EnviarDocumentos />
    </Suspense>
  );
}
