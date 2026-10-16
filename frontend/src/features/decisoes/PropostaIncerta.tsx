"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { AcaoDecisao, LocalManual, PropostaCorrecao } from "@/features/decisoes/tipos";

interface PropostaIncertaProps {
  proposta: PropostaCorrecao;
  onDecidir: (acao: AcaoDecisao, textoCorrigido?: string, local?: LocalManual) => void;
  ocupado?: boolean;
  somenteLeitura?: boolean;
}

/**
 * Proposta incerta ou sem decisão (SPEC-0039, FR-003): a pessoa aceita, edita o texto da
 * correção ou mantém sem decisão. Nada é gravado antes da escolha.
 */
export default function PropostaIncerta({
  proposta,
  onDecidir,
  ocupado,
  somenteLeitura,
}: PropostaIncertaProps) {
  const [editando, setEditando] = useState(false);
  const [texto, setTexto] = useState(proposta.texto_corrigido);
  const [arquivo, setArquivo] = useState(proposta.arquivo ?? "");
  const [trecho, setTrecho] = useState(proposta.trecho_alvo);
  const semTrecho = !proposta.trecho_alvo || !proposta.arquivo;
  const semDecisao = proposta.situacao === "sem_decisao";

  function aceitarEdicao() {
    if (semTrecho) onDecidir("editar", texto, { arquivo, trecho_alvo: trecho });
    else onDecidir("editar", texto);
  }

  return (
    <article className="flex min-w-0 flex-col gap-3 rounded-lg border bg-card p-4">
      <header className="flex flex-wrap items-center gap-2">
        {proposta.arquivo ? (
          <span className="min-w-0 break-words text-sm font-medium">{proposta.arquivo}</span>
        ) : null}
        <Badge variant={semDecisao ? "outline" : "secondary"}>
          {semDecisao ? "Sem decisão" : "Incerta"}
        </Badge>
      </header>
      {proposta.motivo ? (
        <p className="break-words text-sm text-muted-foreground">{proposta.motivo}</p>
      ) : null}
      {proposta.trecho_alvo ? (
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Trecho a corrigir</span>
          <blockquote className="break-words rounded-md bg-muted p-3 text-sm [overflow-wrap:anywhere]">
            {proposta.trecho_alvo}
          </blockquote>
        </div>
      ) : null}
      {proposta.texto_corrigido ? (
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Texto proposto</span>
          <p className="break-words text-sm [overflow-wrap:anywhere]">{proposta.texto_corrigido}</p>
        </div>
      ) : null}
      {somenteLeitura ? null : editando ? (
        <div className="flex min-w-0 flex-col gap-2">
          {semTrecho ? (
            <>
              <Label htmlFor={`arquivo-${proposta.id}`}>Arquivo a corrigir</Label>
              <Input
                id={`arquivo-${proposta.id}`}
                value={arquivo}
                onChange={(evento) => setArquivo(evento.target.value)}
              />
              <Label htmlFor={`trecho-${proposta.id}`}>Trecho a corrigir (copie do arquivo)</Label>
              <Textarea
                id={`trecho-${proposta.id}`}
                value={trecho}
                onChange={(evento) => setTrecho(evento.target.value)}
                rows={3}
              />
            </>
          ) : null}
          <Label htmlFor={`texto-${proposta.id}`}>Texto da correção</Label>
          <Textarea
            id={`texto-${proposta.id}`}
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            rows={4}
            className="min-w-0"
          />
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <Button type="button" variant="outline" onClick={() => setEditando(false)}>
              Cancelar edição
            </Button>
            <Button type="button" onClick={aceitarEdicao} disabled={ocupado || !texto.trim()}>
              Aceitar edição
            </Button>
          </div>
        </div>
      ) : (
        <div data-testid="acoes-proposta" className="flex min-w-0 flex-col gap-2 sm:flex-row">
          {proposta.trecho_alvo && proposta.texto_corrigido ? (
            <Button type="button" onClick={() => onDecidir("aceitar", undefined)} disabled={ocupado}>
              Aceitar
            </Button>
          ) : null}
          <Button type="button" variant="outline" onClick={() => setEditando(true)}>
            Editar
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => onDecidir("manter", undefined)}
            disabled={ocupado}
          >
            Manter sem decisão
          </Button>
        </div>
      )}
    </article>
  );
}
