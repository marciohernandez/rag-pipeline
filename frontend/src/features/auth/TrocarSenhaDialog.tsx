"use client";

import { useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";

interface Props {
  open: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onChanged?: () => void;
}

export default function TrocarSenhaDialog({ open, onOpenChange, onChanged }: Props) {
  const campoAtual = useRef<HTMLInputElement>(null);
  const campoNova = useRef<HTMLInputElement>(null);
  const campoConfirmacao = useRef<HTMLInputElement>(null);
  const [atual, setAtual] = useState("");
  const [nova, setNova] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [campoErro, setCampoErro] = useState<"atual" | "nova" | "confirmacao" | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setCampoErro(null);
    if (nova.length < 10) {
      setCampoErro("nova"); setErro("A senha precisa ter pelo menos 10 caracteres."); campoNova.current?.focus(); return;
    }
    if (nova !== confirmacao) {
      setCampoErro("confirmacao"); setErro("As senhas não conferem."); campoConfirmacao.current?.focus(); return;
    }
    setEnviando(true);
    try {
      await apiFetch("/api/v1/auth/senha", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ senha_atual: atual, nova_senha: nova }) });
      onChanged?.();
      onOpenChange?.(false);
    } catch (falha) {
      const mensagem = falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível trocar a senha.";
      const senhaAtualIncorreta = /senha atual/i.test(mensagem);
      setCampoErro(senhaAtualIncorreta ? "atual" : "nova");
      setErro(mensagem);
      (senhaAtualIncorreta ? campoAtual : campoNova).current?.focus();
    } finally {
      setEnviando(false);
    }
  }

  const erroCampo = (campo: typeof campoErro) => campoErro === campo ? erro : null;
  return (
    <Dialog open={open} onOpenChange={(aberto) => !enviando && onOpenChange?.(aberto)}>
      <DialogContent>
        <DialogHeader><DialogTitle>Trocar senha</DialogTitle><DialogDescription>A sessão atual continuará aberta; as outras serão encerradas.</DialogDescription></DialogHeader>
        <form onSubmit={enviar} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5"><Label htmlFor="senha-atual">Senha atual</Label><Input ref={campoAtual} id="senha-atual" type="password" autoComplete="current-password" value={atual} onChange={(e) => setAtual(e.target.value)} aria-invalid={campoErro === "atual" ? "true" : undefined} />{erroCampo("atual") ? <p role="alert" className="text-sm text-destructive">{erroCampo("atual")}</p> : null}</div>
          <div className="flex flex-col gap-1.5"><Label htmlFor="troca-nova">Nova senha</Label><Input ref={campoNova} id="troca-nova" type="password" autoComplete="new-password" value={nova} onChange={(e) => setNova(e.target.value)} aria-invalid={campoErro === "nova" ? "true" : undefined} />{erroCampo("nova") ? <p role="alert" className="text-sm text-destructive">{erroCampo("nova")}</p> : null}</div>
          <div className="flex flex-col gap-1.5"><Label htmlFor="troca-confirmacao">Confirmar nova senha</Label><Input ref={campoConfirmacao} id="troca-confirmacao" type="password" autoComplete="new-password" value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} aria-invalid={campoErro === "confirmacao" ? "true" : undefined} />{erroCampo("confirmacao") ? <p role="alert" className="text-sm text-destructive">{erroCampo("confirmacao")}</p> : null}</div>
          <DialogFooter><Button type="button" variant="outline" onClick={() => onOpenChange?.(false)} disabled={enviando}>Cancelar</Button><Button type="submit" disabled={enviando}>{enviando ? "Trocando…" : "Trocar senha"}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
