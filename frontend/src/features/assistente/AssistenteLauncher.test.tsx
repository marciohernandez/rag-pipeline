import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigation = vi.hoisted(() => ({ pathname: "/workspaces", replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useRouter: () => ({ replace: navigation.replace }),
}));

import LayoutAutenticado from "@/app/(autenticado)/layout";
import { saveSession } from "@/lib/session";
import { simularApi } from "./_apoio";

beforeEach(() => {
  navigation.replace.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("AssistenteLauncher no shell autenticado", () => {
  it("test_launcher_aparece_nas_telas_autenticadas_e_abre_o_painel", async () => {
    // SPECSFY: SPEC-0021 US-001 FR-001 FR-009 AC-001
    for (const caminho of ["/workspaces", "/execucoes/base-1", "/pessoas"]) {
      navigation.pathname = caminho;
      simularApi();
      const user = userEvent.setup();
      const { unmount } = render(<LayoutAutenticado>Conteúdo da tela</LayoutAutenticado>);

      const botao = await screen.findByRole("button", { name: /abrir assistente/i });
      await user.click(botao);

      const painel = await screen.findByRole("dialog", { name: /assistente/i });
      expect(within(painel).getByRole("textbox", { name: /mensagem/i })).toBeInTheDocument();
      expect(screen.getByText("Conteúdo da tela")).toBeInTheDocument();
      expect(navigation.replace).not.toHaveBeenCalled();

      unmount();
      vi.restoreAllMocks();
    }
  });
});
