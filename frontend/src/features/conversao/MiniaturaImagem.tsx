"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

interface MiniaturaImagemProps {
  loteId: string;
  documentoId: string;
  nome: string;
}

/**
 * Miniatura de uma imagem do lote (SPEC-0040). A rota exige o token da sessão, que uma tag
 * `<img src>` não envia; por isso a imagem é buscada com `apiFetch` e exibida por uma URL local.
 * Enquanto carrega, ou se falhar, fica o espaço reservado e o texto alternativo (nome do arquivo).
 */
export default function MiniaturaImagem({ loteId, documentoId, nome }: MiniaturaImagemProps) {
  const [origem, setOrigem] = useState<string | undefined>(undefined);

  useEffect(() => {
    let ativo = true;
    let url: string | undefined;
    apiFetch(
      `/api/v1/conversoes/${encodeURIComponent(loteId)}/documentos/${encodeURIComponent(documentoId)}/miniatura`,
    )
      .then((resposta) => resposta.blob())
      .then((blob) => {
        if (!ativo || typeof URL.createObjectURL !== "function") return;
        url = URL.createObjectURL(blob);
        setOrigem(url);
      })
      .catch(() => undefined);
    return () => {
      ativo = false;
      if (url && typeof URL.revokeObjectURL === "function") URL.revokeObjectURL(url);
    };
  }, [loteId, documentoId]);

  return (
    // eslint-disable-next-line @next/next/no-img-element -- imagem local (blob) da API autenticada
    <img
      src={origem}
      alt={nome}
      aria-busy={origem === undefined}
      className="h-16 w-16 shrink-0 rounded-md border bg-muted object-cover"
    />
  );
}
