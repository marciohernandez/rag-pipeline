import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";
import { exigir } from "@/test/carregar";

const baixar = vi.fn();
vi.mock("@/features/conversao/acoesDocumento", () => ({
  baixar: (...args: unknown[]) => baixar(...args),
  baixarMarkdown: vi.fn(),
  reenviarDocumento: vi.fn(),
}));
vi.mock("@/lib/api-client", () => ({ apiJson: vi.fn(), apiFetch: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const documento = (id: string, nome: string, extra: Record<string, unknown>) => ({
  id,
  nome_arquivo: nome,
  formato: "pdf",
  tamanho_bytes: 10,
  situacao: "concluido",
  erro: null,
  criado_em: "2026-10-16T10:00:00Z",
  concluido_em: "2026-10-16T10:01:00Z",
  ...extra,
});
const lote = {
  id: "l1",
  workspace_id: "w1",
  situacao: "concluido",
  criado_em: "2026-10-16T10:00:00Z",
  documentos: [
    documento("d1", "a.pdf", { limpeza_situacao: "limpo", exclusoes: 2, duvidas: 0 }),
    documento("d2", "b.pdf", { limpeza_situacao: "limpo_com_duvidas", exclusoes: 1, duvidas: 3 }),
  ],
};

async function montar(papel: string) {
  const { default: Painel } = await exigir<{
    default: ComponentType<{ lote: unknown; papel?: string }>;
  }>("@/features/conversao/PainelLoteConversao");
  render(<Painel lote={lote} papel={papel} />);
  return userEvent.setup();
}

it("mostra contagens por documento e baixa o relatório por teclado", async () => {
  // SPECSFY: SPEC-0037 US-005 FR-007 FR-009 NFR-004 AC-014
  const usuario = await montar("owner");

  expect(screen.getByText(/2 exclusões/i)).toBeInTheDocument();
  expect(screen.getByText(/3 dúvidas/i)).toBeInTheDocument();
  const botao = screen.getByRole("button", { name: "Baixar relatório do lote" });
  botao.focus();
  expect(botao).toHaveFocus();
  await usuario.keyboard("{Enter}");
  expect(baixar).toHaveBeenCalledWith(
    "/api/v1/conversoes/l1/relatorio",
    expect.stringMatching(/relatorio.*\.md$/),
  );
});

it("não oferece o download do relatório a quem só consulta", async () => {
  // SPECSFY: SPEC-0037 US-005 FR-009 NFR-004 AC-014
  await montar("member");

  expect(screen.getByText(/2 exclusões/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Baixar relatório do lote" })).toBeNull();
});
