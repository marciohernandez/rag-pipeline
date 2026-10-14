"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { motivoAviso, type AvisoConversao } from "@/features/conversao/situacao";

export default function SeloRevisarDocumento({ avisos }: { avisos: AvisoConversao[] }) {
  const [aberto, setAberto] = useState(false);
  if (!avisos.length) return null;
  const motivos = avisos.map(motivoAviso);

  return (
    <TooltipProvider>
      <Tooltip open={aberto} onOpenChange={setAberto}>
        <TooltipTrigger
          delay={0}
          closeOnClick={false}
          render={<Badge variant="outline" render={<button type="button" />} />}
          aria-label={`Revisar: ${motivos.join("; ")}`}
          onClick={(evento) => { evento.stopPropagation(); setAberto(true); }}
          onKeyDown={(evento) => evento.stopPropagation()}
        >
          Revisar
        </TooltipTrigger>
        <TooltipContent>
          <ul className="flex flex-col gap-1">
            {motivos.map((motivo, indice) => <li key={indice}>{motivo}</li>)}
          </ul>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
