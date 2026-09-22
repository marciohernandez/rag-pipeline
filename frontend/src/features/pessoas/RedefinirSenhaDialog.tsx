"use client";

import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";

interface Props { open: boolean; pessoa: { id: string; nome: string }; onOpenChange?: (aberto: boolean) => void; onDone?: () => void; }
export default function RedefinirSenhaDialog({ open, pessoa, onOpenChange, onDone }: Props) {
  const campo = useRef<HTMLInputElement>(null); const [senha, setSenha] = useState(""); const [erro, setErro] = useState<string | null>(null); const [enviando, setEnviando] = useState(false);
  async function enviar(e: FormEvent) { e.preventDefault(); if (senha.length < 10) { setErro("A senha precisa ter pelo menos 10 caracteres."); campo.current?.focus(); return; } setEnviando(true); try { await apiFetch(`/api/v1/pessoas/${pessoa.id}/redefinir-senha`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ senha_temporaria: senha }) }); onDone?.(); onOpenChange?.(false); } catch (falha) { setErro(falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível redefinir a senha."); campo.current?.focus(); } finally { setEnviando(false); } }
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Redefinir senha</DialogTitle><DialogDescription>Defina uma senha temporária para <strong>{pessoa.nome}</strong>. As sessões terminam e a nova entrada exigirá uma nova troca.</DialogDescription></DialogHeader><form onSubmit={enviar} className="flex flex-col gap-4"><div className="flex flex-col gap-1.5"><Label htmlFor="senha-temporaria">Senha temporária</Label><Input ref={campo} id="senha-temporaria" type="password" autoComplete="new-password" value={senha} onChange={(e) => setSenha(e.target.value)} aria-invalid={erro ? "true" : undefined} />{erro ? <p role="alert" className="text-sm text-destructive">{erro}</p> : null}</div><DialogFooter><Button type="button" variant="outline" onClick={() => onOpenChange?.(false)}>Cancelar</Button><Button type="submit" disabled={enviando}>{enviando ? "Redefinindo…" : "Redefinir senha"}</Button></DialogFooter></form></DialogContent></Dialog>;
}
