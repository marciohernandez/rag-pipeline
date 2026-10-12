"use client";

import { useEffect, useState } from "react";
import { HistoryIcon, MessageSquarePlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";

import ApagarConversaDialog from "./ApagarConversaDialog";
import ComposerMensagem from "./ComposerMensagem";
import ListaConversas from "./ListaConversas";
import ListaMensagens from "./ListaMensagens";
import { useAssistente, type ConversaResumo } from "./useAssistente";

/**
 * Painel lateral do assistente (SPEC-0021). Camada sobre a tela atual: alterna
 * entre a conversa e o histórico, inicia nova conversa e apaga com confirmação.
 * Foco preso, Esc e devolução do foco ao botão vêm do `Sheet` modal.
 */

interface AssistentePainelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSessaoEncerrada?: () => void;
}

export default function AssistentePainel({ open, onOpenChange, onSessaoEncerrada }: AssistentePainelProps) {
  const assistente = useAssistente({ onSessaoEncerrada });
  const [visao, setVisao] = useState<"conversa" | "historico">("conversa");
  const [texto, setTexto] = useState("");
  const [alvoDaExclusao, setAlvoDaExclusao] = useState<ConversaResumo | null>(null);
  const [apagando, setApagando] = useState(false);
  const { carregarHistorico } = assistente;

  useEffect(() => {
    if (open && visao === "historico") void carregarHistorico();
  }, [open, visao, carregarHistorico]);

  async function enviar(colecaoId: string | null) {
    if (await assistente.enviar(texto, colecaoId)) setTexto("");
  }

  async function abrir(id: string) {
    setVisao("conversa");
    await assistente.abrirConversa(id);
  }

  async function confirmarExclusao() {
    if (!alvoDaExclusao) return;
    setApagando(true);
    if (await assistente.apagar(alvoDaExclusao.id)) setAlvoDaExclusao(null);
    setApagando(false);
  }

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent
          side="right"
          className="w-full gap-2 data-[side=right]:w-full data-[side=right]:sm:max-w-md"
        >
          <SheetHeader className="gap-2 pr-12">
            <SheetTitle>Assistente de RAG</SheetTitle>
            <SheetDescription className="sr-only sm:not-sr-only">
              Orienta sobre RAG e o processamento de documentos. Não altera nada no sistema.
            </SheetDescription>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  assistente.novaConversa();
                  setTexto("");
                  setVisao("conversa");
                }}
              >
                <MessageSquarePlusIcon data-icon="inline-start" />
                Nova conversa
              </Button>
              <Button
                type="button"
                variant={visao === "historico" ? "secondary" : "outline"}
                size="sm"
                aria-pressed={visao === "historico"}
                onClick={() => setVisao(visao === "historico" ? "conversa" : "historico")}
              >
                <HistoryIcon data-icon="inline-start" />
                Histórico
              </Button>
            </div>
          </SheetHeader>

          {visao === "historico" ? (
            <ListaConversas
              conversas={assistente.conversas}
              carregando={assistente.carregandoConversas}
              erro={assistente.erroHistorico}
              onAbrir={(id) => void abrir(id)}
              onApagar={setAlvoDaExclusao}
              onTentarNovamente={() => void carregarHistorico()}
            />
          ) : assistente.carregandoMensagens ? (
            <IndicadorProcessamento className="px-4 py-2">Carregando conversa…</IndicadorProcessamento>
          ) : (
            <>
              <ListaMensagens
                mensagens={assistente.mensagens}
                carregando={assistente.enviando}
                erro={assistente.erro}
                onSugestao={setTexto}
                onTentarNovamente={() => void enviar(null)}
              />
              <ComposerMensagem
                value={texto}
                onChange={setTexto}
                onEnviar={(colecaoId) => void enviar(colecaoId)}
                enviando={assistente.enviando}
              />
            </>
          )}
        </SheetContent>
      </Sheet>
      <ApagarConversaDialog
        open={alvoDaExclusao !== null}
        titulo={alvoDaExclusao?.titulo ?? ""}
        apagando={apagando}
        erro={assistente.erroHistorico}
        onConfirmar={() => void confirmarExclusao()}
        onCancelar={() => setAlvoDaExclusao(null)}
      />
    </>
  );
}
