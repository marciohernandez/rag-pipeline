import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { exigir } from "@/test/carregar";

interface Imagem {
  documento_id: string;
  nome_arquivo: string;
  posicao: number;
}
interface Grupo {
  id: string;
  ordem: number;
  certeza: "total" | "incerta";
  aprovado: boolean;
  imagens: Imagem[];
}
interface Props {
  loteId: string;
  grupo: Grupo;
  outrosGrupos: { id: string; ordem: number }[];
  somenteLeitura?: boolean;
  onMover: (documentoId: string, grupoDestinoId: string) => void;
  onReordenar: (documentoId: string, direcao: "subir" | "descer") => void;
}
type Modulo = { default: ComponentType<Props> };

const grupo: Grupo = {
  id: "g1",
  ordem: 1,
  certeza: "incerta",
  aprovado: false,
  imagens: [
    { documento_id: "d1", nome_arquivo: "ana-1.png", posicao: 1 },
    { documento_id: "d2", nome_arquivo: "ana-2.png", posicao: 2 },
    { documento_id: "d3", nome_arquivo: "ana-3.png", posicao: 3 },
  ],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CartaoGrupoImagens", () => {
  it("move uma imagem para outro grupo e anuncia a mudança em role=status", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 NFR-004 AC-006
    const { default: Cartao } = await exigir<Modulo>("@/features/conversao/CartaoGrupoImagens");
    const onMover = vi.fn();
    const user = userEvent.setup();
    render(
      <Cartao loteId="l1" grupo={grupo} outrosGrupos={[{ id: "g2", ordem: 2 }]} onMover={onMover} onReordenar={vi.fn()} />,
    );

    await user.selectOptions(screen.getByLabelText("Mover ana-2.png para outro grupo"), "g2");

    expect(onMover).toHaveBeenCalledWith("d2", "g2");
    expect(screen.getByRole("status")).toHaveTextContent(/ana-2\.png.*grupo 2/i);
  });

  it("reordena por teclado, anuncia a posição e mantém o foco no controle usado", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 NFR-004 AC-006
    const { default: Cartao } = await exigir<Modulo>("@/features/conversao/CartaoGrupoImagens");
    const onReordenar = vi.fn();
    const user = userEvent.setup();
    render(<Cartao loteId="l1" grupo={grupo} outrosGrupos={[]} onMover={vi.fn()} onReordenar={onReordenar} />);

    const descer = screen.getByRole("button", { name: "Descer ana-1.png" });
    descer.focus();
    await user.keyboard("{Enter}");

    expect(onReordenar).toHaveBeenCalledWith("d1", "descer");
    expect(screen.getByRole("status")).toHaveTextContent(/ana-1\.png.*posição 2/i);
    expect(descer).toHaveFocus();
  });

  it("não oferece subir a primeira nem descer a última imagem", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 NFR-004 AC-006
    const { default: Cartao } = await exigir<Modulo>("@/features/conversao/CartaoGrupoImagens");
    render(<Cartao loteId="l1" grupo={grupo} outrosGrupos={[]} onMover={vi.fn()} onReordenar={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Subir ana-1.png" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Descer ana-3.png" })).toBeDisabled();
    expect(screen.getAllByRole("img").map((i) => i.getAttribute("alt"))).toEqual([
      "ana-1.png", "ana-2.png", "ana-3.png",
    ]);
  });

  it("em modo leitura não mostra mover nem reordenar", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 NFR-004 AC-006
    const { default: Cartao } = await exigir<Modulo>("@/features/conversao/CartaoGrupoImagens");
    render(<Cartao loteId="l1" grupo={grupo} outrosGrupos={[{ id: "g2", ordem: 2 }]} somenteLeitura onMover={vi.fn()} onReordenar={vi.fn()} />);

    expect(screen.queryByRole("button", { name: /subir|descer/i })).toBeNull();
    expect(screen.queryByLabelText(/mover .* para outro grupo/i)).toBeNull();
    expect(screen.getByText("ana-2.png")).toBeInTheDocument();
  });
});
