"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import DetailLists from "@/components/DetailLists";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Skeleton } from "@/components/ui/skeleton";
import type { PessoaResumo } from "@/features/pessoas/DataGridPessoas";
import DesativarPessoaDialog from "@/features/pessoas/DesativarPessoaDialog";
import PessoaFormSheet from "@/features/pessoas/PessoaFormSheet";
import RedefinirSenhaDialog from "@/features/pessoas/RedefinirSenhaDialog";
import { ApiError, apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

type Acao = "editar" | "situacao" | "senha" | null;
type Falha = "nao-encontrada" | "sem-permissao" | "carregamento" | null;

const rotulosPapel: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
};

function data(iso?: string) {
  if (!iso) return "—";
  const valor = new Date(iso);
  return Number.isNaN(valor.getTime()) ? iso : valor.toLocaleString("pt-BR");
}

function autor(pessoa: PessoaResumo) {
  if (!pessoa.criada_por) return "Autor não identificado";
  return `${pessoa.criada_por.nome}${pessoa.criada_por.desativada ? " (desativada)" : ""}`;
}

function CarregandoDetalhe() {
  return (
    <section
      className="mx-auto flex w-full max-w-5xl flex-col gap-5"
    >
      <IndicadorProcessamento>Carregando detalhes da pessoa</IndicadorProcessamento>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-7 w-56 max-w-full" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <div className="flex flex-col overflow-hidden rounded-lg border">
        {Array.from({ length: 6 }).map((_, indice) => (
          <div key={indice} className="grid grid-cols-1 gap-2 border-b p-3 last:border-b-0 sm:grid-cols-[minmax(10rem,16rem)_1fr] sm:gap-4">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-full max-w-sm" />
          </div>
        ))}
      </div>
    </section>
  );
}

export default function PessoaDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [eu, setEu] = useState<PessoaSessao | null>(null);
  const [pessoa, setPessoa] = useState<PessoaResumo | null>(null);
  const [falha, setFalha] = useState<Falha>(null);
  const [carregando, setCarregando] = useState(true);
  const [acao, setAcao] = useState<Acao>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setFalha(null);
    try {
      const identidade = await apiJson<PessoaSessao>("/api/v1/auth/me");
      setEu(identidade);
      if (identidade.papel === "member") {
        setPessoa(null);
        setFalha("sem-permissao");
        return;
      }
      setPessoa(await apiJson<PessoaResumo>(`/api/v1/pessoas/${id}`));
    } catch (erro) {
      setPessoa(null);
      if (erro instanceof ApiError && erro.status === 404) setFalha("nao-encontrada");
      else if (erro instanceof ApiError && erro.status === 403) setFalha("sem-permissao");
      else setFalha("carregamento");
    } finally {
      setCarregando(false);
    }
  }

  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps -- leitura inicial por id
  useEffect(() => { void carregar(); }, [id]);

  if (carregando) return <CarregandoDetalhe />;

  if (falha === "sem-permissao") {
    return (
      <section className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <PageHeader title="Acesso restrito" description="Administração das pessoas da equipe." />
        <Alert>
          <AlertDescription>Você não tem permissão para administrar pessoas.</AlertDescription>
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
        <PageHeader title="Pessoa não encontrada" />
        <Alert variant="destructive">
          <AlertDescription>A pessoa não existe ou não pertence à sua equipe.</AlertDescription>
        </Alert>
        <Link href="/pessoas" className="w-fit text-sm font-medium text-primary underline">
          Voltar para Pessoas
        </Link>
      </section>
    );
  }

  if (falha === "carregamento" || !pessoa) {
    return (
      <section className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <PageHeader title="Pessoa" description="Dados de acesso e administração." />
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>Não foi possível carregar esta pessoa. Tente novamente.</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void carregar()}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </section>
    );
  }

  const ativa = pessoa.situacao === "ativa";
  return (
    <section className="mx-auto flex w-full min-w-0 max-w-5xl flex-col gap-5">
      <PageHeader
        title={pessoa.nome}
        status={<Badge variant={ativa ? "secondary" : "outline"}>{ativa ? "Ativa" : "Desativada"}</Badge>}
        description="Dados de acesso e administração desta pessoa."
        actions={(
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setAcao("editar")}>Editar</Button>
            <Button variant="outline" onClick={() => setAcao("senha")}>Redefinir senha</Button>
            <Button variant={ativa ? "destructive" : "default"} onClick={() => setAcao("situacao")}>
              {ativa ? "Desativar" : "Reativar"}
            </Button>
          </div>
        )}
      />
      {feedback ? (
        <Alert>
          <AlertDescription>{feedback}</AlertDescription>
        </Alert>
      ) : null}
      <DetailLists
        items={[
          { label: "E-mail", value: pessoa.email },
          { label: "Papel", value: rotulosPapel[pessoa.papel] ?? pessoa.papel },
          { label: "Situação", value: ativa ? "Ativa" : "Desativada" },
          { label: "Troca de senha pendente", value: pessoa.precisa_trocar_senha ? "Sim" : "Não" },
          { label: "Criada em", value: data(pessoa.criada_em) },
          { label: "Criada por", value: autor(pessoa) },
        ]}
      />
      {acao === "editar" ? (
        <PessoaFormSheet
          open
          pessoa={pessoa}
          podeAtribuirOwner={eu?.papel === "owner"}
          onOpenChange={(aberto) => !aberto && setAcao(null)}
          onSaved={() => {
            setAcao(null);
            setFeedback("Pessoa atualizada.");
            void carregar();
          }}
        />
      ) : null}
      {acao === "situacao" ? (
        <DesativarPessoaDialog
          open
          pessoa={pessoa}
          acao={ativa ? "desativar" : "reativar"}
          bloqueio={pessoa.id === eu?.id ? "Você não pode desativar a própria conta." : undefined}
          onOpenChange={(aberto) => !aberto && setAcao(null)}
          onDone={() => {
            setAcao(null);
            setFeedback(ativa ? "Pessoa desativada." : "Pessoa reativada.");
            void carregar();
          }}
        />
      ) : null}
      {acao === "senha" ? (
        <RedefinirSenhaDialog
          open
          pessoa={pessoa}
          onOpenChange={(aberto) => !aberto && setAcao(null)}
          onDone={() => {
            setAcao(null);
            setFeedback("Senha redefinida. A pessoa deverá trocá-la no próximo acesso.");
          }}
        />
      ) : null}
    </section>
  );
}
