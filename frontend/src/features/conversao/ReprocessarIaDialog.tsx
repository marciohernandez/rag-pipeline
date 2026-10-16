"use client";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import { apiJson } from "@/lib/api-client";

interface Props {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  loteId: string;
  documento: {id: string; nome_arquivo: string};
  onReprocessado: (lote: LoteConversaoResumo) => void;
}
export default function ReprocessarIaDialog({open,onOpenChange,loteId,documento,onReprocessado}:Props) {
  const [enviando,setEnviando]=useState(false);
  const [erro,setErro]=useState<string|null>(null);
  async function confirmar() {
    if(enviando)return;
    setEnviando(true);setErro(null);
    try {
      await apiJson(`/api/v1/conversoes/${loteId}/documentos/${documento.id}/reprocessar-ia`,{method:"POST"});
      onReprocessado(await apiJson<LoteConversaoResumo>(`/api/v1/conversoes/${loteId}`));
      onOpenChange?.(false);
    } catch {setErro("Não foi possível solicitar o reprocessamento; tente novamente.");}
    finally {setEnviando(false);}
  }
  return <Dialog open={open} onOpenChange={(valor)=>{if(!enviando)onOpenChange?.(valor);}}>
    <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto [overflow-wrap:anywhere]">
      <DialogHeader><DialogTitle>Reprocessar com IA</DialogTitle><DialogDescription>O conteúdo de {documento.nome_arquivo} será enviado ao provedor de IA configurado. O Markdown atual só será substituído se a leitura terminar com sucesso.</DialogDescription></DialogHeader>
      {erro && <Alert variant="destructive"><AlertDescription>{erro}</AlertDescription></Alert>}
      <DialogFooter><Button variant="outline" onClick={()=>onOpenChange?.(false)} disabled={enviando}>Cancelar</Button><Button className="h-auto min-h-8 whitespace-normal py-1" onClick={confirmar} disabled={enviando}>{enviando?"Solicitando…":"Confirmar reprocessamento"}</Button></DialogFooter>
    </DialogContent>
  </Dialog>;
}
export function AcaoReprocessarIa({loteId,documento,onReprocessado}:Omit<Props,"open"|"onOpenChange">) {
 const [aberto,setAberto]=useState(false);
 return <><Button type="button" variant="ghost" size="xs" className="h-auto min-h-6 max-w-full whitespace-normal py-1 text-left" onClick={()=>setAberto(true)}>Reprocessar com IA</Button><ReprocessarIaDialog open={aberto} onOpenChange={setAberto} loteId={loteId} documento={documento} onReprocessado={onReprocessado}/></>;
}
