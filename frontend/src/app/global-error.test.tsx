import { Children, type ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { executarScript, extrairScript, instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

import GlobalError from "@/app/global-error";

type WithChildren = {
  children: ReactElement<WithChildren> | ReactElement<WithChildren>[];
};

afterEach(limparAmbienteTema);

describe("GlobalError", () => {
  it("oferece recuperação segura sem expor o erro interno", () => {
    const reset = vi.fn();
    const error = new Error("segredo interno");
    const markup = renderToStaticMarkup(<GlobalError error={error} reset={reset} />);
    const view = GlobalError({ error, reset });
    const body = Children.toArray(view.props.children).find(
      (filho) => (filho as ReactElement).type === "body",
    ) as ReactElement<WithChildren>;
    const main = body.props.children as ReactElement<WithChildren>;
    const button = (main.props.children as unknown as ReactElement<{ onClick: () => void }>[]) [1];

    expect(markup).toContain("Não foi possível abrir esta tela");
    expect(markup).toContain("Tentar novamente");
    expect(markup).not.toContain("segredo interno");
    button.props.onClick();
    expect(reset).toHaveBeenCalledOnce();
  });

  it("test_erro_global_inclui_o_script_de_tema", () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 FR-006 AC-009
    instalarMatchMedia(false);
    localStorage.setItem("rag-pipeline-tema", "escuro");
    const markup = renderToStaticMarkup(<GlobalError error={new Error("x")} reset={vi.fn()} />);

    const head = /<head[^>]*>([\s\S]*?)<\/head>/.exec(markup);
    expect(head, "a tela de erro global não emite <head>").not.toBeNull();
    const codigo = extrairScript(head![1]);
    expect(codigo, "a tela de erro global não emite o script de tema").not.toBeNull();

    executarScript(codigo as string);
    expect(document.documentElement).toHaveClass("dark");
    expect(markup).toContain("Tentar novamente");
  });

  it("test_erro_global_aceita_a_mudanca_de_classe_do_tema_no_html", () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 FR-006 AC-009
    const view = GlobalError({ error: new Error("x"), reset: vi.fn() }) as ReactElement<{
      suppressHydrationWarning?: boolean;
    }>;

    expect(view.props.suppressHydrationWarning).toBe(true);
  });

  it("test_erro_global_nao_exibe_controle_de_tema", () => {
    // SPECSFY: SPEC-0024 US-002 FR-006 AC-009
    const markup = renderToStaticMarkup(<GlobalError error={new Error("x")} reset={vi.fn()} />);

    expect(markup).not.toMatch(/menuitemradio|role="radio"|>Tema</);
    expect(markup).toContain("<script");
  });
});
