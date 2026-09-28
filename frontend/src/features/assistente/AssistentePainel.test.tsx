import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { exigir } from "@/test/carregar";
import { saveSession } from "@/lib/session";
import { conversaAntiga, mensagem, simularApi } from "./_apoio";

type Painel = typeof import("./AssistentePainel");

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("AssistentePainel", () => {
  it("test_nova_conversa_e_retomada_do_historico_mantem_as_mensagens", async () => {
    // SPECSFY: SPEC-0021 US-002 FR-001 FR-002 FR-003 AC-006
    const { default: AssistentePainel } = await exigir<Painel>("@/features/assistente/AssistentePainel");
    simularApi({
      "c-antiga": {
        ...conversaAntiga,
        mensagens: [
          mensagem("pessoa", "Pergunta antiga sobre overlap"),
          mensagem("assistente", "Resposta antiga sobre overlap"),
        ],
      },
    });
    const user = userEvent.setup();
    render(<AssistentePainel open onOpenChange={vi.fn()} />);
    const painel = await screen.findByRole("dialog", { name: /assistente/i });

    await user.click(within(painel).getByRole("button", { name: /nova conversa/i }));
    await user.type(within(painel).getByRole("textbox", { name: /mensagem/i }), "Qual splitter usar?");
    await user.click(within(painel).getByRole("button", { name: /^enviar$/i }));
    expect(await within(painel).findByText("Resposta nova do assistente")).toBeInTheDocument();
    expect(within(painel).getByText("docs/architecture.md")).toBeInTheDocument();

    await user.click(within(painel).getByRole("button", { name: /hist[oó]rico/i }));
    expect(await within(painel).findByRole("button", { name: /qual splitter usar/i })).toBeInTheDocument();
    await user.click(await within(painel).findByRole("button", { name: /conversa antiga/i }));

    expect(await within(painel).findByText("Pergunta antiga sobre overlap")).toBeInTheDocument();
    expect(within(painel).getByText("Resposta antiga sobre overlap")).toBeInTheDocument();
  });

  it("test_painel_em_viewport_estreito_e_mensagens_longas_sem_overflow_horizontal", async () => {
    // SPECSFY: SPEC-0021 US-001 NFR-003 AC-027
    const { default: AssistentePainel } = await exigir<Painel>("@/features/assistente/AssistentePainel");
    const longa = `Veja o exemplo:\n\`\`\`\n${"linha_de_codigo_muito_longa_".repeat(20)}\n\`\`\``;
    simularApi({
      "c-antiga": { ...conversaAntiga, mensagens: [mensagem("assistente", longa)] },
    });
    window.innerWidth = 375;
    window.dispatchEvent(new Event("resize"));
    const user = userEvent.setup();
    render(<AssistentePainel open onOpenChange={vi.fn()} />);
    const painel = await screen.findByRole("dialog", { name: /assistente/i });

    await user.click(within(painel).getByRole("button", { name: /hist[oó]rico/i }));
    await user.click(await within(painel).findByRole("button", { name: /conversa antiga/i }));

    const lista = await within(painel).findByRole("log");
    await waitFor(() => expect(lista.textContent).toContain("linha_de_codigo_muito_longa_"));
    expect(painel.className).toMatch(/(^|\s)w-full(\s|$)/);
    expect(lista.className).toMatch(/overflow-y-auto/);
    const bloco = lista.querySelector("pre");
    expect(bloco, "bloco de código renderizado em <pre>").not.toBeNull();
    expect(bloco!.className).toMatch(/overflow-x-auto/);
    const todos = [painel, ...Array.from(painel.querySelectorAll("*"))];
    expect(todos.some((el) => /overflow-x-(scroll|visible)/.test(el.className.toString()))).toBe(false);
  });
});
