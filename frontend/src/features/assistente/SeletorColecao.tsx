"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
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
 * Filtro opcional por Coleção do projeto (SPEC-0021, US-004 / FR-007; SPEC-0030, FR-013;
 * SPEC-0031, FR-007). Sem filtro o copilot busca em todas as coleções ("Todas as coleções");
 * a escolha restringe a busca e "Limpar filtro" volta ao padrão. Lê `/api/v1/colecoes` pelo
 * cliente HTTP único; se a leitura falhar, a lista fica só com "Todas as coleções".
 */

const TODAS = "__todas__";

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
    { value: TODAS, label: "Todas as coleções" },
    ...colecoes.map((colecao) => ({
      value: colecao.id,
      label: colecao.workspace_nome ? `${colecao.workspace_nome} · ${colecao.nome}` : colecao.nome,
    })),
  ];

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <Label htmlFor="assistente-colecao">Filtrar por coleção (opcional)</Label>
        {value !== null ? (
          <Button type="button" variant="ghost" size="sm" onClick={() => onChange(null)} disabled={disabled}>
            Limpar filtro
          </Button>
        ) : null}
      </div>
      <Select
        items={itens}
        value={value ?? TODAS}
        onValueChange={(escolhida) => onChange(escolhida === TODAS ? null : String(escolhida))}
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
        Sem filtro, o copilot busca em todas as coleções do seu projeto.
      </p>
    </div>
  );
}
