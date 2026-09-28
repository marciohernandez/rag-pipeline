import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { exigir } from "@/test/carregar";
import { saveSession } from "@/lib/session";
import { simularApi } from "./_apoio";

type Launcher = typeof import("./AssistenteLauncher");

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("AssistentePainel — teclado e foco", () => {
  it("test_painel_abre_e_fecha_por_teclado_e_devolve_o_foco", async () => {
    // SPECSFY: SPEC-0021 US-001 NFR-003 AC-025
    const { default: AssistenteLauncher } = await exigir<Launcher>("@/features/assistente/AssistenteLauncher");
    simularApi();
    const user = userEvent.setup();
    render(<AssistenteLauncher />);
    const botao = await screen.findByRole("button", { name: /abrir assistente/i });

    botao.focus();
    await user.keyboard("{Enter}");
    const painel = await screen.findByRole("dialog", { name: /assistente/i });
    await waitFor(() => expect(painel.contains(document.activeElement)).toBe(true));

    // O Base UI prende o foco com sentinelas `span[data-type]` que, no navegador,
    // devolvem o foco ao painel; o jsdom não executa esse redirecionamento. O que
    // não pode acontecer é o foco chegar à tela de fundo, marcada como inerte.
    for (let i = 0; i < 12; i += 1) {
      await user.tab();
      const ativo = document.activeElement as HTMLElement;
      const sentinela = ativo.matches("span[data-type]");
      expect(painel.contains(ativo) || sentinela, `Tab ${i + 1} saiu do painel`).toBe(true);
      if (sentinela) break;
      expect(ativo.closest("[data-base-ui-inert]"), `Tab ${i + 1} alcançou a tela de fundo`).toBeNull();
      expect(ativo).not.toBe(botao);
    }

    const axe = (await import("axe-core")).default;
    const resultado = await axe.run(painel, {
      rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
    });
    expect(resultado.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);

    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog", { name: /assistente/i })).toBeNull());
    expect(botao).toHaveFocus();
  });
});
