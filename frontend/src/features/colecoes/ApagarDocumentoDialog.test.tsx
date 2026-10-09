import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { json, simularFetch } from "./_apoio";

interface Props {
  open: boolean;
  colecaoId: string;
  documento: { id: string; nome_arquivo: string; chunks: number };
  onDeleted: (id: string) => void;
  onClose?: () => void;
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

describe("ApagarDocumentoDialog", () => {
  it("mantém o diálogo aberto com erro seguro quando o Qdrant falha", async () => {
    // SPECSFY: SPEC-0030 US-004 FR-009 NFR-001 NFR-004 AC-011
    const { default: ApagarDocumentoDialog } = await exigir<Modulo>("@/features/colecoes/ApagarDocumentoDialog");
    simularFetch({
      "DELETE .*/api/v1/colecoes/c1/documentos/doc-a": () =>
        json({ detail: "Não foi possível apagar o documento. Tente novamente." }, 502),
    });
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(
      <ApagarDocumentoDialog
        open
        colecaoId="c1"
        documento={{ id: "doc-a", nome_arquivo: "a.md", chunks: 12 }}
        onDeleted={onDeleted}
      />,
    );

    expect(screen.getByRole("dialog")).toHaveTextContent(/a\.md/);
    expect(screen.getByRole("dialog")).toHaveTextContent(/12 chunks/);

    await user.click(screen.getByRole("button", { name: /apagar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível apagar o documento. Tente novamente.",
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(onDeleted).not.toHaveBeenCalled();
  });
});
