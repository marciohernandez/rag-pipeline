import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { exigir } from "@/test/carregar";

interface Ocorrencia {
  id: string;
  assunto: string;
  etiqueta: "conflito" | "versao_desatualizada" | "duplicado";
  impacto: "alto" | "baixo";
  trechos: { arquivo: string; texto: string; imagem?: string | null }[];
  explicacao: string;
  arquivo_mais_antigo?: string | null;
}
type Modulo = { default: ComponentType<{ ocorrencia: Ocorrencia }> };

const PALAVRA_LONGA = "cancelamentocancelamentocancelamentocancelamentocancelamentocancelamento";
const ocorrencia: Ocorrencia = {
  id: "o1",
  assunto: "prazo de cancelamento",
  etiqueta: "conflito",
  impacto: "alto",
  trechos: [
    { arquivo: "comercial.md", texto: `Cancelamento em 7 dias ${PALAVRA_LONGA}` },
    { arquivo: "marketing.md", texto: "Cancelamento em 15 dias." },
  ],
  explicacao: "Os prazos divergem.",
};

afterEach(cleanup);

describe("CartaoOcorrencia", () => {
  it("mostra assunto, etiqueta, os dois trechos com o arquivo de origem e a explicação", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-007 NFR-004 AC-021
    const { default: Cartao } = await exigir<Modulo>("@/features/contradicoes/CartaoOcorrencia");
    render(<Cartao ocorrencia={ocorrencia} />);

    expect(screen.getByRole("heading", { level: 3 })).toHaveTextContent("prazo de cancelamento");
    expect(screen.getByText("Conflito")).toBeInTheDocument();
    expect(screen.getByText("comercial.md")).toBeInTheDocument();
    expect(screen.getByText("marketing.md")).toBeInTheDocument();
    expect(screen.getByText("Os prazos divergem.")).toBeInTheDocument();
  });

  it("empilha os trechos no celular e quebra palavras longas sem rolagem horizontal", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-007 NFR-004 AC-021
    const { default: Cartao } = await exigir<Modulo>("@/features/contradicoes/CartaoOcorrencia");
    render(<Cartao ocorrencia={ocorrencia} />);

    const grade = screen.getByTestId("trechos-lado-a-lado");
    expect(grade.className).toMatch(/grid-cols-1/);
    expect(grade.className).toMatch(/md:grid-cols-2/);
    const longo = screen.getByText(new RegExp(PALAVRA_LONGA));
    expect(longo.className).toMatch(/break-words|wrap-anywhere|break-all/);
    expect(grade.className).not.toMatch(/overflow-x-(auto|scroll)/);
  });

  it("não cria armadilha de teclado: nenhum controle focável além dos links de origem", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-007 NFR-004 AC-021
    const { default: Cartao } = await exigir<Modulo>("@/features/contradicoes/CartaoOcorrencia");
    const user = userEvent.setup();
    render(<Cartao ocorrencia={{ ...ocorrencia, arquivo_mais_antigo: "comercial.md" }} />);

    await user.tab();
    await user.tab();
    await user.tab();
    expect(document.body.contains(document.activeElement)).toBe(true);
    expect(screen.getByText(/mais antigo/i)).toBeInTheDocument();
  });
});
