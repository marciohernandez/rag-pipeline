"use client";

import { useState } from "react";
import { MessageCircleIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

import AssistentePainel from "./AssistentePainel";

/**
 * Botão global do assistente (SPEC-0021, FR-001): fixo no canto inferior
 * direito, montado uma única vez no shell autenticado (nunca em Login e Nova
 * senha). Abre o painel lateral sobre a tela atual, sem trocar de rota.
 */

export default function AssistenteLauncher({ onSessaoEncerrada }: { onSessaoEncerrada?: () => void }) {
  const [aberto, setAberto] = useState(false);
  return (
    <>
      <Button
        type="button"
        size="lg"
        className="fixed right-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-40 shadow-lg"
        aria-haspopup="dialog"
        aria-label="Abrir assistente"
        onClick={() => setAberto(true)}
      >
        <MessageCircleIcon data-icon="inline-start" />
        <span className="hidden sm:inline">Assistente</span>
      </Button>
      <AssistentePainel open={aberto} onOpenChange={setAberto} onSessaoEncerrada={onSessaoEncerrada} />
    </>
  );
}
