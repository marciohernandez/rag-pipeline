import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Props {
  colecaoId: string;
  provedor: string | null;
  iaPermitida: boolean;
  onInterpretada?: () => void;
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

const posts = (chamadas: ReturnType<typeof simularFetch>) =>
  chamadas.mock.calls.filter(([, init]) => init?.method === "POST");

describe("CaixaRespostaEmpresa", () => {
  it("avisa o envio do texto à IA e só interpreta depois da confirmação", async () => {
    // SPECSFY: SPEC-0039 US-001 FR-001 NFR-001 AC-003
    const { default: Caixa } = await exigir<Modulo>("@/features/decisoes/CaixaRespostaEmpresa");
    const chamadas = simularFetch({
      "POST .*/api/v1/colecoes/c1/decisoes/respostas$": () => json({ id: "r1" }, 202),
    });
    const onInterpretada = vi.fn();
    const user = userEvent.setup();
    render(<Caixa colecaoId="c1" provedor="openrouter" iaPermitida onInterpretada={onInterpretada} />);

    await user.type(screen.getByLabelText("Resposta da empresa"), "Vale o prazo de 7 dias.");
    await user.click(screen.getByRole("button", { name: "Interpretar resposta" }));

    const dialogo = screen.getByRole("dialog");
    expect(dialogo).toHaveTextContent(/enviado à IA configurada/i);
    expect(dialogo).toHaveTextContent("openrouter");
    expect(posts(chamadas)).toHaveLength(0);

    await user.click(screen.getByRole("button", { name: /confirmar e interpretar/i }));

    expect(posts(chamadas)).toHaveLength(1);
    expect(JSON.parse(String(posts(chamadas)[0][1]?.body))).toEqual({
      texto: "Vale o prazo de 7 dias.",
      confirmado: true,
    });
    expect(onInterpretada).toHaveBeenCalled();
  });

  it("não abre o aviso com a caixa vazia e leva o foco ao campo com o erro", async () => {
    // SPECSFY: SPEC-0039 US-001 FR-001 NFR-001 AC-003
    const { default: Caixa } = await exigir<Modulo>("@/features/decisoes/CaixaRespostaEmpresa");
    const chamadas = simularFetch({});
    const user = userEvent.setup();
    render(<Caixa colecaoId="c1" provedor="openrouter" iaPermitida />);

    await user.click(screen.getByRole("button", { name: "Interpretar resposta" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("alert")).toHaveTextContent(/resposta da empresa/i);
    expect(screen.getByLabelText("Resposta da empresa")).toHaveFocus();
    expect(posts(chamadas)).toHaveLength(0);
  });

  it("com a IA externa desligada explica o motivo e não envia nada", async () => {
    // SPECSFY: SPEC-0039 US-001 FR-001 NFR-001 AC-003
    const { default: Caixa } = await exigir<Modulo>("@/features/decisoes/CaixaRespostaEmpresa");
    const chamadas = simularFetch({});
    const user = userEvent.setup();
    render(<Caixa colecaoId="c1" provedor={null} iaPermitida={false} />);

    expect(screen.getByText(/análise por IA externa/i)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Resposta da empresa"), "Vale 7 dias.");
    await user.click(screen.getByRole("button", { name: "Interpretar resposta" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(posts(chamadas)).toHaveLength(0);
  });

  it("repete o aviso a cada nova interpretação, depois de as correções serem aplicadas", async () => {
    // SPECSFY: SPEC-0039 US-004 FR-006 NFR-001 AC-018
    const { default: Caixa } = await exigir<Modulo>("@/features/decisoes/CaixaRespostaEmpresa");
    const chamadas = simularFetch({
      "POST .*/api/v1/colecoes/c1/decisoes/respostas$": () => json({ id: "r1" }, 202),
    });
    const user = userEvent.setup();
    render(<Caixa colecaoId="c1" provedor="openrouter" iaPermitida />);
    await user.type(screen.getByLabelText("Resposta da empresa"), "Vale 7 dias.");
    await user.click(screen.getByRole("button", { name: "Interpretar resposta" }));
    await user.click(screen.getByRole("button", { name: /confirmar e interpretar/i }));

    await user.click(screen.getByRole("button", { name: "Interpretar resposta" }));

    expect(screen.getByRole("dialog")).toHaveTextContent(/enviado à IA configurada/i);
    expect(posts(chamadas)).toHaveLength(1);
  });
});
