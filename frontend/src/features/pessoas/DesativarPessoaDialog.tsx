"use client";

import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiFetch } from "@/lib/api-client";

interface Props { open: boolean; pessoa: { id: string; nome: string }; acao: "desativar" | "reativar"; bloqueio?: string; onOpenChange?: (aberto: boolean) => void; onDone?: () => void; }
export default function DesativarPessoaDialog({ open, pessoa, acao, bloqueio, onOpenChange, onDone }: Props) {
  const [enviando, setEnviando] = useState(false); const [erro, setErro] = useState<string | null>(null);
  async function confirmar() { setEnviando(true); setErro(null); try { await apiFetch(`/api/v1/pessoas/${pessoa.id}/${acao}`, { method: "POST" }); onDone?.(); onOpenChange?.(false); } catch { setErro(`Não foi possível ${acao} esta pessoa.`); } finally { setEnviando(false); } }
  const titulo = acao === "desativar" ? "Desativar pessoa" : "Reativar pessoa";
  return <Dialog open={open} onOpenChange={(aberto) => !enviando && onOpenChange?.(aberto)}><DialogContent><DialogHeader><DialogTitle>{titulo}</DialogTitle><DialogDescription>{acao === "desativar" ? <>Desativar <strong>{pessoa.nome}</strong>? A sessão dela termina imediatamente.</> : <>Reativar <strong>{pessoa.nome}</strong> e permitir uma nova entrada?</>}</DialogDescription></DialogHeader>{bloqueio ? <Alert><AlertDescription>{bloqueio}</AlertDescription></Alert> : null}{erro ? <Alert variant="destructive"><AlertDescription>{erro}</AlertDescription></Alert> : null}<DialogFooter><Button type="button" variant="outline" onClick={() => onOpenChange?.(false)}>Cancelar</Button><Button type="button" variant={acao === "desativar" ? "destructive" : "default"} disabled={enviando || Boolean(bloqueio)} onClick={() => void confirmar()}>{enviando ? "Salvando…" : acao === "desativar" ? "Desativar" : "Reativar"}</Button></DialogFooter></DialogContent></Dialog>;
}
