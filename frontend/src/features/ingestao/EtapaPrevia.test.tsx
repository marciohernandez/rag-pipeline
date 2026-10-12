import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import EtapaPrevia from "@/features/ingestao/EtapaPrevia";
import type { Previa } from "@/features/ingestao/useFluxoIngestao";

const longo = "palavra ".repeat(60).trim();
const previa: Previa = {
  resumo: { documentos: 2, chunks: 25, tamanho_medio: 420 },
  avisos: ["Estes arquivos têm configuração própria no frontmatter e ignoram o formulário: qa.md."],
  arquivos_com_configuracao_propria: ["qa.md"],
  pagina: 1,
  total: 25,
  chunks: [
    { documento: "a.md", posicao: 0, tamanho: 12, texto: "Texto curto." },
    { documento: "a.md", posicao: 1, tamanho: longo.length, texto: longo },
  ],
};
const props = { calculando: false, erro: null, documento: null, documentos: ["a.md", "b.md"] };

afterEach(cleanup);

describe("EtapaPrevia", () => {
  it("mostra resumo, aviso e a lista somente leitura com texto truncado e ver mais", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-005 FR-014 NFR-003 NFR-004 AC-015 AC-017
    const user = userEvent.setup();
    render(<EtapaPrevia {...props} previa={previa} onCalcular={vi.fn()} />);

    expect(screen.getByText("Documentos").nextSibling).toHaveTextContent("2");
    expect(screen.getByText("Chunks").nextSibling).toHaveTextContent("25");
    expect(screen.getByText(/configuração própria no frontmatter/i)).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(/25 chunks em 2 documentos/i);
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    const botao = screen.getByRole("button", { name: /ver mais/i });
    expect(screen.queryByText(longo)).not.toBeInTheDocument();
    await user.click(botao);
    expect(screen.getByText(longo)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ver menos/i })).toHaveAttribute("aria-expanded", "true");
  });

  it("pagina e filtra por documento chamando o cálculo", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-005 FR-014 NFR-003 NFR-004 AC-015 AC-017
    const onCalcular = vi.fn();
    const user = userEvent.setup();
    render(<EtapaPrevia {...props} previa={previa} onCalcular={onCalcular} />);

    expect(screen.getByText("Página 1 de 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /página anterior/i })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /página seguinte/i }));
    expect(onCalcular).toHaveBeenCalledWith(2, null);
    await user.selectOptions(screen.getByLabelText(/filtrar por documento/i), "b.md");
    expect(onCalcular).toHaveBeenCalledWith(1, "b.md");
  });

  it("calcula ao entrar, mostra o carregamento e a falha com Tentar novamente", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-005 FR-014 NFR-003 NFR-004 AC-015 AC-017
    const onCalcular = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(<EtapaPrevia {...props} previa={null} onCalcular={onCalcular} />);

    expect(onCalcular).toHaveBeenCalledWith(1, null);
    expect(screen.getByText(/calculando a prévia/i)).toBeInTheDocument();

    rerender(<EtapaPrevia {...props} previa={null} erro="Não foi possível dividir os arquivos." onCalcular={onCalcular} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/não foi possível dividir/i);
    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));
    expect(onCalcular).toHaveBeenLastCalledWith(1, null);
  });
});

describe("EtapaPrevia — chunks por página (SPEC-0029)", () => {
  it("troca a quantidade de chunks por página", () => {
    // SPECSFY: SPEC-0029 US-004 FR-007 FR-008 AC-017
    const muitos: Previa = {
      ...previa,
      total: 120,
      resumo: { documentos: 2, chunks: 120, tamanho_medio: 100 },
      chunks: Array.from({ length: 50 }, (_, i) => ({ documento: "a.md", posicao: i, tamanho: 10, texto: `Chunk ${i}` })),
    };
    const extra = { tamanhoPagina: 50 } as Record<string, unknown>;

    render(<EtapaPrevia {...props} {...extra} previa={muitos} onCalcular={vi.fn()} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(50);
    expect(screen.getByText(/página 1 de 3/i)).toBeInTheDocument();
  });
});
