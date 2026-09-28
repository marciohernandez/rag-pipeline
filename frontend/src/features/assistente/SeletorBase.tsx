"use client";

import { useEffect, useState } from "react";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiJson } from "@/lib/api-client";

/**
 * Escolha opcional de uma Base do escopo para o assistente analisar
 * (SPEC-0021, US-004 / FR-007). Lê `/api/v1/bases` pelo cliente HTTP único; se a
 * leitura falhar, a lista fica só com "Nenhuma" e o chat segue funcionando.
 */

const NENHUMA = "__nenhuma__";

interface BaseResumo {
  id: string;
  nome: string;
}

interface SeletorBaseProps {
  value: string | null;
  onChange: (baseId: string | null) => void;
  disabled?: boolean;
}

export default function SeletorBase({ value, onChange, disabled }: SeletorBaseProps) {
  const [bases, setBases] = useState<BaseResumo[]>([]);

  useEffect(() => {
    let ativo = true;
    apiJson<BaseResumo[]>("/api/v1/bases")
      .then((lista) => {
        if (ativo && Array.isArray(lista)) setBases(lista);
      })
      .catch(() => {
        // Sem a lista, o assistente continua útil para perguntas gerais.
      });
    return () => {
      ativo = false;
    };
  }, []);

  const itens = [
    { value: NENHUMA, label: "Nenhuma" },
    ...bases.map((base) => ({ value: base.id, label: base.nome })),
  ];

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <Label htmlFor="assistente-base">Base (opcional)</Label>
      <Select
        items={itens}
        value={value ?? NENHUMA}
        onValueChange={(escolhida) => onChange(escolhida === NENHUMA ? null : String(escolhida))}
        disabled={disabled}
      >
        <SelectTrigger id="assistente-base" className="w-full min-w-0">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {itens.map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {item.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="hidden text-xs text-muted-foreground sm:block">
        O assistente analisa o conteúdo da Base antes de recomendar.
      </p>
    </div>
  );
}
