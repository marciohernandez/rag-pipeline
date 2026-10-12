"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import ConexaoFormSheet from "@/features/conexoes/ConexaoFormSheet";
import DataGridConexoes, { type ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import ExcluirConexaoDialog from "@/features/conexoes/ExcluirConexaoDialog";
import { apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

const DESCRICAO = "Cadastre as conexões de embeddings e de Qdrant que as coleções usam ao receber documentos.";

export default function ConexoesPage() {
  const [identidade, setIdentidade] = useState<PessoaSessao | null>(null);
  const [conexoes, setConexoes] = useState<ConexaoResumo[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [formulario, setFormulario] = useState<ConexaoResumo | "nova" | null>(null);
  const [exclusao, setExclusao] = useState<ConexaoResumo | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const eu = await apiJson<PessoaSessao>("/api/v1/auth/me");
      setIdentidade(eu);
      if (eu.papel === "owner" || eu.papel === "admin") {
        setConexoes(await apiJson<ConexaoResumo[]>("/api/v1/conexoes"));
      }
    } catch {
      setErro("Não foi possível carregar as conexões. Tente novamente.");
    } finally {
      setCarregando(false);
    }
  }
  // eslint-disable-next-line react-hooks/set-state-in-effect -- leitura inicial da rota cliente
  useEffect(() => { void carregar(); }, []);

  async function alternar(conexao: ConexaoResumo) {
    const ativa = conexao.situacao === "ativa";
    try {
      await apiJson(`/api/v1/conexoes/${conexao.id}/${ativa ? "desativar" : "reativar"}`, { method: "POST" });
      setAviso(`Conexão ${conexao.nome} ${ativa ? "desativada" : "reativada"}.`);
      await carregar();
    } catch {
      setErro(`Não foi possível ${ativa ? "desativar" : "reativar"} a conexão. Tente novamente.`);
    }
  }

  if (!carregando && identidade?.papel === "member") {
    return (
      <section className="mx-auto flex max-w-3xl flex-col gap-4">
        <PageHeader title="Conexões" description={DESCRICAO} />
        <Alert>
          <AlertDescription>Você não tem permissão para administrar conexões.</AlertDescription>
        </Alert>
        <Link href="/workspaces" className="text-sm font-medium text-primary underline">
          Voltar aos Workspaces
        </Link>
      </section>
    );
  }

  const podeGerir = identidade?.papel === "owner" || identidade?.papel === "admin";

  return (
    <section className="mx-auto flex w-full min-w-0 max-w-6xl flex-col gap-5 overflow-x-hidden">
      <PageHeader
        title="Conexões"
        description={DESCRICAO}
        actions={podeGerir ? <Button onClick={() => setFormulario("nova")}>Nova conexão</Button> : undefined}
      />
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void carregar()}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
      <div role="status" aria-live="polite">
        {aviso ? (
          <Alert>
            <AlertDescription>{aviso}</AlertDescription>
          </Alert>
        ) : null}
      </div>
      {erro && conexoes.length === 0 ? null : (
        <DataGridConexoes
          conexoes={conexoes}
          carregando={carregando}
          onEditar={setFormulario}
          onAlternarSituacao={(c) => void alternar(c)}
          onExcluir={setExclusao}
        />
      )}
      {formulario ? (
        <ConexaoFormSheet
          open
          conexao={formulario === "nova" ? undefined : formulario}
          onOpenChange={(aberto) => !aberto && setFormulario(null)}
          onSaved={(salva) => {
            setFormulario(null);
            setAviso(`Conexão ${salva.nome} salva.${salva.teste ? ` ${salva.teste.mensagem}` : ""}`);
            void carregar();
          }}
        />
      ) : null}
      {exclusao ? (
        <ExcluirConexaoDialog
          open
          conexao={exclusao}
          onOpenChange={(aberto) => !aberto && setExclusao(null)}
          onDeleted={() => {
            setAviso(`Conexão ${exclusao.nome} excluída.`);
            setExclusao(null);
            void carregar();
          }}
        />
      ) : null}
    </section>
  );
}
