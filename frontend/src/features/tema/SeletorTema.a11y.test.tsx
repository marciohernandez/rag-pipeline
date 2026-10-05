import type { ComponentType } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { exigir } from "@/test/carregar";
import { instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

type Modulo = { default: ComponentType };

async function abrirMenu(preferenciaSalva?: string) {
  if (preferenciaSalva) localStorage.setItem("rag-pipeline-tema", preferenciaSalva);
  const { default: SeletorTema } = await exigir<Modulo>("@/features/tema/SeletorTema");
  const user = userEvent.setup();
  render(
    <DropdownMenu>
      <DropdownMenuTrigger>Pessoa</DropdownMenuTrigger>
      <DropdownMenuContent>
        <SeletorTema />
      </DropdownMenuContent>
    </DropdownMenu>,
  );
  await user.click(screen.getByRole("button", { name: "Pessoa" }));
  return user;
}

beforeEach(() => {
  instalarMatchMedia(false);
});

afterEach(() => {
  cleanup();
  limparAmbienteTema();
});

describe("SeletorTema — acessibilidade", () => {
  it("test_opcoes_sao_anunciadas_com_nome_e_estado", async () => {
    // SPECSFY: SPEC-0024 US-003 FR-008 NFR-003 AC-013
    await abrirMenu();

    const grupo = await screen.findByRole("group", { name: "Tema" });
    const opcoes = within(grupo).getAllByRole("menuitemradio");
    expect(opcoes.map((opcao) => opcao.textContent)).toEqual(["Claro", "Escuro", "Sistema"]);
    expect(opcoes.map((opcao) => opcao.getAttribute("aria-checked"))).toEqual([
      "false",
      "false",
      "true",
    ]);
  });

  it("test_estado_marcado_acompanha_a_preferencia_salva", async () => {
    // SPECSFY: SPEC-0024 US-003 FR-008 NFR-003 AC-013
    await abrirMenu("escuro");

    expect(await screen.findByRole("menuitemradio", { name: "Escuro" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("menuitemradio", { name: "Claro" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
    expect(screen.getByRole("menuitemradio", { name: "Sistema" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("test_escolher_outra_opcao_move_o_estado_marcado", async () => {
    // SPECSFY: SPEC-0024 US-003 FR-008 NFR-003 AC-013
    const user = await abrirMenu();

    await user.click(await screen.findByRole("menuitemradio", { name: "Escuro" }));
    await user.click(screen.getByRole("button", { name: "Pessoa" }));

    expect(await screen.findByRole("menuitemradio", { name: "Escuro" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("menuitemradio", { name: "Sistema" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });
});
