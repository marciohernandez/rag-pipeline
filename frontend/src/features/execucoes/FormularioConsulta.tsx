"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import ChunksFontes, { type ChunkFonte } from "@/features/execucoes/ChunksFontes";
import { apiJson } from "@/lib/api-client";

/**
 * Consulta à base indexada (SPEC-0013, US-004 / FR-008).
 *
 * Envia a pergunta a `POST /api/v1/bases/{id}/query` e mostra o resultado com
 * os chunks-fontes (AC-012). Em falha, exibe uma mensagem segura, sem detalhe
 * de provedor, e preserva a pergunta digitada (AC-013). O resultado e o
 * carregamento vivem numa região `role="status"` para anúncio assistivo
 * (AC-018).
 */

interface RespostaConsulta {
  resultado: string;
  chunks_fontes: ChunkFonte[];
  criado_por?: { id: string; nome: string; desativada: boolean } | null;
}

export default function FormularioConsulta({ baseId }: { baseId: string }) {
  const [pergunta, setPergunta] = useState("");
  const [resposta, setResposta] = useState<RespostaConsulta | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [consultando, setConsultando] = useState(false);

  async function consultar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setConsultando(true);
    try {
      const dados = await apiJson<RespostaConsulta>(
        `/api/v1/bases/${baseId}/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pergunta }),
        },
      );
      setResposta(dados);
    } catch {
      setResposta(null);
      setErro(
        "Não foi possível consultar a base agora. Tente novamente em instantes.",
      );
    } finally {
      setConsultando(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <form onSubmit={consultar} className="flex flex-col gap-2">
        <Label htmlFor="pergunta">Pergunta</Label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            id="pergunta"
            name="pergunta"
            value={pergunta}
            onChange={(evento) => setPergunta(evento.target.value)}
            placeholder="O que você quer verificar nesta base?"
          />
          <Button
            type="submit"
            disabled={consultando || pergunta.trim() === ""}
          >
            {consultando ? "Consultando…" : "Consultar"}
          </Button>
        </div>
      </form>

      <div role="status" aria-live="polite" className="flex flex-col gap-3">
        {consultando ? (
          <p className="text-sm text-muted-foreground">Consultando a base…</p>
        ) : null}
        {resposta ? (
          <>
            <p className="text-sm">{resposta.resultado}</p>
            <p className="text-xs text-muted-foreground">Consultada por {resposta.criado_por ? `${resposta.criado_por.nome}${resposta.criado_por.desativada ? " (desativada)" : ""}` : "Autor não identificado"}</p>
            <ChunksFontes chunks={resposta.chunks_fontes} />
          </>
        ) : null}
      </div>

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
    </section>
  );
}
