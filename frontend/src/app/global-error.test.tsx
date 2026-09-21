import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import GlobalError from "@/app/global-error";

type WithChildren = {
  children: ReactElement<WithChildren> | ReactElement<WithChildren>[];
};

describe("GlobalError", () => {
  it("oferece recuperação segura sem expor o erro interno", () => {
    const reset = vi.fn();
    const error = new Error("segredo interno");
    const markup = renderToStaticMarkup(<GlobalError error={error} reset={reset} />);
    const view = GlobalError({ error, reset });
    const body = view.props.children as ReactElement<WithChildren>;
    const main = body.props.children as ReactElement<WithChildren>;
    const button = (main.props.children as unknown as ReactElement<{ onClick: () => void }>[]) [1];

    expect(markup).toContain("Não foi possível abrir esta tela");
    expect(markup).toContain("Tentar novamente");
    expect(markup).not.toContain("segredo interno");
    button.props.onClick();
    expect(reset).toHaveBeenCalledOnce();
  });
});
