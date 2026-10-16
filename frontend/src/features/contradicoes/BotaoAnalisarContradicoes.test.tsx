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
  onIniciada?: (analiseId: string) => void;
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

describe("BotaoAnalisarContradicoes", () => {
  it("avisa o envio à IA e só inicia depois da confirmação", async () => {
    // SPECSFY: SPEC-0038 US-001 FR-001 NFR-001 AC-006
    const { default: Botao } = await exigir<Modulo>("@/features/contradicoes/BotaoAnalisarContradicoes");
    const chamadas = simularFetch({
      "POST .*/api/v1/colecoes/c1/contradicoes/analises$": () => json({ id: "a1", situacao: "em_andamento" }, 202),
    });
    const onIniciada = vi.fn();
    const user = userEvent.setup();
    render(<Botao colecaoId="c1" provedor="openrouter" onIniciada={onIniciada} />);

    await user.click(screen.getByRole("button", { name: "Analisar contradições" }));

    const dialogo = screen.getByRole("dialog");
    expect(dialogo).toHaveTextContent(/enviado à IA configurada/i);
    expect(dialogo).toHaveTextContent("openrouter");
    expect(chamadas.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(0);

    await user.click(screen.getByRole("button", { name: /confirmar e analisar/i }));

    const posts = chamadas.mock.calls.filter(([, init]) => init?.method === "POST");
    expect(posts).toHaveLength(1);
    expect(JSON.parse(String(posts[0][1]?.body))).toEqual({ confirmado: true });
    expect(onIniciada).toHaveBeenCalledWith("a1");
  });

  it("cancelar fecha o aviso sem iniciar a análise", async () => {
    // SPECSFY: SPEC-0038 US-001 FR-001 NFR-001 AC-006
    const { default: Botao } = await exigir<Modulo>("@/features/contradicoes/BotaoAnalisarContradicoes");
    const chamadas = simularFetch({});
    const user = userEvent.setup();
    render(<Botao colecaoId="c1" provedor="openrouter" />);

    await user.click(screen.getByRole("button", { name: "Analisar contradições" }));
    await user.click(screen.getByRole("button", { name: /cancelar/i }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(chamadas.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(0);
  });

  it("mostra o estado de carregamento enquanto o pedido está em curso", async () => {
    // SPECSFY: SPEC-0038 US-005 NFR-004 AC-022
    const { default: Botao } = await exigir<Modulo>("@/features/contradicoes/BotaoAnalisarContradicoes");
    let liberar: (r: Response) => void = () => {};
    simularFetch({
      "POST .*/contradicoes/analises$": () => new Promise<Response>((r) => { liberar = r; }) as unknown as Response,
    });
    const user = userEvent.setup();
    render(<Botao colecaoId="c1" provedor="openrouter" />);

    await user.click(screen.getByRole("button", { name: "Analisar contradições" }));
    await user.click(screen.getByRole("button", { name: /confirmar e analisar/i }));

    expect(screen.getByRole("button", { name: /confirmar e analisar|analisando/i })).toHaveAttribute(
      "aria-busy", "true",
    );
    liberar(json({ id: "a1", situacao: "em_andamento" }, 202));
  });
});
