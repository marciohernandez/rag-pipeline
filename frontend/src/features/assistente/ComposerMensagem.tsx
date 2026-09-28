"use client";

import { useState, type KeyboardEvent } from "react";
import { SendIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import SeletorBase from "./SeletorBase";

/**
 * Rodapé do painel: Base opcional, campo de mensagem e Enviar (SPEC-0021, FR-003).
 *
 * Aceita de 1 a 4000 caracteres; o contador aparece a partir de 3500. Enter
 * envia, Shift+Enter quebra linha. O texto só é limpo pelo chamador quando o
 * envio dá certo, então uma falha preserva o que foi digitado.
 */

export const LIMITE = 4000;
const AVISO_A_PARTIR_DE = 3500;

interface ComposerMensagemProps {
  value: string;
  onChange: (texto: string) => void;
  onEnviar: (baseId: string | null) => void;
  enviando: boolean;
}

export default function ComposerMensagem({ value, onChange, onEnviar, enviando }: ComposerMensagemProps) {
  const [baseId, setBaseId] = useState<string | null>(null);
  const tamanho = value.length;
  const invalida = value.trim() === "" || tamanho > LIMITE;

  function enviar() {
    if (!invalida && !enviando) onEnviar(baseId);
  }

  function aoTeclar(evento: KeyboardEvent<HTMLTextAreaElement>) {
    if (evento.key === "Enter" && !evento.shiftKey && !evento.nativeEvent.isComposing) {
      evento.preventDefault();
      enviar();
    }
  }

  return (
    <form
      className="flex flex-col gap-2 border-t px-4 py-3 sm:gap-3"
      onSubmit={(evento) => {
        evento.preventDefault();
        enviar();
      }}
    >
      <SeletorBase value={baseId} onChange={setBaseId} disabled={enviando} />
      <div className="flex flex-col gap-1">
        <Label htmlFor="assistente-mensagem">Mensagem</Label>
        <Textarea
          id="assistente-mensagem"
          value={value}
          onChange={(evento) => onChange(evento.target.value)}
          onKeyDown={aoTeclar}
          rows={2}
          aria-invalid={tamanho > LIMITE}
          aria-describedby="assistente-mensagem-ajuda"
          placeholder="Pergunte sobre RAG ou sobre o processamento dos documentos"
          className="max-h-40 min-h-14 resize-none"
        />
        <div id="assistente-mensagem-ajuda" className="flex justify-between gap-2 text-xs text-muted-foreground">
          <span className="hidden sm:inline">Enter envia; Shift+Enter quebra a linha.</span>
          {tamanho >= AVISO_A_PARTIR_DE ? (
            <span className={tamanho > LIMITE ? "text-destructive" : undefined}>
              {tamanho}/{LIMITE}
            </span>
          ) : null}
        </div>
      </div>
      <Button type="submit" disabled={invalida || enviando} className="self-end">
        <SendIcon data-icon="inline-start" />
        Enviar
      </Button>
    </form>
  );
}
