export type PreferenciaTema = "claro" | "escuro" | "sistema";
export type Tema = "claro" | "escuro";

export const CHAVE_TEMA = "rag-pipeline-tema";
export const CONSULTA_TEMA = "(prefers-color-scheme: dark)";

export function normalizarPreferencia(valor: unknown): PreferenciaTema {
  return valor === "claro" || valor === "escuro" ? valor : "sistema";
}

export function resolverTema(preferencia: PreferenciaTema, computadorEscuro: boolean): Tema {
  return preferencia === "sistema" ? (computadorEscuro ? "escuro" : "claro") : preferencia;
}

export function aplicarTema(tema: Tema): void {
  document.documentElement.classList.toggle("dark", tema === "escuro");
  document.documentElement.style.colorScheme = tema === "escuro" ? "dark" : "light";
}

export function lerPreferencia(): PreferenciaTema {
  try {
    return normalizarPreferencia(localStorage.getItem(CHAVE_TEMA));
  } catch {
    return "sistema";
  }
}

export function gravarPreferencia(preferencia: PreferenciaTema): void {
  try {
    localStorage.setItem(CHAVE_TEMA, preferencia);
  } catch {
    // Navegadores com armazenamento bloqueado mantêm a escolha apenas na sessão.
  }
}

/** Código constante, sem entrada externa, executado antes da primeira pintura. */
export function scriptTema(): string {
  return `(function(){var p;try{p=localStorage.getItem("${CHAVE_TEMA}")}catch(e){}var d=p==="escuro"||(p!=="claro"&&typeof matchMedia==="function"&&matchMedia("${CONSULTA_TEMA}").matches);var h=document.documentElement;h.classList.toggle("dark",d);h.style.colorScheme=d?"dark":"light"})()`;
}
