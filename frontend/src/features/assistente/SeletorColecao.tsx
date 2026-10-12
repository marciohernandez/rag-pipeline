"use client";

import { useEffect, useState } from "react";

import { Label } from "@/components/ui/label";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiJson } from "@/lib/api-client";

/**
 * Escolha opcional de uma Coleção do projeto para o assistente analisar
 * (SPEC-0021, US-004 / FR-007; SPEC-0030, FR-013). Lê `/api/v1/colecoes` pelo cliente
 * HTTP único; se a leitura falhar, a lista fica só com "Nenhuma" e o chat segue funcionando.
 */

const NENHUMA = "__nenhuma__";

interface ColecaoDoProjeto {
  id: string;
  nome: string;
  workspace_nome?: string;
}

interface SeletorColecaoProps {
  value: string | null;
  onChange: (colecaoId: string | null) => void;
  disabled?: boolean;
}

export default function SeletorColecao({ value, onChange, disabled }: SeletorColecaoProps) {
  const [colecoes, setColecoes] = useState<ColecaoDoProjeto[]>([]);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let ativo = true;
    apiJson<ColecaoDoProjeto[]>("/api/v1/colecoes")
      .then((lista) => {
        if (ativo && Array.isArray(lista)) setColecoes(lista);
      })
      .catch(() => {
        // Sem a lista, o assistente continua útil para perguntas gerais.
      })
      .finally(() => { if (ativo) setCarregando(false); });
    return () => {
      ativo = false;
    };
  }, []);

  const itens = [
    { value: NENHUMA, label: "Nenhuma" },
    ...colecoes.map((colecao) => ({
      value: colecao.id,
      label: colecao.workspace_nome ? `${colecao.workspace_nome} · ${colecao.nome}` : colecao.nome,
    })),
  ];

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <Label htmlFor="assistente-colecao">Coleção (opcional)</Label>
      <Select
        items={itens}
        value={value ?? NENHUMA}
        onValueChange={(escolhida) => onChange(escolhida === NENHUMA ? null : String(escolhida))}
        disabled={disabled}
      >
        <SelectTrigger id="assistente-colecao" className="w-full min-w-0">
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
      {carregando ? <IndicadorProcessamento className="text-xs">Carregando coleções…</IndicadorProcessamento> : null}
      <p className="hidden text-xs text-muted-foreground sm:block">
        O assistente analisa o conteúdo da coleção antes de recomendar.
      </p>
    </div>
  );
}
