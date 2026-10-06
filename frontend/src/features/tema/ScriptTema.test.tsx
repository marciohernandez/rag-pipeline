import type { ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { exigir } from "@/test/carregar";
import {
  executarScript,
  extrairScript,
  instalarMatchMedia,
  limparAmbienteTema,
} from "@/test/tema";

type Modulo = { default: ComponentType };

const html = () => document.documentElement;

async function scriptRenderizado(): Promise<string> {
  const { default: ScriptTema } = await exigir<Modulo>("@/features/tema/ScriptTema");
  const codigo = extrairScript(renderToStaticMarkup(<ScriptTema />));
  expect(codigo, "ScriptTema não renderizou um <script> em linha").not.toBeNull();
  return codigo as string;
}

beforeEach(() => {
  html().classList.remove("dark");
});

afterEach(limparAmbienteTema);

describe("ScriptTema", () => {
  it("test_script_aplica_escuro_salvo_antes_da_hidratacao", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 NFR-001 AC-006
    instalarMatchMedia(false);
    localStorage.setItem("rag-pipeline-tema", "escuro");

    executarScript(await scriptRenderizado());

    expect(html()).toHaveClass("dark");
  });

  it("test_script_claro_salvo_vence_o_computador_escuro", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 NFR-001 AC-006
    instalarMatchMedia(true);
    localStorage.setItem("rag-pipeline-tema", "claro");

    executarScript(await scriptRenderizado());

    expect(html()).not.toHaveClass("dark");
  });

  it("test_script_com_sistema_escuro_aplica_a_classe_sem_preferencia_salva", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-003 FR-004 FR-005 NFR-001 AC-007
    instalarMatchMedia(true);

    executarScript(await scriptRenderizado());

    expect(html()).toHaveClass("dark");
  });

  it("test_script_com_valor_invalido_ou_armazenamento_bloqueado_segue_o_computador", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-004 FR-005 NFR-001 AC-007
    instalarMatchMedia(true);
    localStorage.setItem("rag-pipeline-tema", "azul");
    const codigo = await scriptRenderizado();

    expect(() => executarScript(codigo)).not.toThrow();
    expect(html()).toHaveClass("dark");

    html().classList.remove("dark");
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get() {
        throw new DOMException("bloqueado", "SecurityError");
      },
    });
    try {
      expect(() => executarScript(codigo)).not.toThrow();
      expect(html()).toHaveClass("dark");
    } finally {
      // @ts-expect-error restaura o acessor original do jsdom
      delete window.localStorage;
    }
  });

  it("test_script_sem_matchmedia_deixa_o_tema_claro", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-003 FR-005 NFR-001 AC-007
    const codigo = await scriptRenderizado();
    // `matchMedia` não existe no jsdom: o script não pode lançar nem escurecer a página.
    expect(() => executarScript(codigo)).not.toThrow();
    expect(html()).not.toHaveClass("dark");
  });
});
