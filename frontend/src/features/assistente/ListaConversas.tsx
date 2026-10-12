import { Trash2Icon } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";

import type { ConversaResumo } from "./useAssistente";

/**
 * Histórico de conversas da pessoa (SPEC-0021, US-002). Lista simples, não uma
 * grade de registros: cada linha abre a conversa por mouse e teclado e tem uma
 * ação independente de apagar (a confirmação fica em `ApagarConversaDialog`).
 */

function dataCurta(iso: string): string {
  const data = new Date(iso);
  return Number.isNaN(data.getTime())
    ? ""
    : data.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

interface ListaConversasProps {
  conversas: ConversaResumo[];
  carregando: boolean;
  erro: string | null;
  onAbrir: (id: string) => void;
  onApagar: (conversa: ConversaResumo) => void;
  onTentarNovamente: () => void;
}

export default function ListaConversas({
  conversas,
  carregando,
  erro,
  onAbrir,
  onApagar,
  onTentarNovamente,
}: ListaConversasProps) {
  if (carregando) {
    return (
      <div className="flex flex-col gap-2 px-4 py-2">
        <IndicadorProcessamento>Carregando conversas</IndicadorProcessamento>
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }
  if (erro) {
    return (
      <div className="px-4 py-2">
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={onTentarNovamente}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }
  if (conversas.length === 0) {
    return (
      <p className="px-4 py-4 text-sm text-muted-foreground">
        Você ainda não tem conversas. Comece uma nova para tirar dúvidas sobre RAG.
      </p>
    );
  }
  return (
    <ul className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-4 pb-2">
      {conversas.map((conversa) => (
        <li key={conversa.id} className="flex min-w-0 items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            className="h-auto min-w-0 flex-1 flex-col items-start gap-0 whitespace-normal py-2 text-left"
            onClick={() => onAbrir(conversa.id)}
          >
            <span className="w-full [overflow-wrap:anywhere] font-medium">{conversa.titulo}</span>
            <span className="text-xs font-normal text-muted-foreground">
              {dataCurta(conversa.atualizada_em)}
            </span>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={`Apagar conversa de ${dataCurta(conversa.atualizada_em)}`}
            title="Apagar conversa"
            onClick={() => onApagar(conversa)}
          >
            <Trash2Icon />
          </Button>
        </li>
      ))}
    </ul>
  );
}
