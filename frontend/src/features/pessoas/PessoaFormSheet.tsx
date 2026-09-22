"use client";

import { useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { PessoaResumo } from "@/features/pessoas/DataGridPessoas";
import { ApiError, apiJson } from "@/lib/api-client";

interface Props {
  open: boolean;
  pessoa?: PessoaResumo;
  podeAtribuirOwner?: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onSaved?: (pessoa: PessoaResumo) => void;
}

export default function PessoaFormSheet({ open, pessoa, podeAtribuirOwner = false, onOpenChange, onSaved }: Props) {
  const [nome, setNome] = useState(pessoa?.nome ?? "");
  const [email, setEmail] = useState(pessoa?.email ?? "");
  const [papel, setPapel] = useState(pessoa?.papel ?? "member");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [campoErro, setCampoErro] = useState<"nome" | "email" | "senha" | null>(null);
  const [salvando, setSalvando] = useState(false);
  const campoNome = useRef<HTMLInputElement>(null);
  const campoEmail = useRef<HTMLInputElement>(null);
  const campoSenha = useRef<HTMLInputElement>(null);
  const editando = pessoa !== undefined;

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setErro(null); setCampoErro(null);
    if (!nome.trim()) { setCampoErro("nome"); setErro("Informe o nome."); campoNome.current?.focus(); return; }
    if (!email.includes("@")) { setCampoErro("email"); setErro("Informe um e-mail válido."); campoEmail.current?.focus(); return; }
    if (!editando && senha.length < 10) { setCampoErro("senha"); setErro("A senha precisa ter pelo menos 10 caracteres."); campoSenha.current?.focus(); return; }
    setSalvando(true);
    try {
      const salvo = await apiJson<PessoaResumo>(editando ? `/api/v1/pessoas/${pessoa.id}` : "/api/v1/pessoas", { method: editando ? "PATCH" : "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(editando ? { nome: nome.trim(), email: email.trim(), papel } : { nome: nome.trim(), email: email.trim(), papel, senha_inicial: senha }) });
      onSaved?.(salvo);
      onOpenChange?.(false);
    } catch (falha) {
      const mensagem = falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível salvar a pessoa.";
      const duplicado = falha instanceof ApiError && falha.status === 409 && /e-mail/i.test(mensagem);
      setCampoErro(duplicado ? "email" : "nome"); setErro(mensagem); (duplicado ? campoEmail : campoNome).current?.focus();
    } finally { setSalvando(false); }
  }

  const erroDe = (campo: typeof campoErro) => campoErro === campo ? erro : null;
  return <Sheet open={open} onOpenChange={(aberto) => !salvando && onOpenChange?.(aberto)}><SheetContent side="right" className="w-full sm:max-w-lg"><SheetHeader><SheetTitle>{editando ? "Editar pessoa" : "Nova pessoa"}</SheetTitle><SheetDescription>{editando ? "Corrija os dados e o papel desta pessoa." : "Crie o acesso e compartilhe a senha inicial por um canal seguro."}</SheetDescription></SheetHeader><form onSubmit={salvar} className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4">
    <div className="flex flex-col gap-1.5"><Label htmlFor="pessoa-nome">Nome</Label><Input ref={campoNome} id="pessoa-nome" value={nome} onChange={(e) => setNome(e.target.value)} aria-invalid={campoErro === "nome" ? "true" : undefined} />{erroDe("nome") ? <p role="alert" className="text-sm text-destructive">{erroDe("nome")}</p> : null}</div>
    <div className="flex flex-col gap-1.5"><Label htmlFor="pessoa-email">E-mail</Label><Input ref={campoEmail} id="pessoa-email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={campoErro === "email" ? "true" : undefined} />{erroDe("email") ? <p role="alert" className="text-sm text-destructive">{erroDe("email")}</p> : null}</div>
    <div className="flex flex-col gap-1.5"><Label htmlFor="pessoa-papel">Papel</Label><select id="pessoa-papel" value={papel} onChange={(e) => setPapel(e.target.value)} className="h-8 rounded-lg border bg-background px-2.5 text-sm focus-visible:ring-3 focus-visible:ring-ring/50"><option value="member">member</option><option value="admin">admin</option>{podeAtribuirOwner ? <option value="owner">owner</option> : null}</select></div>
    {!editando ? <div className="flex flex-col gap-1.5"><Label htmlFor="pessoa-senha">Senha inicial</Label><Input ref={campoSenha} id="pessoa-senha" type="password" autoComplete="new-password" value={senha} onChange={(e) => setSenha(e.target.value)} aria-invalid={campoErro === "senha" ? "true" : undefined} />{erroDe("senha") ? <p role="alert" className="text-sm text-destructive">{erroDe("senha")}</p> : null}</div> : null}
    <SheetFooter className="-mx-4 flex-row justify-end border-t"><Button type="button" variant="outline" onClick={() => onOpenChange?.(false)} disabled={salvando}>Cancelar</Button><Button type="submit" disabled={salvando}>{salvando ? "Salvando…" : "Salvar"}</Button></SheetFooter>
  </form></SheetContent></Sheet>;
}
