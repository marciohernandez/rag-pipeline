import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";

import MensagemChat from "./MensagemChat";
import type { MensagemAssistente } from "./useAssistente";

/**
 * Lista rolável das mensagens (SPEC-0021, NFR-003).
 *
 * A região `aria-live="polite"` anuncia o carregamento e cada resposta nova; o
 * erro aparece com `role="alert"`. A rolagem é vertical e fica dentro da lista.
 */

export const SUGESTOES = [
  "Text splitter ou Markdown splitter para ter um melhor RAG?",
  "Qual tamanho de chunk e overlap devo usar?",
  "Qual a melhor forma de processar os documentos que tenho?",
];

interface ListaMensagensProps {
  mensagens: MensagemAssistente[];
  carregando: boolean;
  erro: string | null;
  onSugestao?: (texto: string) => void;
  onTentarNovamente?: () => void;
}

export default function ListaMensagens({
  mensagens,
  carregando,
  erro,
  onSugestao,
  onTentarNovamente,
}: ListaMensagensProps) {
  const vazia = mensagens.length === 0 && !carregando;
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div
        role="log"
        aria-live="polite"
        aria-label="Mensagens da conversa"
        className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 pb-2"
      >
        {vazia ? (
          <div className="flex flex-col gap-3 py-4">
            <p className="text-sm text-muted-foreground">
              Pergunte sobre RAG, sobre o conteúdo dos seus documentos e sobre o que acontece no sistema.
            </p>
            {onSugestao ? (
              <ul className="flex flex-col gap-2">
                {SUGESTOES.map((sugestao) => (
                  <li key={sugestao}>
                    <Button
                      type="button"
                      variant="outline"
                      className="h-auto w-full justify-start whitespace-normal py-2 text-left"
                      onClick={() => onSugestao(sugestao)}
                    >
                      {sugestao}
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : (
          <ol className="flex min-w-0 flex-col gap-3">
            {mensagens.map((mensagem) => (
              <MensagemChat key={mensagem.id} mensagem={mensagem} />
            ))}
          </ol>
        )}
        {carregando ? (
          <div className="flex flex-col gap-2" aria-busy="true">
            <IndicadorProcessamento className="text-xs">Aguardando resposta do assistente…</IndicadorProcessamento>
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ) : null}
      </div>
      {erro ? (
        <div className="px-4">
          <Alert variant="destructive" role="alert">
            <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
              <span>{erro}</span>
              {onTentarNovamente ? (
                <Button type="button" variant="outline" size="sm" onClick={onTentarNovamente}>
                  Tentar novamente
                </Button>
              ) : null}
            </AlertDescription>
          </Alert>
        </div>
      ) : null}
    </div>
  );
}
