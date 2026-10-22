import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Proposta {
  id: string;
  arquivo: string;
  trecho_alvo: string;
  texto_corrigido: string;
  motivo: string | null;
  situacao: string;
}
interface Props {
  proposta: Proposta;
  onDecidir: (acao: "aceitar" | "editar" | "manter", textoCorrigido?: string) => void;
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

const LONGO = "textosemespacosmuitolongo".repeat(8);
const proposta: Proposta = {
  id: "p1",
  arquivo: "marketing.md",
  trecho_alvo: "O cancelamento pode ser feito em até 15 dias. " + LONGO,
  texto_corrigido: "O cancelamento pode ser feito em até 7 dias.",
  motivo: "Não foi possível localizar o trecho; indique qual corrigir",
  situacao: "incerta",
};

describe("PropostaIncerta", () => {
  it("empilha os controles no celular e quebra texto longo sem rolagem horizontal", async () => {
    // SPECSFY: SPEC-0039 US-002 NFR-004 AC-022
    const { default: Incerta } = await exigir<Modulo>("@/features/decisoes/PropostaIncerta");
    render(<Incerta proposta={proposta} onDecidir={vi.fn()} />);

    const acoes = screen.getByTestId("acoes-proposta");
    expect(acoes.className).toMatch(/flex-col/);
    expect(acoes.className).toMatch(/sm:flex-row/);
    expect(screen.getByText(new RegExp(LONGO)).className).toMatch(/break-words|wrap-anywhere|break-all/);
    expect(screen.getByText(proposta.motivo as string)).toBeInTheDocument();
    expect(acoes.className).not.toMatch(/overflow-x-(auto|scroll)/);
  });

  it("decide por teclado: Aceitar, Manter sem decisão e Editar com o texto alterado", async () => {
    // SPECSFY: SPEC-0039 US-002 NFR-004 AC-022
    const { default: Incerta } = await exigir<Modulo>("@/features/decisoes/PropostaIncerta");
    const onDecidir = vi.fn();
    const user = userEvent.setup();
    render(<Incerta proposta={proposta} onDecidir={onDecidir} />);

    screen.getByRole("button", { name: "Aceitar" }).focus();
    await user.keyboard("{Enter}");
    expect(onDecidir).toHaveBeenLastCalledWith("aceitar", undefined);

    await user.click(screen.getByRole("button", { name: "Manter sem decisão" }));
    expect(onDecidir).toHaveBeenLastCalledWith("manter", undefined);

    await user.click(screen.getByRole("button", { name: "Editar" }));
    const campo = screen.getByLabelText("Texto da correção");
    await user.clear(campo);
    await user.type(campo, "Prazo de 8 dias.");
    await user.click(screen.getByRole("button", { name: /aceitar edição/i }));
    expect(onDecidir).toHaveBeenLastCalledWith("editar", "Prazo de 8 dias.");
  });

  it("mostra o arquivo de origem e o texto proposto sem alterar nada antes da decisão", async () => {
    // SPECSFY: SPEC-0039 US-002 NFR-004 AC-022
    const { default: Incerta } = await exigir<Modulo>("@/features/decisoes/PropostaIncerta");
    const onDecidir = vi.fn();
    render(<Incerta proposta={proposta} onDecidir={onDecidir} />);

    expect(screen.getByText("marketing.md")).toBeInTheDocument();
    expect(screen.getByText(proposta.texto_corrigido)).toBeInTheDocument();
    expect(onDecidir).not.toHaveBeenCalled();
  });
});
