import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const apiFetch = vi.fn();
const apiJson = vi.fn();
vi.mock("@/lib/api-client", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  apiJson: (...args: unknown[]) => apiJson(...args),
}));

import { exigir } from "@/test/carregar";

type Doc = {
  id: string; nome_arquivo: string; formato: string; tamanho_bytes: number;
  situacao: "fila" | "processando" | "concluido" | "falhou"; erro: string | null;
  criado_em: string; concluido_em: string | null;
};
type Lote = {
  id: string; workspace_id: string; situacao: "processando" | "concluido" | "concluido_com_falhas";
  criado_em: string; criado_por: { id: string; nome: string; desativada: boolean } | null; documentos: Doc[];
};
type Props = {
  lotes: Lote[]; papel?: string; carregando?: boolean; onConverter?: () => void;
  onLoteAtualizado?: (lote: Lote) => void;
};
type Modulo = { default: ComponentType<Props> };

const doc = (id: string, nome: string, situacao: Doc["situacao"]): Doc => ({
  id, nome_arquivo: nome, formato: nome.split(".").pop() ?? "", tamanho_bytes: 1024, situacao,
  erro: situacao === "falhou" ? "Documento ilegível" : null,
  criado_em: "2026-10-14T10:00:00Z", concluido_em: null,
});
const autor = { id: "p1", nome: "Marcio", desativada: false };
const LOTES: Lote[] = [
  {
    id: "L1", workspace_id: "w1", situacao: "concluido_com_falhas", criado_em: "2026-10-14T10:00:00Z",
    criado_por: autor,
    documentos: [doc("D1", "relatorio.pdf", "concluido"), doc("D2", "planilha.xlsx", "fila"), doc("D3", "scan.png", "falhou")],
  },
  {
    id: "L2", workspace_id: "w1", situacao: "processando", criado_em: "2026-10-14T11:00:00Z",
    criado_por: autor, documentos: [doc("D4", "contrato.docx", "processando")],
  },
];

beforeEach(() => {
  apiFetch.mockResolvedValue({ blob: async () => new Blob(["# md"]) });
  apiJson.mockResolvedValue(LOTES[0]);
  URL.createObjectURL = vi.fn(() => "blob:teste");
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  apiFetch.mockReset();
  apiJson.mockReset();
});

async function carregarGrid() {
  const { default: Grid } = await exigir<Modulo>("@/features/conversao/DataGridLotesConversao");
  return Grid;
}

describe("Lista de documentos da aba Conversão de documentos", () => {
  it("lista uma linha por documento com situação em rótulo legível", async () => {
    // SPECSFY: SPEC-0023 US-005 FR-004 FR-009 AC-020
    const Grid = await carregarGrid();
    render(<Grid lotes={LOTES} papel="owner" />);

    const cabecalhos = screen.getAllByRole("columnheader").map((c) => c.textContent);
    expect(cabecalhos).toEqual(
      expect.arrayContaining(["ID", "Arquivo", "Formato", "Situação", "Lote", "Criado em", "Criado por"]),
    );
    const linhas = screen.getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(4);
    for (const nome of ["relatorio.pdf", "planilha.xlsx", "scan.png", "contrato.docx"]) {
      expect(screen.getByText(nome)).toBeInTheDocument();
    }
    for (const rotulo of ["Convertido", "Na fila", "Falhou", "Processando"]) {
      expect(screen.getByText(rotulo)).toBeInTheDocument();
    }
    expect(screen.queryByText("concluido")).toBeNull();
    expect(screen.queryByText("processando")).toBeNull();
    expect(screen.queryByText("concluido_com_falhas")).toBeNull();
  });

  it("baixa, reenvia e abre o painel do lote a partir da linha do documento", async () => {
    // SPECSFY: SPEC-0023 US-005 US-003 US-004 FR-005 FR-006 FR-009 AC-021
    const Grid = await carregarGrid();
    const user = userEvent.setup();
    render(<Grid lotes={LOTES} papel="owner" />);

    const convertido = screen.getByText("relatorio.pdf").closest("tr") as HTMLElement;
    await user.click(within(convertido).getByRole("button", { name: /baixar/i }));
    expect(apiFetch).toHaveBeenCalledWith("/api/v1/conversoes/L1/documentos/D1/markdown");
    expect(screen.queryByRole("button", { name: /baixar todos/i })).toBeNull();

    const falho = screen.getByText("scan.png").closest("tr") as HTMLElement;
    await user.click(within(falho).getByRole("button", { name: /reenviar/i }));
    expect(apiJson).toHaveBeenCalledWith(
      "/api/v1/conversoes/L1/documentos/D3/reenviar",
      expect.objectContaining({ method: "POST" }),
    );

    falho.focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("button", { name: /baixar todos/i })).toBeInTheDocument();
  });

  it("não oferece reenviar a quem não tem permissão de escrita", async () => {
    // SPECSFY: SPEC-0023 US-005 US-004 FR-006 FR-009 AC-021
    const Grid = await carregarGrid();
    render(<Grid lotes={LOTES} papel="member" />);

    expect(screen.getAllByRole("row").slice(1)).toHaveLength(4);
    expect(screen.queryByRole("button", { name: /reenviar/i })).toBeNull();
    expect(screen.getAllByRole("button", { name: /baixar/i }).length).toBeGreaterThan(0);
  });

  it("mostra o vazio com o botão Converter documentos conforme o papel", async () => {
    // SPECSFY: SPEC-0023 US-005 US-001 FR-009 AC-022
    const Grid = await carregarGrid();
    const user = userEvent.setup();
    const onConverter = vi.fn();

    const dono = render(<Grid lotes={[]} papel="owner" onConverter={onConverter} />);
    expect(screen.getByText(/nenhum documento convertido ainda/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Converter documentos" }));
    expect(onConverter).toHaveBeenCalledTimes(1);
    dono.unmount();

    render(<Grid lotes={[]} papel="member" onConverter={onConverter} />);
    expect(screen.getByText(/nenhum documento convertido ainda/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Converter documentos" })).toBeNull();
  });

  it("apaga um documento pela linha depois de confirmar a consequência", async () => {
    // SPECSFY: SPEC-0023 US-006 FR-010 AC-023
    const Grid = await carregarGrid();
    const user = userEvent.setup();
    const onLoteAtualizado = vi.fn();
    render(<Grid lotes={LOTES} papel="owner" onLoteAtualizado={onLoteAtualizado} />);

    const linha = screen.getByText("scan.png").closest("tr") as HTMLElement;
    await user.click(within(linha).getByRole("button", { name: /apagar/i }));
    const dialogo = await screen.findByRole("dialog");
    expect(dialogo).toHaveTextContent(/scan\.png/);
    expect(dialogo).toHaveTextContent(/original/i);
    expect(dialogo).toHaveTextContent(/não é possível desfazer/i);
    expect(apiFetch).not.toHaveBeenCalled();

    await user.click(within(dialogo).getByRole("button", { name: /^apagar$/i }));
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/v1/conversoes/L1/documentos/D3",
      expect.objectContaining({ method: "DELETE" }),
    );
    expect(onLoteAtualizado).toHaveBeenCalledTimes(1);
  });

  it("cancelar o diálogo de apagar não apaga nada", async () => {
    // SPECSFY: SPEC-0023 US-006 FR-010 AC-023
    const Grid = await carregarGrid();
    const user = userEvent.setup();
    render(<Grid lotes={LOTES} papel="owner" />);

    const linha = screen.getByText("relatorio.pdf").closest("tr") as HTMLElement;
    await user.click(within(linha).getByRole("button", { name: /apagar/i }));
    const dialogo = await screen.findByRole("dialog");
    await user.click(within(dialogo).getByRole("button", { name: /cancelar/i }));

    expect(apiFetch).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByText("relatorio.pdf")).toBeInTheDocument();
  });

  it("não oferece apagar em fila ou processando nem a quem só lê", async () => {
    // SPECSFY: SPEC-0023 US-006 FR-010 AC-024 AC-025
    const Grid = await carregarGrid();
    const dono = render(<Grid lotes={LOTES} papel="owner" />);
    for (const nome of ["planilha.xlsx", "contrato.docx"]) {
      const linha = screen.getByText(nome).closest("tr") as HTMLElement;
      expect(within(linha).queryByRole("button", { name: /apagar/i })).toBeNull();
    }
    expect(screen.getAllByRole("button", { name: /apagar/i })).toHaveLength(2);
    dono.unmount();

    render(<Grid lotes={LOTES} papel="member" />);
    expect(screen.queryByRole("button", { name: /apagar/i })).toBeNull();
  });
});
