"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { SituacaoAnalise } from "@/features/contradicoes/situacaoContradicao";

interface AvisoAnaliseProps {
  situacao: SituacaoAnalise;
  concluidos: number;
  total: number;
  motivo?: string | null;
  podeContinuar: boolean;
  onContinuar?: () => void;
}

/**
 * Aviso de andamento da análise de contradições (SPEC-0038, FR-005 / FR-007).
 *
 * Uma única região `role="status"` anuncia o progresso, a conclusão e a análise incompleta;
 * o elemento é o mesmo entre as mudanças para que a tecnologia assistiva leia a atualização.
 */
export default function AvisoAnalise({
  situacao,
  concluidos,
  total,
  motivo,
  podeContinuar,
  onContinuar,
}: AvisoAnaliseProps) {
  let texto: string;
  if (situacao === "incompleta") {
    texto = `Análise incompleta (${concluidos} de ${total} assuntos)`;
  } else if (situacao === "concluida") {
    texto = `Análise concluída (${concluidos} de ${total} assuntos)`;
  } else {
    texto =
      total > 0
        ? `Analisando contradições… ${concluidos} de ${total} assuntos`
        : "Analisando contradições… lendo os documentos";
  }
  return (
    <Alert
      role="status"
      aria-live="polite"
      aria-busy={situacao === "em_andamento"}
      className="min-w-0 [overflow-wrap:anywhere]"
    >
      <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
        <span>
          {texto}
          {situacao === "incompleta" && motivo ? `. ${motivo}.` : null}
        </span>
        {situacao === "incompleta" && podeContinuar ? (
          <Button type="button" size="sm" onClick={onContinuar}>
            Continuar análise
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}
