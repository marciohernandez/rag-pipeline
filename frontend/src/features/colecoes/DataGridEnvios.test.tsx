import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { enviosExemplo, json, simularFetch } from "./_apoio";

type Papel = "owner" | "admin" | "member";
interface Props {
  papel: Papel;
  envios: typeof enviosExemplo;
}
type Modulo = { default: ComponentType<Props> };

const pessoa = (papel: Papel) => ({
  id: `pessoa-${papel}`, nome: "Pessoa de teste", email: `${papel}@exemplo.com`, papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca", pessoa("owner"));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  push.mockReset();
});

describe("DataGridEnvios", () => {
  it("lista os envios do mais recente ao mais antigo e oferece Repetir ao que falhou", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-012 FR-009 AC-009
    const { default: DataGridEnvios } = await exigir<Modulo>("@/features/colecoes/DataGridEnvios");
    const repetir = simularFetch({ "POST .*/api/v1/envios/env-3/retry": () => json({}, 202) });
    const user = userEvent.setup();
    render(<DataGridEnvios papel="owner" envios={enviosExemplo} />);

    const linhas = screen.getAllByRole("row").slice(1);
    expect(linhas.map((l) => within(l).getByText(/^env-\d$/).textContent)).toEqual(["env-3", "env-2", "env-1"]);
    for (const coluna of ["ID", "Arquivos", "Divisão", "Situação", "Contagens", "Autor", "Iniciado em"]) {
      expect(screen.getByRole("columnheader", { name: coluna })).toBeInTheDocument();
    }
    expect(linhas[0]).toHaveTextContent("Falha ao processar o envio");
    expect(within(linhas[0]).getByRole("button", { name: /repetir/i })).toBeInTheDocument();
    expect(within(linhas[1]).queryByRole("button", { name: /repetir/i })).toBeNull();

    await user.click(within(linhas[0]).getByRole("button", { name: /repetir/i }));
    await waitFor(() => expect(repetir).toHaveBeenCalled());

    linhas[1].focus();
    await user.keyboard("{Enter}");
    expect(push).toHaveBeenCalledWith("/envios/env-2");
  });
});
