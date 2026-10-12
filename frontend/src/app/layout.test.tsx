import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { executarScript, extrairScript, instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

vi.mock("next/font/google", () => ({
  Geist: () => ({ variable: "fonte-sans" }),
  Geist_Mono: () => ({ variable: "fonte-mono" }),
}));

import RootLayout from "@/app/layout";

type Props = Parameters<typeof RootLayout>[0];

function renderizar() {
  const elemento = RootLayout({ children: <p id="conteudo">conteúdo</p> } as unknown as Props);
  return { elemento: elemento as ReactElement<{ suppressHydrationWarning?: boolean }>, html: renderToStaticMarkup(elemento) };
}

afterEach(limparAmbienteTema);

describe("RootLayout", () => {
  it("test_layout_raiz_renderiza_o_script_no_head_e_aceita_a_mudanca_de_classe", () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 FR-006 NFR-001 AC-016
    const { elemento, html } = renderizar();

    const head = /<head[^>]*>([\s\S]*?)<\/head>/.exec(html);
    expect(head, "o layout raiz não emite <head>").not.toBeNull();
    expect(head![1]).toContain("<script");
    expect(html.indexOf("<script")).toBeLessThan(html.indexOf('id="conteudo"'));
    expect(elemento.props.suppressHydrationWarning).toBe(true);
  });

  it("test_script_do_layout_raiz_tem_menos_de_1_kb_e_nao_faz_requisicao", () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 NFR-001 AC-016
    const { html } = renderizar();
    const codigo = extrairScript(html);

    expect(codigo, "o layout raiz não emite o script de tema").not.toBeNull();
    expect(new TextEncoder().encode(codigo as string).length).toBeLessThan(1024);
    expect(html).not.toMatch(/<script[^>]*\ssrc=/);
    expect(codigo).not.toMatch(/fetch|XMLHttpRequest|import\(/);
  });

  it("test_script_do_layout_raiz_aplica_o_tema_salvo_ao_html", () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 FR-006 NFR-001 AC-016
    instalarMatchMedia(false);
    localStorage.setItem("rag-pipeline-tema", "escuro");
    const codigo = extrairScript(renderizar().html);

    expect(codigo, "o layout raiz não emite o script de tema").not.toBeNull();
    executarScript(codigo as string);
    expect(document.documentElement).toHaveClass("dark");
  });
});
