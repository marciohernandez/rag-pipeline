"use client";

import { useLayoutEffect, useState } from "react";
import {
  aplicarTema,
  CONSULTA_TEMA,
  gravarPreferencia,
  lerPreferencia,
  resolverTema,
  type PreferenciaTema,
} from "@/lib/tema";

export function useTema() {
  const [preferencia, setPreferencia] = useState<PreferenciaTema>("sistema");

  useLayoutEffect(() => {
    // A leitura só acontece após hidratar; a primeira pintura é coberta pelo script.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPreferencia(lerPreferencia());
  }, []);

  useLayoutEffect(() => {
    const media = typeof matchMedia === "function" ? matchMedia(CONSULTA_TEMA) : undefined;
    const atualizar = () => aplicarTema(resolverTema(preferencia, media?.matches ?? false));
    atualizar();
    if (preferencia !== "sistema") return;
    media?.addEventListener("change", atualizar);
    return () => media?.removeEventListener("change", atualizar);
  }, [preferencia]);

  function escolher(proxima: PreferenciaTema) {
    gravarPreferencia(proxima);
    setPreferencia(proxima);
    aplicarTema(resolverTema(proxima, typeof matchMedia === "function" && matchMedia(CONSULTA_TEMA).matches));
  }

  return { preferencia, escolher };
}
