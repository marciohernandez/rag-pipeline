import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { exigir } from "@/test/carregar";
import { apiJson } from "@/lib/api-client";

vi.mock("@/lib/api-client", () => ({ apiJson: vi.fn(), apiFetch: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const PALAVRA_LONGA = "domínio".repeat(40);
type Props = { workspaceId: string; papel: string };

async function montar(papel: string) {
  vi.mocked(apiJson).mockImplementation(async (caminho: string) => {
    if (caminho.endsWith("/dominio")) {
      return { versao: 2, texto: PALAVRA_LONGA, aprovado_por: "p1", criado_em: "2026-10-16" };
    }
    if (caminho.endsWith("/versoes")) return [];
    return [];
  });
  const { default: Secao } = await exigir<{ default: ComponentType<Props> }>(
    "@/features/workspaces/SecaoDominioEmpresa",
  );
  render(<Secao workspaceId="w1" papel={papel} />);
  return await screen.findByRole("region", { name: /Domínio da empresa/i });
}

it("em 375 px usa coluna única e quebra textos longos sem rolagem horizontal", async () => {
  // SPECSFY: SPEC-0037 US-002 US-005 NFR-004 AC-016
  const secao = await montar("owner");

  expect(secao.className).toMatch(/flex-col|grid-cols-1/);
  const campo = await screen.findByRole("textbox", { name: /resumo do domínio/i });
  expect(campo.className).toMatch(/w-full/);
  expect(secao.innerHTML).toMatch(/overflow-wrap:anywhere|break-words/);
  expect(secao.className).not.toMatch(/overflow-x-(scroll|auto)/);
});

it("owner salva por teclado; member só consulta", async () => {
  // SPECSFY: SPEC-0037 US-002 US-005 NFR-004 AC-016
  await montar("owner");
  const salvar = await screen.findByRole("button", { name: "Salvar" });
  salvar.focus();
  expect(salvar).toHaveFocus();
  cleanup();

  await montar("member");
  expect(screen.queryByRole("button", { name: "Salvar" })).toBeNull();
  expect(await screen.findByText(new RegExp(PALAVRA_LONGA.slice(0, 20)))).toBeInTheDocument();
});

it("anuncia o resultado do salvamento em role=status", async () => {
  // SPECSFY: SPEC-0037 US-002 US-005 NFR-004 AC-016
  await montar("owner");

  const salvar = await screen.findByRole("button", { name: "Salvar" });
  salvar.click();

  expect(await screen.findByRole("status")).toHaveTextContent(/salv/i);
});
