import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import type { MensagemAssistente } from "./useAssistente";

/**
 * Uma mensagem do chat (SPEC-0021). A pessoa fica à direita e o assistente à
 * esquerda; blocos de código (```) rolam na horizontal dentro da própria bolha,
 * nunca na página; as fontes citadas aparecem como `Badge` abaixo da resposta.
 */

function partes(conteudo: string): { codigo: boolean; texto: string }[] {
  return conteudo
    .split(/```[\w-]*\n?([\s\S]*?)```/)
    .map((texto, indice) => ({ codigo: indice % 2 === 1, texto }))
    .filter((parte) => parte.texto.trim() !== "");
}

export default function MensagemChat({ mensagem }: { mensagem: MensagemAssistente }) {
  const daPessoa = mensagem.papel === "pessoa";
  return (
    <li className={cn("flex min-w-0 flex-col gap-1.5", daPessoa ? "items-end" : "items-start")}>
      <span className="sr-only">{daPessoa ? "Você" : "Assistente"}:</span>
      <div
        className={cn(
          "flex min-w-0 max-w-[92%] flex-col gap-2 rounded-lg px-3 py-2 text-sm leading-relaxed",
          daPessoa ? "bg-primary text-primary-foreground" : "bg-muted text-foreground",
        )}
      >
        {partes(mensagem.conteudo).map((parte, indice) =>
          parte.codigo ? (
            <pre
              key={indice}
              className="max-w-full overflow-x-auto rounded-md bg-background/80 p-2 font-mono text-xs leading-normal text-foreground"
            >
              <code>{parte.texto.replace(/\n$/, "")}</code>
            </pre>
          ) : (
            <p key={indice} className="whitespace-pre-wrap [overflow-wrap:anywhere]">
              {parte.texto.trim()}
            </p>
          ),
        )}
      </div>
      {mensagem.fontes.length > 0 ? (
        <ul aria-label="Fontes citadas" className="flex max-w-[92%] flex-wrap gap-1">
          {mensagem.fontes.map((fonte) => (
            <li key={fonte} className="min-w-0">
              <Badge variant="outline" className="h-auto min-h-5 max-w-full py-0.5 [overflow-wrap:anywhere] whitespace-normal">
                {fonte}
              </Badge>
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}
