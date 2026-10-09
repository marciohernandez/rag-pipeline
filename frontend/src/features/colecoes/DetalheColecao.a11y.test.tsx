import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { documentosExemplo, enviosExemplo, json } from "./_apoio";

interface PropsAbas {
  workspaceId: string;
  colecao: { id: string; nome: string };
  papel: "owner" | "admin" | "member";
  documentos: typeof documentosExemplo;
  envios: typeof enviosExemplo;
}
interface PropsPublicacao {
  resumo: { arquivos: number; chunks: number };
  workspaceId: string;
  onPublicar: () => Promise<{ envio_id: string; colecao_id: string }>;
}

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

async function violacoes(raiz: HTMLElement) {
  const axe = (await import("axe-core")).default;
  const resultado = await axe.run(raiz, {
    rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
  });
  return resultado.violations.map((v) => `${v.id}: ${v.help}`);
}

describe("Telas da coleção — acessibilidade", () => {
  it("alcança abas, linhas e grupo de opções só pelo teclado e passa no axe", async () => {
    // SPECSFY: SPEC-0030 NFR-003 FR-008 FR-002 AC-021
    const { default: AbasColecao } = await exigir<{ default: ComponentType<PropsAbas> }>(
      "@/features/colecoes/AbasColecao",
    );
    const { default: Publicacao } = await exigir<{ default: ComponentType<PropsPublicacao> }>(
      "@/features/ingestao/EtapaPublicacao",
    );
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/colecoes")) return json([{ id: "c1", nome: "manuais", documentos: 2, chunks: 17, ultimo_envio_em: null }]);
      if (url.includes("/api/v1/conexoes")) return json([]);
      return json({ embeddings: 1536, colecao: null, compativel: true });
    });
    const user = userEvent.setup();
    const abas = render(
      <AbasColecao
        workspaceId="w1"
        colecao={{ id: "c1", nome: "manuais" }}
        papel="owner"
        documentos={documentosExemplo}
        envios={enviosExemplo}
      />,
    );

    const lista = screen.getByRole("tablist");
    const documentosAba = within(lista).getByRole("tab", { name: "Documentos" });
    expect(documentosAba).toHaveAttribute("aria-selected", "true");
    documentosAba.focus();
    await user.keyboard("{ArrowRight}");
    expect(within(lista).getByRole("tab", { name: "Envios" })).toHaveFocus();
    await user.keyboard("{ArrowLeft}");
    expect(documentosAba).toHaveFocus();

    await user.tab();
    const linhaAlcancada = screen.getAllByRole("row").some((linha) => linha.contains(document.activeElement));
    expect(linhaAlcancada || document.activeElement?.closest("[role=tabpanel]") !== null).toBe(true);
    expect(await violacoes(abas.container)).toEqual([]);

    abas.unmount();
    const publicacao = render(<Publicacao resumo={{ arquivos: 1, chunks: 3 }} workspaceId="w1" onPublicar={vi.fn()} />);
    const grupo = await screen.findByRole("radiogroup", { name: /coleção/i });
    expect(within(grupo).getAllByRole("radio")).toHaveLength(2);
    expect(await violacoes(publicacao.container)).toEqual([]);
  });
});
