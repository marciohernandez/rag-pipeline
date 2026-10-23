import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { exigir } from "@/test/carregar";

type Papel = "owner" | "admin" | "member";
interface Doc {
  id: string;
  nome_arquivo: string;
  situacao: "fila" | "processando" | "concluido" | "falhou";
  apagado_em?: string | null;
  limpeza_situacao?: string | null;
}
interface Props {
  workspaceId: string;
  papel: Papel;
  lote: { id: string; situacao: string; documentos: Doc[] };
}
type Modulo = { default: ComponentType<Props> };

const doc = (id: string, nome: string, extra: Partial<Doc> = {}): Doc => ({
  id, nome_arquivo: nome, situacao: "concluido", ...extra,
});
const tres = [doc("d1", "a.pdf"), doc("d2", "b.pdf"), doc("d3", "c.pdf")];
const lote = (situacao: string, documentos: Doc[] = tres) => ({ id: "lote-1", situacao, documentos });

beforeEach(() => push.mockReset());
afterEach(cleanup);

describe("SeguirParaIndexacao — disponibilidade e seleção", () => {
  it("owner marca os aptos por padrão, desmarca um e segue com os restantes", async () => {
    // SPECSFY: SPEC-0043 US-001 FR-001 FR-002 FR-005 FR-009 NFR-004 AC-001
    const { default: Seguir } = await exigir<Modulo>("@/features/conversao/SeguirParaIndexacao");
    const user = userEvent.setup();
    render(<Seguir workspaceId="ws-1" papel="owner" lote={lote("concluido")} />);

    const caixas = screen.getAllByRole("checkbox");
    expect(caixas).toHaveLength(3);
    caixas.forEach((c) => expect(c).toBeChecked());
    expect(screen.getByRole("status")).toHaveTextContent(/3 documentos marcados/i);

    await user.click(screen.getByRole("checkbox", { name: /b\.pdf/i }));
    expect(screen.getByRole("status")).toHaveTextContent(/2 documentos marcados/i);

    await user.click(screen.getByRole("button", { name: /seguir para a indexação/i }));
    expect(push).toHaveBeenCalledTimes(1);
    const destino = String(push.mock.calls[0][0]);
    expect(destino).toContain("/workspaces/ws-1/enviar");
    expect(destino).toContain("lote=lote-1");
    expect(destino).toContain("documentos=d1%2Cd3");
  });

  it("fica indisponível, com o motivo visível, quando o lote não pode seguir", async () => {
    // SPECSFY: SPEC-0043 US-001 FR-001 FR-009 FR-010 AC-002
    const { default: Seguir } = await exigir<Modulo>("@/features/conversao/SeguirParaIndexacao");
    const casos: Array<[string, ReturnType<typeof lote>, RegExp]> = [
      ["processando", lote("processando"), /processamento/i],
      ["aguardando_dominio", lote("aguardando_dominio"), /domínio/i],
      ["limpando", lote("limpando"), /limpeza/i],
      ["sem apto", lote("concluido_com_falhas", [doc("d1", "a.pdf", { situacao: "falhou" })]), /nenhum documento apto/i],
      ["apagados", lote("concluido", [doc("d1", "a.pdf", { apagado_em: "2026-10-20T10:00:00Z" })]), /apagad|expirad/i],
    ];
    for (const [rotulo, loteCaso, motivo] of casos) {
      const { unmount } = render(<Seguir workspaceId="ws-1" papel="owner" lote={loteCaso} />);
      const botao = screen.getByRole("button", { name: /seguir para a indexação/i });
      expect(botao, rotulo).toBeDisabled();
      expect(screen.getByRole("status"), rotulo).toHaveTextContent(motivo);
      unmount();
    }
    expect(push).not.toHaveBeenCalled();
  });

  it("sem documento marcado a ação fica indisponível e o motivo é anunciado", async () => {
    // SPECSFY: SPEC-0043 US-001 FR-002 FR-005 NFR-004 AC-004
    const { default: Seguir } = await exigir<Modulo>("@/features/conversao/SeguirParaIndexacao");
    const user = userEvent.setup();
    render(<Seguir workspaceId="ws-1" papel="admin" lote={lote("concluido", [doc("d1", "a.pdf")])} />);

    await user.click(screen.getByRole("checkbox", { name: /a\.pdf/i }));

    expect(screen.getByRole("button", { name: /seguir para a indexação/i })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent(/nenhum documento marcado/i);
    await user.click(screen.getByRole("button", { name: /seguir para a indexação/i }));
    expect(push).not.toHaveBeenCalled();
  });
});
