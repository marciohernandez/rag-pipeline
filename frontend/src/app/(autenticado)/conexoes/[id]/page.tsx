"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ConexaoFormSheet from "@/features/conexoes/ConexaoFormSheet";
import type { ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import DetalheConexao from "@/features/conexoes/DetalheConexao";
import ExcluirConexaoDialog from "@/features/conexoes/ExcluirConexaoDialog";
import { ApiError, apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

type Falha = "nao-encontrada" | "sem-permissao" | "carregamento" | null;
type Acao = "editar" | "excluir" | null;

export default function ConexaoDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [conexao, setConexao] = useState<ConexaoResumo | null>(null);
  const [falha, setFalha] = useState<Falha>(null);
  const [carregando, setCarregando] = useState(true);
  const [acao, setAcao] = useState<Acao>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setFalha(null);
    try {
      const eu = await apiJson<PessoaSessao>("/api/v1/auth/me");
      if (eu.papel === "member") {
        setConexao(null);
        setFalha("sem-permissao");
        return;
      }
      setConexao(await apiJson<ConexaoResumo>(`/api/v1/conexoes/${id}`));
    } catch (erro) {
      setConexao(null);
      if (erro instanceof ApiError && erro.status === 404) setFalha("nao-encontrada");
      else if (erro instanceof ApiError && erro.status === 403) setFalha("sem-permissao");
      else setFalha("carregamento");
    } finally {
      setCarregando(false);
    }
  }
  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps -- leitura inicial por id
  useEffect(() => { void carregar(); }, [id]);

  async function alternar() {
    if (!conexao) return;
    const ativa = conexao.situacao === "ativa";
    try {
      setConexao(await apiJson<ConexaoResumo>(`/api/v1/conexoes/${conexao.id}/${ativa ? "desativar" : "reativar"}`, { method: "POST" }));
      setAviso(ativa ? "Conexão desativada." : "Conexão reativada.");
    } catch {
      setFalha("carregamento");
    }
  }

  if (carregando) {
    return (
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-5">
        <IndicadorProcessamento>Carregando detalhes da conexão</IndicadorProcessamento>
        <Skeleton className="h-7 w-56 max-w-full" />
        <Skeleton className="h-40 w-full" />
      </section>
    );
  }

  if (falha === "sem-permissao") {
    return (
      <section className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <PageHeader title="Acesso restrito" description="Administração das conexões de ingestão." />
        <Alert>
          <AlertDescription>Você não tem permissão para administrar conexões.</AlertDescription>
        </Alert>
        <Link href="/workspaces" className="w-fit text-sm font-medium text-primary underline">
          Voltar aos Workspaces
        </Link>
      </section>
    );
  }

  if (falha === "nao-encontrada") {
    return (
      <section className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <PageHeader title="Conexão não encontrada" />
        <Alert variant="destructive">
          <AlertDescription>A conexão não existe ou não pertence à sua equipe.</AlertDescription>
        </Alert>
        <Link href="/conexoes" className="w-fit text-sm font-medium text-primary underline">
          Voltar para Conexões
        </Link>
      </section>
    );
  }

  if (falha === "carregamento" || !conexao) {
    return (
      <section className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <PageHeader title="Conexão" description="Dados da conexão de ingestão." />
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>Não foi possível carregar esta conexão. Tente novamente.</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void carregar()}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </section>
    );
  }

  const ativa = conexao.situacao === "ativa";
  return (
    <section className="mx-auto flex w-full min-w-0 max-w-5xl flex-col gap-5">
      <PageHeader
        title={conexao.nome}
        status={<Badge variant={ativa ? "secondary" : "outline"}>{ativa ? "Ativa" : "Desativada"}</Badge>}
        description="Dados da conexão reutilizável de ingestão."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setAcao("editar")}>Editar</Button>
            <Button variant="outline" onClick={() => void alternar()}>{ativa ? "Desativar" : "Reativar"}</Button>
            <Button variant="destructive" onClick={() => setAcao("excluir")}>Excluir</Button>
          </div>
        }
      />
      <div role="status" aria-live="polite">
        {aviso ? (
          <Alert>
            <AlertDescription>{aviso}</AlertDescription>
          </Alert>
        ) : null}
      </div>
      <DetalheConexao conexao={conexao} />
      {acao === "editar" ? (
        <ConexaoFormSheet
          open
          conexao={conexao}
          onOpenChange={(aberto) => !aberto && setAcao(null)}
          onSaved={(salva) => {
            setAcao(null);
            setConexao(salva);
            setAviso("Conexão atualizada.");
          }}
        />
      ) : null}
      {acao === "excluir" ? (
        <ExcluirConexaoDialog
          open
          conexao={conexao}
          onOpenChange={(aberto) => !aberto && setAcao(null)}
          onDeleted={() => router.push("/conexoes")}
        />
      ) : null}
    </section>
  );
}
