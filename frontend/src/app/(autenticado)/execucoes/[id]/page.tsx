"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import PainelProgresso, {
  type Execucao,
} from "@/features/execucoes/PainelProgresso";
import { ApiError, apiJson } from "@/lib/api-client";
import { getPapel } from "@/lib/session";

/**
 * Detalhe da base pelo id na URL (SPEC-0013, seção 10).
 *
 * `[id]` é o id da base: a tela mostra a execução mais recente e o histórico.
 * Enquanto a execução mais recente estiver `pending`/`running`, faz polling
 * do backend (FR-005) — nenhuma chamada toca o banco vetorial (AC-008).
 */

interface BaseDetalhe {
  id: string;
  nome: string;
  origem: string;
  documentos: number;
  criado_em: string;
  execucoes: Execucao[];
}

const SITUACOES_ATIVAS = ["pending", "running"];
const INTERVALO_POLLING_MS = 3000;

export default function ExecucaoDetalhePage() {
  const params = useParams<{ id: string }>();
  const baseId = params.id;

  const [detalhe, setDetalhe] = useState<BaseDetalhe | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [releituras, setReleituras] = useState(0);

  useEffect(() => {
    let ativo = true;
    apiJson<BaseDetalhe>(`/api/v1/bases/${baseId}`)
      .then((dados) => {
        if (ativo) {
          setDetalhe(dados);
          setErro(null);
        }
      })
      .catch((causa) => {
        if (ativo && !(causa instanceof ApiError && causa.unauthorized)) {
          setErro(
            causa instanceof ApiError && causa.status === 404
              ? "Base não encontrada."
              : "Não foi possível carregar o detalhe da base.",
          );
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [baseId, releituras]);

  const execucaoAtual = detalhe?.execucoes[0] ?? null;
  const historico = detalhe?.execucoes.slice(1) ?? [];
  const emAndamento = execucaoAtual
    ? SITUACOES_ATIVAS.includes(execucaoAtual.situacao)
    : false;

  useEffect(() => {
    if (!emAndamento) return;
    const id = setInterval(
      () => setReleituras((valor) => valor + 1),
      INTERVALO_POLLING_MS,
    );
    return () => clearInterval(id);
  }, [emAndamento]);

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title={detalhe ? `Base ${detalhe.nome || detalhe.id}` : "Detalhe da base"}
        description="Acompanhe o processamento e consulte a base indexada."
        actions={
          <Link href="/projeto" className={buttonVariants({ variant: "outline" })}>
            Voltar ao projeto
          </Link>
        }
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}

      {carregando && !detalhe ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : null}

      {execucaoAtual ? (
        <PainelProgresso
          execucao={execucaoAtual}
          papel={getPapel() ?? undefined}
          onRepetida={() => setReleituras((valor) => valor + 1)}
        />
      ) : null}

      {detalhe && detalhe.execucoes.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Esta base ainda não tem execuções.
        </p>
      ) : null}

      {historico.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium">Histórico de execuções</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {historico.map((execucao) => (
              <li
                key={execucao.id}
                className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
              >
                <span className="font-mono text-xs">{execucao.id}</span>
                <span className="text-muted-foreground">
                  {execucao.situacao} · {execucao.etapa || "—"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {/* FormularioConsulta (T031) e ExcluirBaseDialog (T027) entram nas próximas tarefas. */}
    </div>
  );
}
