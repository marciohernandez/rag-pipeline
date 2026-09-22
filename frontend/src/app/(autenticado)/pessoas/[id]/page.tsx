"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import DetailLists from "@/components/DetailLists";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PessoaResumo } from "@/features/pessoas/DataGridPessoas";
import DesativarPessoaDialog from "@/features/pessoas/DesativarPessoaDialog";
import PessoaFormSheet from "@/features/pessoas/PessoaFormSheet";
import RedefinirSenhaDialog from "@/features/pessoas/RedefinirSenhaDialog";
import { ApiError, apiJson } from "@/lib/api-client";
import type { PessoaSessao } from "@/lib/session";

function data(iso?: string) { if (!iso) return "—"; const d = new Date(iso); return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("pt-BR"); }

export default function PessoaDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [eu, setEu] = useState<PessoaSessao | null>(null); const [pessoa, setPessoa] = useState<PessoaResumo | null>(null); const [erro, setErro] = useState<string | null>(null); const [acao, setAcao] = useState<"editar" | "situacao" | "senha" | null>(null);
  async function carregar() { try { const identidade = await apiJson<PessoaSessao>("/api/v1/auth/me"); setEu(identidade); setPessoa(await apiJson<PessoaResumo>(`/api/v1/pessoas/${id}`)); } catch (falha) { setErro(falha instanceof ApiError && falha.status === 404 ? "Pessoa não encontrada." : "Não foi possível carregar esta pessoa."); } }
  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps -- leitura inicial por id
  useEffect(() => { void carregar(); }, [id]);
  if (erro) return <Alert variant="destructive"><AlertDescription>{erro}</AlertDescription></Alert>;
  if (!pessoa) return <p role="status" className="text-sm text-muted-foreground">Carregando pessoa…</p>;
  const ativa = pessoa.situacao === "ativa";
  return <section className="mx-auto flex w-full max-w-5xl flex-col gap-5"><PageHeader title={pessoa.nome} status={<Badge variant={ativa ? "secondary" : "outline"}>{ativa ? "Ativa" : "Desativada"}</Badge>} description="Dados de acesso e administração desta pessoa." actions={<div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => setAcao("editar")}>Editar</Button><Button variant="outline" onClick={() => setAcao("senha")}>Redefinir senha</Button><Button variant={ativa ? "destructive" : "default"} onClick={() => setAcao("situacao")}>{ativa ? "Desativar" : "Reativar"}</Button></div>} /><DetailLists items={[{ label: "E-mail", value: pessoa.email }, { label: "Papel", value: pessoa.papel }, { label: "Situação", value: ativa ? "Ativa" : "Desativada" }, { label: "Troca de senha pendente", value: pessoa.precisa_trocar_senha ? "Sim" : "Não" }, { label: "Criada em", value: data(pessoa.criada_em) }, { label: "Criada por", value: pessoa.criada_por?.nome ?? "Autor não identificado" }]} />{acao === "editar" ? <PessoaFormSheet open pessoa={pessoa} podeAtribuirOwner={eu?.papel === "owner"} onOpenChange={(aberto) => !aberto && setAcao(null)} onSaved={() => { setAcao(null); void carregar(); }} /> : null}{acao === "situacao" ? <DesativarPessoaDialog open pessoa={pessoa} acao={ativa ? "desativar" : "reativar"} bloqueio={pessoa.id === eu?.id ? "Você não pode desativar a própria conta." : undefined} onOpenChange={(aberto) => !aberto && setAcao(null)} onDone={() => { setAcao(null); void carregar(); }} /> : null}{acao === "senha" ? <RedefinirSenhaDialog open pessoa={pessoa} onOpenChange={(aberto) => !aberto && setAcao(null)} onDone={() => setAcao(null)} /> : null}</section>;
}
