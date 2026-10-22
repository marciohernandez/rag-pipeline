import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Props {
  resolvidas: number;
  novas: number;
  abertas: number;
}
type Modulo = { default: ComponentType<Props> };

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca", {
    id: "p1", nome: "Pessoa de teste", email: "owner@exemplo.com", papel: "owner",
    tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ResumoRodada", () => {
  it("anuncia em role=status as contagens de resolvidas, novas e abertas", async () => {
    // SPECSFY: SPEC-0039 US-004 FR-006 NFR-004 AC-017
    const { default: Resumo } = await exigir<Modulo>("@/features/decisoes/ResumoRodada");
    render(<Resumo resolvidas={2} novas={1} abertas={3} />);

    const aviso = screen.getByRole("status");
    expect(aviso).toHaveTextContent("2 resolvidas");
    expect(aviso).toHaveTextContent("1 nova");
    expect(aviso).toHaveTextContent("3 abertas");
  });

  it("mantém a mesma região viva quando os números mudam", async () => {
    // SPECSFY: SPEC-0039 US-004 FR-006 NFR-004 AC-017
    const { default: Resumo } = await exigir<Modulo>("@/features/decisoes/ResumoRodada");
    const { rerender } = render(<Resumo resolvidas={0} novas={0} abertas={1} />);
    const antes = screen.getByRole("status");

    rerender(<Resumo resolvidas={1} novas={0} abertas={0} />);

    expect(screen.getByRole("status")).toBe(antes);
    expect(antes).toHaveTextContent("1 resolvida");
    expect(antes).toHaveAttribute("aria-live", "polite");
  });

  it("quebra o texto longo sem rolagem horizontal", async () => {
    // SPECSFY: SPEC-0039 US-004 FR-006 NFR-004 AC-017
    const { default: Resumo } = await exigir<Modulo>("@/features/decisoes/ResumoRodada");
    render(<Resumo resolvidas={10} novas={20} abertas={30} />);

    expect(screen.getByRole("status").className).toMatch(/min-w-0|break-words|wrap-anywhere/);
  });
});
