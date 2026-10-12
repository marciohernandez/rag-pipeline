/**
 * Apoio dos testes da SPEC-0024 (tema escuro).
 *
 * O jsdom não implementa `matchMedia`; `instalarMatchMedia` simula a
 * preferência de tema do computador e permite mudá-la com o sistema aberto.
 */
import { vi } from "vitest";

export type ComputadorSimulado = {
  /** Muda o tema do computador e avisa quem ouve `prefers-color-scheme`. */
  definirEscuro: (escuro: boolean) => void;
};

export function instalarMatchMedia(escuroInicial: boolean): ComputadorSimulado {
  let escuro = escuroInicial;
  const ouvintes = new Set<(evento: { matches: boolean }) => void>();

  vi.stubGlobal(
    "matchMedia",
    vi.fn((consulta: string) => ({
      get matches() {
        return consulta.includes("dark") ? escuro : false;
      },
      media: consulta,
      onchange: null,
      addEventListener: (_: string, ouvinte: (evento: { matches: boolean }) => void) => {
        ouvintes.add(ouvinte);
      },
      removeEventListener: (_: string, ouvinte: (evento: { matches: boolean }) => void) => {
        ouvintes.delete(ouvinte);
      },
      addListener: (ouvinte: (evento: { matches: boolean }) => void) => {
        ouvintes.add(ouvinte);
      },
      removeListener: (ouvinte: (evento: { matches: boolean }) => void) => {
        ouvintes.delete(ouvinte);
      },
      dispatchEvent: () => true,
    })),
  );

  return {
    definirEscuro(valor: boolean) {
      escuro = valor;
      ouvintes.forEach((ouvinte) => ouvinte({ matches: valor }));
    },
  };
}

export function limparAmbienteTema() {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  document.documentElement.classList.remove("dark");
  document.documentElement.style.removeProperty("color-scheme");
  try {
    localStorage.clear();
  } catch {
    // O armazenamento pode ter sido bloqueado pelo próprio teste.
  }
}

/** Extrai o texto do primeiro `<script>` do HTML renderizado. */
export function extrairScript(html: string): string | null {
  const achado = /<script[^>]*>([\s\S]*?)<\/script>/.exec(html);
  return achado ? achado[1] : null;
}

/** Executa o script em linha como o navegador faria antes da hidratação. */
export function executarScript(codigo: string) {
  new Function(codigo)();
}
