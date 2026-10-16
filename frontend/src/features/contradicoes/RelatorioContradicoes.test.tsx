import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Modulo = { default: ComponentType<{ colecaoId: string; nomeColecao?: string }> };

const trechos = (a: string, b: string) => [
  { arquivo: a, texto: "Valor X." },
  { arquivo: b, texto: "Valor Y." },
];
const OCORRENCIAS = [
  { id: "o1", assunto: "horário de atendimento", etiqueta: "conflito", impacto: "baixo",
    trechos: trechos("a.md", "b.md"), explicacao: "Horários diferentes." },
  { id: "o2", assunto: "preço do plano", etiqueta: "conflito", impacto: "alto",
    trechos: trechos("c.md", "d.md"), explicacao: "Preços diferentes." },
  { id: "o3", assunto: "prazo de entrega", etiqueta: "versao_desatualizada", impacto: "alto",
    trechos: trechos("e.md", "f.md"), explicacao: "Versões diferentes." },
];
const analise = {
  id: "a1", situacao: "concluida", motivo: null, provedor: "openrouter",
  dominio_versao_id: "d1", total_assuntos: 3, concluidos: 3, documentos_analisados: 6,
};

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

describe("RelatorioContradicoes", () => {
  it("põe valores e prazos no topo e filtra por etiqueta", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-007 AC-015
    const { default: Relatorio } = await exigir<Modulo>("@/features/contradicoes/RelatorioContradicoes");
    simularFetch({
      "GET .*/api/v1/colecoes/c1/contradicoes.*": () =>
        json({ analise, ocorrencias: OCORRENCIAS, nao_classificadas: 0 }),
    });
    const user = userEvent.setup();
    render(<Relatorio colecaoId="c1" nomeColecao="políticas" />);

    await screen.findByText("preço do plano");
    const titulos = () => screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(titulos().slice(0, 2).sort()).toEqual(["prazo de entrega", "preço do plano"]);
    expect(titulos()[2]).toBe("horário de atendimento");

    await user.click(screen.getByRole("button", { name: "Conflito" }));

    expect(titulos()).toEqual(["preço do plano", "horário de atendimento"]);
    expect(screen.queryByText("prazo de entrega")).toBeNull();
    expect(screen.getByRole("button", { name: "Conflito" })).toHaveAttribute("aria-pressed", "true");
  });

  it("sem ocorrências diz que nenhuma contradição foi encontrada e quantos documentos foram analisados", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-004 FR-007 AC-016
    const { default: Relatorio } = await exigir<Modulo>("@/features/contradicoes/RelatorioContradicoes");
    simularFetch({
      "GET .*/api/v1/colecoes/c1/contradicoes.*": () =>
        json({ analise: { ...analise, documentos_analisados: 8 }, ocorrencias: [], nao_classificadas: 0 }),
    });
    render(<Relatorio colecaoId="c1" />);

    expect(await screen.findByText("Nenhuma contradição encontrada")).toBeInTheDocument();
    expect(screen.getByText(/8 documentos/)).toBeInTheDocument();
  });

  it("member consulta mas não vê os botões de baixar", async () => {
    // SPECSFY: SPEC-0038 US-005 FR-007 AC-016
    saveSession("sessao-opaca", {
      id: "p2", nome: "Leitora", email: "member@exemplo.com", papel: "member",
      tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
    });
    const { default: Relatorio } = await exigir<Modulo>("@/features/contradicoes/RelatorioContradicoes");
    simularFetch({
      "GET .*/api/v1/colecoes/c1/contradicoes.*": () =>
        json({ analise, ocorrencias: OCORRENCIAS, nao_classificadas: 0 }),
    });
    render(<Relatorio colecaoId="c1" />);

    await screen.findByText("preço do plano");
    expect(screen.queryByRole("button", { name: /baixar markdown/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /baixar pdf/i })).toBeNull();
    expect(within(document.body).getAllByRole("heading", { level: 3 })).toHaveLength(3);
  });
});
