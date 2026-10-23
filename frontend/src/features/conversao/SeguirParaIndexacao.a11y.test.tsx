import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { exigir } from "@/test/carregar";

type Papel = "owner" | "admin" | "member";
interface SeguirProps {
  workspaceId: string;
  papel: Papel;
  lote: { id: string; situacao: string; documentos: Array<{ id: string; nome_arquivo: string; situacao: string }> };
}
interface GradeProps {
  workspaceId: string;
  colecaoId: string;
  papel: Papel;
  documentos: Array<Record<string, unknown>>;
}

const lote = {
  id: "lote-1", situacao: "concluido",
  documentos: [
    { id: "d1", nome_arquivo: "a.pdf", situacao: "concluido" },
    { id: "d2", nome_arquivo: "b.pdf", situacao: "concluido" },
  ],
};
const alterado = {
  id: "doc-a", nome_arquivo: "a.md", chunks: 12, chunking: { splitter: "header" },
  ultimo_envio_em: "2026-10-09T10:00:00Z",
  origem: { lote_id: "lote-1", documento_conversao_id: "d1", situacao_origem: "alterado" },
};

beforeEach(() => push.mockReset());
afterEach(cleanup);

describe("SeguirParaIndexacao e reindexação — teclado e estados (SPEC-0043)", () => {
  it("alcança caixas e botão pelo teclado e anuncia a mudança de seleção em role=status", async () => {
    // SPECSFY: SPEC-0043 US-001 US-003 FR-001 FR-002 FR-007 NFR-004 AC-014
    const { default: Seguir } = await exigir<{ default: ComponentType<SeguirProps> }>(
      "@/features/conversao/SeguirParaIndexacao",
    );
    const user = userEvent.setup();
    render(<Seguir workspaceId="ws-1" papel="owner" lote={lote} />);

    await user.tab();
    expect(screen.getByRole("checkbox", { name: /a\.pdf/i })).toHaveFocus();
    await user.keyboard(" ");
    expect(screen.getByRole("checkbox", { name: /a\.pdf/i })).not.toBeChecked();
    expect(screen.getByRole("status")).toHaveTextContent(/1 documento marcado/i);
    await user.tab();
    await user.tab();
    expect(screen.getByRole("button", { name: /seguir para a indexação/i })).toHaveFocus();
  });

  it("owner reindexa documento alterado pelo teclado e o foco volta ao acionador", async () => {
    // SPECSFY: SPEC-0043 US-003 FR-007 FR-008 NFR-004 AC-014
    const { default: Grade } = await exigir<{ default: ComponentType<GradeProps> }>(
      "@/features/colecoes/DataGridDocumentos",
    );
    const user = userEvent.setup();
    render(<Grade workspaceId="ws-1" colecaoId="col-1" papel="owner" documentos={[alterado]} />);

    expect(screen.getByText(/alterado desde a indexação/i)).toBeInTheDocument();
    const acionador = screen.getByRole("button", { name: /reindexar/i });
    acionador.focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("dialog")).toHaveTextContent(/embeddings/i);

    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(acionador).toHaveFocus();
  });
});
