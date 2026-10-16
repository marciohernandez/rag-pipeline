"use client";
import { useId, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";

export default function SelecaoAbas({ abas, onConfirmar }: { abas: string[]; onConfirmar: (abas: string[]) => void | Promise<void> }) {
  const id = useId();
  const [selecionadas, setSelecionadas] = useState(() => [...abas]);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  async function confirmar() {
    if (!selecionadas.length || enviando) return;
    setEnviando(true); setErro(null);
    try { await onConfirmar(selecionadas); }
    catch { setErro("Não foi possível confirmar as abas; tente novamente."); }
    finally { setEnviando(false); }
  }
  return <fieldset className="flex min-w-0 flex-col gap-3 rounded-md border p-3" disabled={enviando}>
    <legend className="px-1 text-sm font-medium">Abas para converter</legend>
    {abas.map((aba, i) => <div key={aba} className="flex min-w-0 items-start gap-2"><Checkbox id={`${id}-${i}`} checked={selecionadas.includes(aba)} onCheckedChange={(marcada) => setSelecionadas((atual) => marcada ? [...atual, aba] : atual.filter((a) => a !== aba))} /><Label htmlFor={`${id}-${i}`} className="min-w-0 leading-5 [overflow-wrap:anywhere]">{aba}</Label></div>)}
    {!selecionadas.length && <Alert variant="destructive"><AlertDescription>Selecione ao menos uma aba.</AlertDescription></Alert>}
    {erro && <Alert variant="destructive"><AlertDescription>{erro}</AlertDescription></Alert>}
    <Button type="button" onClick={confirmar} disabled={enviando || !selecionadas.length}>{enviando ? "Confirmando…" : "Confirmar abas"}</Button>
  </fieldset>;
}
