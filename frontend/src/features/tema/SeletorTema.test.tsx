import type { ComponentType } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { exigir } from "@/test/carregar";
import { instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

type Modulo = { default: ComponentType };

const html = () => document.documentElement;

async function montarMenu() {
  const { default: SeletorTema } = await exigir<Modulo>("@/features/tema/SeletorTema");
  render(
    <DropdownMenu>
      <DropdownMenuTrigger>Pessoa</DropdownMenuTrigger>
      <DropdownMenuContent>
        <SeletorTema />
      </DropdownMenuContent>
    </DropdownMenu>,
  );
  return screen.getByRole("button", { name: "Pessoa" });
}

beforeEach(() => {
  html().classList.remove("dark");
  instalarMatchMedia(false);
});

afterEach(() => {
  cleanup();
  limparAmbienteTema();
});

describe("SeletorTema", () => {
  it("test_escolher_escuro_aplica_o_tema_e_grava_a_preferencia", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-001 FR-002 NFR-003 AC-001
    const user = userEvent.setup();
    const gatilho = await montarMenu();

    await user.click(gatilho);
    await user.click(await screen.findByRole("menuitemradio", { name: "Escuro" }));

    expect(html()).toHaveClass("dark");
    expect(localStorage.getItem("rag-pipeline-tema")).toBe("escuro");
  });

  it("test_voltar_para_claro_remove_o_tema_escuro_e_grava_claro", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-001 FR-002 NFR-003 AC-001
    const user = userEvent.setup();
    localStorage.setItem("rag-pipeline-tema", "escuro");
    html().classList.add("dark");
    const gatilho = await montarMenu();

    await user.click(gatilho);
    await user.click(await screen.findByRole("menuitemradio", { name: "Claro" }));

    expect(html()).not.toHaveClass("dark");
    expect(localStorage.getItem("rag-pipeline-tema")).toBe("claro");
  });

  it("test_seletor_opera_so_pelo_teclado", async () => {
    // SPECSFY: SPEC-0024 US-003 FR-001 FR-008 NFR-003 AC-012
    const user = userEvent.setup();
    const gatilho = await montarMenu();

    gatilho.focus();
    await user.keyboard("{Enter}");
    const claro = await screen.findByRole("menuitemradio", { name: "Claro" });
    const escuro = screen.getByRole("menuitemradio", { name: "Escuro" });
    expect(claro).toHaveFocus();

    await user.keyboard("{ArrowDown}");
    expect(escuro).toHaveFocus();
    await user.keyboard("{Enter}");

    expect(html()).toHaveClass("dark");
    await waitFor(() => expect(gatilho).toHaveFocus());
  });

  it("test_esc_fecha_o_menu_sem_mudar_o_tema_e_devolve_o_foco", async () => {
    // SPECSFY: SPEC-0024 US-003 FR-001 FR-008 NFR-003 AC-012
    const user = userEvent.setup();
    const gatilho = await montarMenu();

    gatilho.focus();
    await user.keyboard("{Enter}");
    await screen.findByRole("menuitemradio", { name: "Escuro" });
    await user.keyboard("{ArrowDown}{Escape}");

    expect(screen.queryByRole("menuitemradio", { name: "Escuro" })).not.toBeInTheDocument();
    expect(html()).not.toHaveClass("dark");
    expect(localStorage.getItem("rag-pipeline-tema")).toBeNull();
    expect(gatilho).toHaveFocus();
  });
});
