import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Imagem {
  documento_id: string;
  nome_arquivo: string;
  posicao: number;
}
interface Grupo {
  id: string;
  ordem: number;
  certeza: "total" | "incerta";
  aprovado: boolean;
  imagens: Imagem[];
}
interface Props {
  loteId: string;
  proposta: { certeza: "total" | "incerta"; grupos: Grupo[] };
  podeEscrever: boolean;
  onConfirmada?: () => void;
}
type Modulo = { default: ComponentType<Props> };

const LONGO = "conversa-de-whatsapp-com-nome-muito-longo-sem-espacos-".repeat(3) + "1.png";
const grupos = (certeza: "total" | "incerta", aprovado: boolean): Grupo[] => [
  {
    id: "g1", ordem: 1, certeza, aprovado,
    imagens: [
      { documento_id: "d1", nome_arquivo: "ana-1.png", posicao: 1 },
      { documento_id: "d2", nome_arquivo: LONGO, posicao: 2 },
    ],
  },
  { id: "g2", ordem: 2, certeza, aprovado, imagens: [{ documento_id: "d3", nome_arquivo: "bia-1.png", posicao: 1 }] },
];

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

const metodo = (chamadas: ReturnType<typeof simularFetch>, nome: string) =>
  chamadas.mock.calls.filter(([, init]) => init?.method === nome);

describe("AprovacaoGrupos", () => {
  it("com certeza total vem pré-aprovado e um clique confirma", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 AC-004
    const { default: Aprovacao } = await exigir<Modulo>("@/features/conversao/AprovacaoGrupos");
    const chamadas = simularFetch({
      "POST .*/api/v1/conversoes/l1/grupos/confirmar$": () => json({ documentos: [] }, 202),
    });
    const onConfirmada = vi.fn();
    const user = userEvent.setup();
    render(<Aprovacao loteId="l1" proposta={{ certeza: "total", grupos: grupos("total", true) }} podeEscrever onConfirmada={onConfirmada} />);

    expect(screen.getAllByText(/pré-aprovado/i)).toHaveLength(2);
    await user.click(screen.getByRole("button", { name: "Confirmar grupos" }));

    expect(metodo(chamadas, "POST")).toHaveLength(1);
    expect(metodo(chamadas, "PUT")).toHaveLength(0);
    expect(onConfirmada).toHaveBeenCalled();
  });

  it("com proposta incerta nada vem pré-aprovado e o aviso orienta a conferir", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 AC-004
    const { default: Aprovacao } = await exigir<Modulo>("@/features/conversao/AprovacaoGrupos");
    simularFetch({});
    render(<Aprovacao loteId="l1" proposta={{ certeza: "incerta", grupos: grupos("incerta", false) }} podeEscrever />);

    expect(screen.queryByText(/pré-aprovado/i)).toBeNull();
    expect(screen.getByRole("alert")).toHaveTextContent(/confira/i);
  });

  it("em 375 px empilha os cartões, quebra nomes longos e mantém Confirmar grupos acessível", async () => {
    // SPECSFY: SPEC-0040 US-002 NFR-004 AC-021
    const { default: Aprovacao } = await exigir<Modulo>("@/features/conversao/AprovacaoGrupos");
    simularFetch({});
    render(<Aprovacao loteId="l1" proposta={{ certeza: "incerta", grupos: grupos("incerta", false) }} podeEscrever />);

    const lista = screen.getByTestId("lista-grupos");
    expect(lista.className).toMatch(/flex-col|grid-cols-1/);
    expect(lista.className).not.toMatch(/overflow-x-(auto|scroll)/);
    expect(screen.getByText(LONGO, { selector: "span" }).className).toMatch(/break-words|wrap-anywhere|break-all/);
    const rodape = screen.getByRole("button", { name: "Confirmar grupos" }).closest("[data-testid='rodape-aprovacao']");
    expect(rodape).not.toBeNull();
    expect(rodape?.className).toMatch(/sticky/);
    expect(rodape?.className).toMatch(/bottom-0/);
  });

  it("member vê os grupos em modo leitura, sem controles, com o aviso de quem aprova", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-007 NFR-004 AC-025
    const { default: Aprovacao } = await exigir<Modulo>("@/features/conversao/AprovacaoGrupos");
    simularFetch({});
    render(<Aprovacao loteId="l1" proposta={{ certeza: "incerta", grupos: grupos("incerta", false) }} podeEscrever={false} />);

    expect(screen.queryByRole("button", { name: "Confirmar grupos" })).toBeNull();
    expect(screen.queryByRole("button", { name: /subir|descer/i })).toBeNull();
    expect(screen.queryByLabelText(/mover .* para outro grupo/i)).toBeNull();
    expect(screen.getByText(/owner ou admin/i)).toBeInTheDocument();
    expect(screen.getByText("ana-1.png")).toBeInTheDocument();
  });

  it("envia o ajuste antes de confirmar quando a pessoa mudou os grupos e anuncia o resultado", async () => {
    // SPECSFY: SPEC-0040 US-002 FR-002 AC-004
    const { default: Aprovacao } = await exigir<Modulo>("@/features/conversao/AprovacaoGrupos");
    const chamadas = simularFetch({
      "PUT .*/api/v1/conversoes/l1/grupos$": () => json({ grupos: [] }),
      "POST .*/api/v1/conversoes/l1/grupos/confirmar$": () => json({ documentos: [] }, 202),
    });
    const user = userEvent.setup();
    render(<Aprovacao loteId="l1" proposta={{ certeza: "incerta", grupos: grupos("incerta", false) }} podeEscrever />);

    await user.click(screen.getByRole("button", { name: "Descer ana-1.png" }));
    await user.click(screen.getByRole("button", { name: "Confirmar grupos" }));

    expect(metodo(chamadas, "PUT")).toHaveLength(1);
    expect(metodo(chamadas, "POST")).toHaveLength(1);
    expect(screen.getByText(/grupos confirmados/i)).toBeInTheDocument();
  });
});
