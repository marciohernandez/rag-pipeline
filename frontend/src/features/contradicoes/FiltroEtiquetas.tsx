"use client";

import { Button } from "@/components/ui/button";
import {
  ETIQUETAS,
  type Etiqueta,
  rotuloEtiqueta,
} from "@/features/contradicoes/situacaoContradicao";

interface FiltroEtiquetasProps {
  valor: Etiqueta | null;
  onChange: (valor: Etiqueta | null) => void;
}

/** Grupo de botões de alternância para filtrar o relatório por etiqueta (SPEC-0038, FR-007). */
export default function FiltroEtiquetas({ valor, onChange }: FiltroEtiquetasProps) {
  return (
    <div role="group" aria-label="Filtrar por etiqueta" className="flex flex-wrap gap-2">
      <Button
        type="button"
        size="sm"
        variant={valor === null ? "default" : "outline"}
        aria-pressed={valor === null}
        onClick={() => onChange(null)}
      >
        Todas
      </Button>
      {ETIQUETAS.map((etiqueta) => (
        <Button
          key={etiqueta}
          type="button"
          size="sm"
          variant={valor === etiqueta ? "default" : "outline"}
          aria-pressed={valor === etiqueta}
          onClick={() => onChange(valor === etiqueta ? null : etiqueta)}
        >
          {rotuloEtiqueta(etiqueta)}
        </Button>
      ))}
    </div>
  );
}
