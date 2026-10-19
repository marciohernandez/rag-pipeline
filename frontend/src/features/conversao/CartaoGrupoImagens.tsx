"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface ImagemDoGrupo {
  documento_id: string;
  nome_arquivo: string;
  posicao: number;
}

export interface GrupoProposto {
  id: string;
  ordem: number;
  certeza: "total" | "incerta";
  aprovado: boolean;
  imagens: ImagemDoGrupo[];
}

interface CartaoGrupoImagensProps {
  loteId: string;
  grupo: GrupoProposto;
  outrosGrupos: { id: string; ordem: number }[];
  somenteLeitura?: boolean;
  onMover: (documentoId: string, grupoDestinoId: string) => void;
  onReordenar: (documentoId: string, direcao: "subir" | "descer") => void;
}

/**
 * Um grupo de imagens da proposta (SPEC-0040, FR-002 / NFR-004): miniaturas numeradas na ordem
 * sugerida, "Mover para outro grupo" e reordenar por botões, tudo operável por teclado. Cada
 * mudança é anunciada em `role="status"` e o foco permanece no controle usado.
 */
export default function CartaoGrupoImagens({
  loteId,
  grupo,
  outrosGrupos,
  somenteLeitura,
  onMover,
  onReordenar,
}: CartaoGrupoImagensProps) {
  const [anuncio, setAnuncio] = useState("");
  const total = grupo.imagens.length;

  function reordenar(indice: number, direcao: "subir" | "descer") {
    const imagem = grupo.imagens[indice];
    const posicao = direcao === "subir" ? indice : indice + 2;
    onReordenar(imagem.documento_id, direcao);
    setAnuncio(`${imagem.nome_arquivo} movida para a posição ${posicao}.`);
  }

  function mover(indice: number, destinoId: string) {
    if (!destinoId) return;
    const imagem = grupo.imagens[indice];
    const destino = outrosGrupos.find((outro) => outro.id === destinoId);
    onMover(imagem.documento_id, destinoId);
    setAnuncio(`${imagem.nome_arquivo} movida para o Grupo ${destino?.ordem ?? ""}.`);
  }

  return (
    <article
      role="group"
      aria-label={`Grupo ${grupo.ordem}`}
      className="flex min-w-0 flex-col gap-3 rounded-lg border bg-card p-4"
    >
      <header className="flex flex-wrap items-center gap-2">
        <h3 className="text-base font-medium">Grupo {grupo.ordem}</h3>
        <Badge variant={grupo.certeza === "total" ? "secondary" : "outline"}>
          {grupo.certeza === "total" ? "Certeza total" : "Confira este grupo"}
        </Badge>
        {grupo.aprovado && grupo.certeza === "total" ? (
          <Badge variant="default">Pré-aprovado</Badge>
        ) : null}
      </header>
      <ol className="flex min-w-0 flex-col gap-2">
        {grupo.imagens.map((imagem, indice) => (
          <li
            key={imagem.documento_id}
            className="flex min-w-0 flex-col gap-2 rounded-md border p-2 sm:flex-row sm:items-center"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- miniatura autenticada da API */}
            <img
              src={`/api/v1/conversoes/${encodeURIComponent(loteId)}/documentos/${encodeURIComponent(imagem.documento_id)}/miniatura`}
              alt={imagem.nome_arquivo}
              loading="lazy"
              className="h-16 w-16 shrink-0 rounded-md border object-cover"
            />
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="text-xs text-muted-foreground">Imagem {indice + 1}</span>
              <span className="min-w-0 break-words text-sm font-medium [overflow-wrap:anywhere]">
                {imagem.nome_arquivo}
              </span>
            </div>
            {somenteLeitura ? null : (
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  aria-label={`Subir ${imagem.nome_arquivo}`}
                  disabled={indice === 0}
                  onClick={() => reordenar(indice, "subir")}
                >
                  Subir
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  aria-label={`Descer ${imagem.nome_arquivo}`}
                  disabled={indice === total - 1}
                  onClick={() => reordenar(indice, "descer")}
                >
                  Descer
                </Button>
                {outrosGrupos.length > 0 ? (
                  <select
                    aria-label={`Mover ${imagem.nome_arquivo} para outro grupo`}
                    value=""
                    onChange={(evento) => mover(indice, evento.target.value)}
                    className="h-8 min-w-0 rounded-lg border border-input bg-transparent px-2 text-sm"
                  >
                    <option value="" disabled>
                      Mover para…
                    </option>
                    {outrosGrupos.map((outro) => (
                      <option key={outro.id} value={outro.id}>
                        Grupo {outro.ordem}
                      </option>
                    ))}
                  </select>
                ) : null}
              </div>
            )}
          </li>
        ))}
      </ol>
      {anuncio ? (
        <p role="status" aria-live="polite" className="sr-only">
          {anuncio}
        </p>
      ) : null}
    </article>
  );
}
