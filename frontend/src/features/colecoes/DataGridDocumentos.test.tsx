import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { documentosExemplo, json, simularFetch } from "./_apoio";

type Papel = "owner" | "admin" | "member";
interface Props {
  workspaceId: string;
  colecaoId: string;
  papel: Papel;
  documentos: typeof documentosExemplo;
}
type Modulo = { default: ComponentType<Props> };

const pessoa = (papel: Papel) => ({
  id: `pessoa-${papel}`, nome: "Pessoa de teste", email: `${papel}@exemplo.com`, papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca", pessoa("member"));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  push.mockReset();
});

describe("DataGridDocumentos", () => {
  it("member vê documentos sem ações de escrita e abre os chunks pelo teclado", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-008 FR-015 NFR-003 AC-008
    const { default: DataGridDocumentos } = await exigir<Modulo>("@/features/colecoes/DataGridDocumentos");
    simularFetch({
      "/documentos/doc-a/chunks": () =>
        json([{ chunk_id: "k1", secao: "Seção 1", texto: "Texto do primeiro chunk de a.md" }]),
    });
    const user = userEvent.setup();
    render(
      <DataGridDocumentos workspaceId="w1" colecaoId="c1" papel="member" documentos={documentosExemplo} />,
    );

    for (const coluna of ["ID", "Arquivo", "Chunks", "Divisão", "Último envio"]) {
      expect(screen.getByRole("columnheader", { name: coluna })).toBeInTheDocument();
    }
    expect(screen.getAllByRole("columnheader")[0]).toHaveTextContent("ID");
    expect(screen.queryByRole("button", { name: /adicionar documentos|substituir|apagar|renomear/i })).toBeNull();

    const linha = screen.getByRole("row", { name: /a\.md/i });
    linha.focus();
    await user.keyboard("{Enter}");

    const painel = await screen.findByRole("dialog");
    expect(painel).toHaveTextContent("Texto do primeiro chunk de a.md");
    expect(painel.querySelector("input, textarea, [contenteditable=true]")).toBeNull();

    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(linha).toHaveFocus();
  });
});
