import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import EtapaDivisao from "@/features/ingestao/EtapaDivisao";
import { PADROES_FALLBACK } from "@/lib/ingestao";

const base = {
  arquivos: [] as File[],
  padroes: PADROES_FALLBACK,
  splitter: "header",
  tamanho: "1000",
  overlap: "200",
  tentativas: 0,
  onAlterar: vi.fn(),
};

afterEach(cleanup);

describe("EtapaDivisao", () => {
  it("mostra os campos pré-preenchidos com ajuda e as estratégias disponíveis", () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    render(<EtapaDivisao {...base} />);

    expect(screen.getByLabelText("Tamanho do chunk")).toHaveValue(1000);
    expect(screen.getByLabelText("Overlap")).toHaveValue(200);
    expect(screen.getByLabelText("Estratégia de divisão")).toHaveValue("header");
    // SPEC-0029 (DEC-004) ampliou as duas estratégias da SPEC-0026 para seis.
    expect(within(screen.getByLabelText("Estratégia de divisão")).getAllByRole("option").map((o) => o.textContent)).toEqual([
      "Markdown por cabeçalhos",
      "Markdown recursivo",
      "Markdown sintático",
      "Recursivo por caracteres",
      "Por caractere",
      "Por tokens",
    ]);
    expect(screen.getByText(/de 200 a 4000/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("mostra o erro abaixo do campo e foca o primeiro inválido ao tentar avançar", () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    const { rerender } = render(<EtapaDivisao {...base} tamanho="5000" overlap="3000" />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    rerender(<EtapaDivisao {...base} tamanho="5000" overlap="3000" tentativas={1} />);

    expect(screen.getByText(/máximo de 4000/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Tamanho do chunk")).toHaveFocus();
    expect(screen.getByLabelText("Tamanho do chunk")).toHaveAttribute("aria-invalid", "true");

    rerender(<EtapaDivisao {...base} tamanho="800" overlap="600" tentativas={2} />);
    expect(screen.getByText(/até a metade do tamanho \(400\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Overlap")).toHaveFocus();
  });

  it("avisa os arquivos com configuração própria no frontmatter", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    const qa = new File(["---\nsplitter: qa\n---\nP: Um?\nR: Um."], "qa.md");
    const comum = new File(["# Comum\n\nTexto."], "comum.md");
    const user = userEvent.setup();
    render(<EtapaDivisao {...base} arquivos={[qa, comum]} />);

    expect(await screen.findByText(/configuração própria no frontmatter/i)).toHaveTextContent("qa.md");
    expect(screen.getByText(/configuração própria no frontmatter/i)).not.toHaveTextContent("comum.md");
    await user.selectOptions(screen.getByLabelText("Estratégia de divisão"), "recursive");
    expect(base.onAlterar).toHaveBeenCalledWith("splitter", "recursive");
  });
});

describe("EtapaDivisao — estratégias e campos próprios (SPEC-0029)", () => {
  async function renderizar(splitter: string, extra: Record<string, unknown> = {}) {
    const lib = (await import("@/lib/ingestao")) as Record<string, unknown>;
    const props = {
      ...base,
      splitter,
      padroes: (lib.PADROES_FALLBACK ?? PADROES_FALLBACK) as typeof PADROES_FALLBACK,
      processamento: lib.PROCESSAMENTO_PADRAO,
      onAlterarProcessamento: vi.fn(),
      ...extra,
    };
    return { ...render(<EtapaDivisao {...(props as typeof base)} />), props };
  }

  it("mostra só os campos da estratégia escolhida", async () => {
    // SPECSFY: SPEC-0029 US-001 FR-002 FR-011 NFR-003 AC-003
    const { rerender, props } = await renderizar("character_split");
    expect(screen.getAllByRole("option", { hidden: true }).map((o) => o.textContent)).toEqual(
      expect.arrayContaining([
        "Markdown por cabeçalhos",
        "Markdown recursivo",
        "Markdown sintático",
        "Recursivo por caracteres",
        "Por caractere",
        "Por tokens",
      ]),
    );
    expect(screen.getByLabelText("Separador")).toBeInTheDocument();
    expect(screen.getByLabelText("Tamanho do chunk")).toBeInTheDocument();

    rerender(<EtapaDivisao {...(props as typeof base)} splitter="token" />);
    expect(screen.getByLabelText("Encoding")).toBeInTheDocument();
    expect(screen.getByLabelText("Tamanho do chunk (tokens)")).toBeInTheDocument();
    expect(screen.queryByLabelText("Separador")).not.toBeInTheDocument();

    rerender(<EtapaDivisao {...(props as typeof base)} splitter="markdown_syntax" />);
    expect(screen.getByLabelText("Dividir por cabeçalhos")).toBeInTheDocument();
    expect(screen.getByLabelText("Remover cabeçalhos do texto")).toBeInTheDocument();
    expect(screen.queryByLabelText(/tamanho do chunk/i)).not.toBeInTheDocument();

    rerender(<EtapaDivisao {...(props as typeof base)} splitter="markdown" />);
    const niveis = screen.getByLabelText("Dividir por cabeçalhos");
    expect(Array.from((niveis as HTMLSelectElement).options).map((o) => o.textContent)).toEqual([
      "Desativado", "Até H1", "Até H2", "Até H3", "Até H4", "Até H5", "Até H6",
    ]);
  });

  it("usa as cores de popover nas opções dos seletores", async () => {
    // SPECSFY: SPEC-0029 US-001 FR-011 NFR-003 AC-024
    await renderizar("header");

    for (const seletor of [screen.getByLabelText("Estratégia de divisão"), screen.getByLabelText("Dividir por cabeçalhos")]) {
      expect(seletor.className).toMatch(/option\]:bg-popover/);
      expect(seletor.className).toMatch(/option\]:text-popover-foreground/);
    }
  });

  it("seletores funcionam no tema claro e por teclado", async () => {
    // SPECSFY: SPEC-0029 FR-011 NFR-003 AC-025
    const user = userEvent.setup();
    const onAlterar = vi.fn();
    await renderizar("header", { onAlterar });
    const estrategia = screen.getByLabelText("Estratégia de divisão");

    estrategia.focus();
    await user.selectOptions(estrategia, "token");

    expect(estrategia).toHaveFocus();
    expect(onAlterar).toHaveBeenCalledWith("splitter", "token");
    expect(estrategia.className).toMatch(/bg-background/);
  });
});
