"use client";

import { useState } from "react";
import type { ChangeEvent } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MAX_ARQUIVOS, validarArquivos } from "@/lib/ingestao";

interface Props {
  arquivos: File[];
  usarPreparada: boolean;
  onAdicionar: (arquivos: File[]) => void;
  onRemover: (nome: string) => void;
  onPreparada: (usar: boolean) => void;
  /** Origem lote (SPEC-0043): documentos do lote marcados no painel, lidos pelo servidor. */
  lote?: { documentos: { id: string; nome: string }[]; erro: string | null; onRemover: (id: string) => void };
}

function tamanhoLegivel(bytes: number) {
  return bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`;
}

/**
 * Etapa Arquivos (SPEC-0026): seleção de `.md` ou uso da base preparada. Os
 * limites do backend são checados aqui antes de qualquer chamada; os arquivos
 * ficam só em memória do navegador.
 */
export default function EtapaArquivos({ arquivos, usarPreparada, onAdicionar, onRemover, onPreparada, lote }: Props) {
  const [erro, setErro] = useState<string | null>(null);

  function selecionar(evento: ChangeEvent<HTMLInputElement>) {
    const novos = Array.from(evento.target.files ?? []);
    evento.target.value = "";
    if (novos.length === 0) return;
    const problema = validarArquivos(arquivos, novos);
    setErro(problema);
    if (!problema) onAdicionar(novos);
  }

  if (lote) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">
          Os documentos abaixo vêm do lote de conversão e são lidos direto do sistema; nenhum arquivo passa pelo navegador.
        </p>
        {lote.erro ? (
          <Alert variant="destructive">
            <AlertDescription>{lote.erro}</AlertDescription>
          </Alert>
        ) : null}
        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-medium">Documentos do lote ({lote.documentos.length})</h3>
          {lote.documentos.length === 0 && !lote.erro ? (
            <p className="text-sm text-muted-foreground" role="status">Carregando os documentos do lote…</p>
          ) : (
            <ul className="flex flex-col overflow-hidden rounded-lg border text-sm">
              {lote.documentos.map((documento) => (
                <li key={documento.id} className="flex items-center justify-between gap-3 border-b px-3 py-2 last:border-b-0">
                  <span className="min-w-0 [overflow-wrap:anywhere]">{documento.nome}</span>
                  <Button type="button" variant="ghost" size="xs" aria-label={`Remover ${documento.nome}`} onClick={() => lote.onRemover(documento.id)}>
                    Remover
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <label className="flex w-fit items-center gap-2 text-sm">
        <input
          type="checkbox"
          className="size-4 accent-primary"
          checked={usarPreparada}
          onChange={(e) => onPreparada(e.target.checked)}
        />
        Usar base preparada
      </label>
      {usarPreparada ? (
        <p className="text-sm text-muted-foreground">
          A base preparada de demonstração será usada; nenhum arquivo precisa ser enviado.
        </p>
      ) : (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="ingestao-arquivos">Arquivos Markdown (.md)</Label>
          <Input id="ingestao-arquivos" type="file" accept=".md" multiple onChange={selecionar} />
          <p className="text-xs text-muted-foreground">
            Até {MAX_ARQUIVOS} arquivos, 5 MB cada e 50 MB no total.
          </p>
        </div>
      )}
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      {arquivos.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-medium">Selecionados ({arquivos.length})</h3>
          <ul className="flex flex-col overflow-hidden rounded-lg border text-sm">
            {arquivos.map((arquivo) => (
              <li key={arquivo.name} className="flex items-center justify-between gap-3 border-b px-3 py-2 last:border-b-0">
                <span className="min-w-0 [overflow-wrap:anywhere]">
                  {arquivo.name} <span className="text-xs text-muted-foreground">{tamanhoLegivel(arquivo.size)}</span>
                </span>
                <Button type="button" variant="ghost" size="xs" aria-label={`Remover ${arquivo.name}`} onClick={() => onRemover(arquivo.name)}>
                  Remover
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
