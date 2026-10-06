import { ETAPAS, type EtapaId } from "@/features/ingestao/useFluxoIngestao";

interface Props {
  etapa: EtapaId;
  /** Índice da etapa mais avançada já alcançada; as seguintes ficam desabilitadas. */
  maisAlta: number;
  onIr: (etapa: EtapaId) => void;
}

/** Indicador navegável das quatro etapas; só se volta ou se salta até onde já se chegou. */
export default function BarraEtapas({ etapa, maisAlta, onIr }: Props) {
  return (
    <nav aria-label="Etapas">
      <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {ETAPAS.map((item, indice) => {
          const atual = item.id === etapa;
          const alcancavel = indice <= maisAlta;
          return (
            <li key={item.id}>
              <button
                type="button"
                aria-current={atual ? "step" : undefined}
                disabled={!alcancavel}
                onClick={() => onIr(item.id)}
                className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 ${atual ? "border-primary bg-muted font-medium text-foreground" : "text-muted-foreground hover:bg-muted/40"}`}
              >
                <span className="flex size-5 shrink-0 items-center justify-center rounded-full border text-xs">{indice + 1}</span>
                <span className="min-w-0 [overflow-wrap:anywhere]">{item.titulo}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
