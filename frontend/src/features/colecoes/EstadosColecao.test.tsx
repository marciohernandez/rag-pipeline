import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Modulo<P> = { default: ComponentType<P> };

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
  push.mockReset();
});

describe("Estados das telas da coleção", () => {
  it("mostra estados vazio, carregando e erro das telas da coleção", async () => {
    // SPECSFY: SPEC-0030 US-003 NFR-003 FR-008 FR-012 FR-014 AC-022
    const { default: DataGridColecoes } = await exigir<
      Modulo<{ workspaceId: string; papel: string; colecoes: unknown[] }>
    >("@/features/colecoes/DataGridColecoes");
    const { default: DataGridDocumentos } = await exigir<
      Modulo<{
        workspaceId: string; colecaoId: string; papel: string; documentos: unknown[];
        estado?: "carregando" | "erro"; onTentarNovamente?: () => void;
      }>
    >("@/features/colecoes/DataGridDocumentos");
    const { default: DataGridEnvios } = await exigir<
      Modulo<{ papel: string; envios: unknown[]; estado?: "carregando" | "erro" }>
    >("@/features/colecoes/DataGridEnvios");
    const user = userEvent.setup();

    const workspace = render(<DataGridColecoes workspaceId="w1" papel="owner" colecoes={[]} />);
    expect(screen.getByText("Nenhuma coleção ainda")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar documentos" })).toBeInTheDocument();
    expect(screen.queryByText(/nova base/i)).toBeNull();
    workspace.unmount();

    const vazio = render(<DataGridDocumentos workspaceId="w1" colecaoId="c1" papel="owner" documentos={[]} />);
    expect(screen.getByText("Nenhum documento")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Adicionar documentos" })).toBeInTheDocument();
    vazio.unmount();

    const carregando = render(<DataGridEnvios papel="owner" envios={[]} estado="carregando" />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent(/carregando/i);
    expect(carregando.container.querySelector("[aria-busy=true]")).not.toBeNull();
    carregando.unmount();

    const tentar = vi.fn();
    render(
      <DataGridDocumentos
        workspaceId="w1" colecaoId="c1" papel="owner" documentos={[]} estado="erro" onTentarNovamente={tentar}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(tentar).toHaveBeenCalledTimes(1);
  });
});
