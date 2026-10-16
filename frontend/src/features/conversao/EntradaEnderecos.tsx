"use client";

import { useId, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function EntradaEnderecos({ onAdicionar, disabled = false }: { onAdicionar: (url: string) => void; disabled?: boolean }) {
  const id = useId();
  const [url, setUrl] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  function adicionar() {
    try {
      const valor = new URL(url.trim());
      const host = valor.hostname.toLowerCase().replace(/^\[|\]$/g, "");
      if (!['http:', 'https:'].includes(valor.protocol) || valor.username || valor.password || valor.port || host === 'localhost' || host.endsWith('.localhost') || (host.includes(':') && (host === '::1' || host === '::' || /^(f[cd]|fe[89ab]|ff|::ffff:)/i.test(host))) || /^(0|10|127|169\.254|172\.(1[6-9]|2\d|3[01])|192\.168)(\.|$)/.test(host)) throw new Error();
      onAdicionar(valor.href);
      setUrl("");
      setErro(null);
    } catch {
      setErro("Informe um endereço público http ou https, sem credenciais ou porta especial.");
    }
  }
  return <div className="flex min-w-0 flex-col gap-2">
    <Label htmlFor={id}>Endereço da página</Label>
    <div className="flex flex-col gap-2 sm:flex-row">
      <Input id={id} inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)} disabled={disabled} aria-invalid={!!erro} aria-describedby={erro ? `${id}-erro` : undefined} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); adicionar(); } }} />
      <Button type="button" onClick={adicionar} disabled={disabled}>Adicionar</Button>
    </div>
    {erro && <Alert id={`${id}-erro`} variant="destructive"><AlertDescription>{erro}</AlertDescription></Alert>}
  </div>;
}
