"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import DataGridPessoas, { type PessoaResumo } from "@/features/pessoas/DataGridPessoas";
import DesativarPessoaDialog from "@/features/pessoas/DesativarPessoaDialog";
import PessoaFormSheet from "@/features/pessoas/PessoaFormSheet";
import { apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

export default function PessoasPage() {
  const [identidade, setIdentidade] = useState<PessoaSessao | null>(null);
  const [pessoas, setPessoas] = useState<PessoaResumo[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [formulario, setFormulario] = useState<PessoaResumo | "nova" | null>(null);
  const [alternar, setAlternar] = useState<PessoaResumo | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const eu = await apiJson<PessoaSessao>("/api/v1/auth/me");
      setIdentidade(eu);
      if (eu.papel === "owner" || eu.papel === "admin") setPessoas(await apiJson<PessoaResumo[]>("/api/v1/pessoas"));
    } catch {
      setErro("Não foi possível carregar as pessoas. Tente novamente.");
    } finally {
      setCarregando(false);
    }
  }
  // eslint-disable-next-line react-hooks/set-state-in-effect -- leitura inicial da rota cliente
  useEffect(() => { void carregar(); }, []);

  if (!carregando && identidade?.papel === "member") return <section className="mx-auto flex max-w-3xl flex-col gap-4"><PageHeader title="Pessoas" description="Administração dos acessos da equipe." /><Alert><AlertDescription>Você não tem permissão para administrar pessoas.</AlertDescription></Alert><Link href="/workspaces" className="text-sm font-medium text-primary underline">Voltar aos Workspaces</Link></section>;

  if (erro) {
    return (
      <section className="mx-auto flex w-full min-w-0 max-w-6xl flex-col gap-5">
        <PageHeader title="Pessoas" description="Gerencie acessos, papéis e situação das pessoas desta equipe." />
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void carregar()}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </section>
    );
  }

  const podeGerir = identidade?.papel === "owner" || identidade?.papel === "admin";

  return <section className="mx-auto flex w-full min-w-0 max-w-6xl flex-col gap-5 overflow-x-hidden"><PageHeader title="Pessoas" description="Gerencie acessos, papéis e situação das pessoas desta equipe." actions={podeGerir ? <Button onClick={() => setFormulario("nova")}>Nova pessoa</Button> : undefined} /><DataGridPessoas pessoas={pessoas} carregando={carregando} onEditar={setFormulario} onAlternarSituacao={setAlternar} />{formulario ? <PessoaFormSheet open pessoa={formulario === "nova" ? undefined : formulario} podeAtribuirOwner={identidade?.papel === "owner"} onOpenChange={(aberto) => !aberto && setFormulario(null)} onSaved={() => { setFormulario(null); void carregar(); }} /> : null}{alternar ? <DesativarPessoaDialog open pessoa={alternar} acao={alternar.situacao === "ativa" ? "desativar" : "reativar"} bloqueio={alternar.id === identidade?.id ? "Você não pode desativar a própria conta." : undefined} onOpenChange={(aberto) => !aberto && setAlternar(null)} onDone={() => { setAlternar(null); void carregar(); }} /> : null}</section>;
}
