"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import ChunksFontes, { type ChunkFonte } from "@/features/colecoes/ChunksFontes";
import { nomeDoAutor, type Autor } from "@/features/colecoes/tipos";
import { ApiError, apiJson } from "@/lib/api-client";

/**
 * Consulta à coleção inteira (SPEC-0030, FR-013): envia a pergunta a
 * `POST /api/v1/colecoes/{id}/query` e mostra o resultado com os chunks-fontes. Em
 * falha, mostra uma mensagem segura e preserva a pergunta digitada. Carregando e
 * resultado ficam numa região `role="status"` para anúncio assistivo.
 */

interface RespostaConsulta {
  resultado: string;
  chunks_fontes: ChunkFonte[];
  criado_por?: Autor | null;
}

export default function ConsultaColecao({ colecaoId }: { colecaoId: string }) {
  const [pergunta, setPergunta] = useState("");
  const [resposta, setResposta] = useState<RespostaConsulta | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [consultando, setConsultando] = useState(false);

  async function consultar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setConsultando(true);
    try {
      setResposta(
        await apiJson<RespostaConsulta>(`/api/v1/colecoes/${encodeURIComponent(colecaoId)}/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pergunta }),
        }),
      );
    } catch (causa) {
      setResposta(null);
      setErro(
        causa instanceof ApiError && causa.status === 409 && causa.detail
          ? causa.detail
          : "Não foi possível consultar a coleção agora. Tente novamente em instantes.",
      );
    } finally {
      setConsultando(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <form onSubmit={consultar} className="flex flex-col gap-2">
        <Label htmlFor="pergunta">Pergunta</Label>
        <Textarea
          id="pergunta"
          name="pergunta"
          rows={3}
          value={pergunta}
          onChange={(evento) => setPergunta(evento.target.value)}
          placeholder="O que você quer verificar nesta coleção?"
        />
        <div>
          <Button type="submit" loading={consultando} disabled={consultando || pergunta.trim() === ""}>
            {consultando ? "Consultando…" : "Consultar"}
          </Button>
        </div>
      </form>

      <div role="status" aria-live="polite" className="flex flex-col gap-3">
        {consultando ? <p className="text-sm text-muted-foreground">Consultando a coleção…</p> : null}
        {resposta ? (
          <>
            <p className="text-sm [overflow-wrap:anywhere]">{resposta.resultado}</p>
            <p className="text-xs text-muted-foreground [overflow-wrap:anywhere]">
              Consultada por {nomeDoAutor(resposta.criado_por)}
            </p>
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
