import { Alert, AlertDescription } from "@/components/ui/alert";
import { plural } from "@/features/decisoes/tipos";

interface ResumoRodadaProps {
  resolvidas: number;
  novas: number;
  abertas: number;
}

/**
 * Resumo da rodada de correção (SPEC-0039, FR-006 / NFR-004): uma única região
 * `role="status"` anuncia quantas contradições foram resolvidas, apareceram de novo e
 * continuam abertas. O elemento é o mesmo entre as atualizações.
 */
export default function ResumoRodada({ resolvidas, novas, abertas }: ResumoRodadaProps) {
  return (
    <Alert role="status" aria-live="polite" className="min-w-0 [overflow-wrap:anywhere]">
      <AlertDescription>
        Rodada concluída: {plural(resolvidas, "resolvida", "resolvidas")},{" "}
        {plural(novas, "nova", "novas")} e {plural(abertas, "aberta", "abertas")}.
      </AlertDescription>
    </Alert>
  );
}
