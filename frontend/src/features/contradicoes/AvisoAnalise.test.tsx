import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { exigir } from "@/test/carregar";

interface Props {
  situacao: "em_andamento" | "concluida" | "incompleta";
  concluidos: number;
  total: number;
  motivo?: string | null;
  podeContinuar: boolean;
  onContinuar?: () => void;
}
type Modulo = { default: ComponentType<Props> };

afterEach(cleanup);

describe("AvisoAnalise", () => {
  it("análise incompleta mostra o progresso e o motivo em role=status", async () => {
    // SPECSFY: SPEC-0038 US-003 FR-005 FR-007 NFR-004 AC-011
    const { default: Aviso } = await exigir<Modulo>("@/features/contradicoes/AvisoAnalise");
    const onContinuar = vi.fn();
    const user = userEvent.setup();
    render(
      <Aviso situacao="incompleta" concluidos={6} total={10} motivo="IA indisponível"
        podeContinuar onContinuar={onContinuar} />,
    );

    const aviso = screen.getByRole("status");
    expect(aviso).toHaveTextContent("Análise incompleta (6 de 10 assuntos)");
    expect(aviso).toHaveTextContent("IA indisponível");
    await user.click(screen.getByRole("button", { name: "Continuar análise" }));
    expect(onContinuar).toHaveBeenCalledTimes(1);
  });

  it("member vê o aviso mas não tem o botão de continuar", async () => {
    // SPECSFY: SPEC-0038 US-003 FR-005 FR-007 NFR-004 AC-011
    const { default: Aviso } = await exigir<Modulo>("@/features/contradicoes/AvisoAnalise");
    render(<Aviso situacao="incompleta" concluidos={6} total={10} motivo="IA indisponível" podeContinuar={false} />);

    expect(screen.getByRole("status")).toHaveTextContent("Análise incompleta");
    expect(screen.queryByRole("button", { name: "Continuar análise" })).toBeNull();
  });

  it("o progresso muda dentro da mesma região de status e o foco permanece no controle", async () => {
    // SPECSFY: SPEC-0038 US-005 NFR-004 AC-022
    const { default: Aviso } = await exigir<Modulo>("@/features/contradicoes/AvisoAnalise");
    const { rerender } = render(
      <Aviso situacao="em_andamento" concluidos={3} total={10} podeContinuar onContinuar={() => {}} />,
    );
    const regiao = screen.getByRole("status");
    expect(regiao).toHaveTextContent("3 de 10");
    const botao = document.createElement("button");
    document.body.appendChild(botao);
    botao.focus();

    rerender(<Aviso situacao="em_andamento" concluidos={7} total={10} podeContinuar onContinuar={() => {}} />);
    expect(screen.getByRole("status")).toBe(regiao);
    expect(regiao).toHaveTextContent("7 de 10");
    expect(document.activeElement).toBe(botao);

    rerender(<Aviso situacao="concluida" concluidos={10} total={10} podeContinuar onContinuar={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent(/concluíd/i);
    botao.remove();
  });
});
