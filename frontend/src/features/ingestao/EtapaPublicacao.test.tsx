import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Valores {
  conexaoEmbeddingsId: string;
  conexaoVectorStoreId: string;
  colecao: string;
}
interface Props {
  resumo: { arquivos: number; chunks: number };
  onPublicar: (valores: Valores) => Promise<{ base_id: string; execution_id: string }>;
}
type Modulo = { default: ComponentType<Props> };

const owner = {
  id: "pessoa-owner", nome: "Pessoa de teste", email: "owner@exemplo.com", papel: "owner" as const,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
};
const embeddings = {
  id: "con-e", nome: "OpenAI principal", tipo: "embeddings_openai", situacao: "ativa",
  configuracao: { modelo: "text-embedding-3-small", dimensoes: 1536 },
};
const qdrant = { id: "con-q", nome: "Qdrant produção", tipo: "qdrant", situacao: "ativa", configuracao: {} };
const resumo = { arquivos: 2, chunks: 6 };
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

function simular(conexoes: unknown[], dimensao: Record<string, unknown> = { embeddings: 1536, colecao: null, compativel: true }) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.includes("/api/v1/ingestao/dimensao")) return json(dimensao);
    if (url.includes("/api/v1/conexoes")) return json(conexoes);
    throw new Error(`URL inesperada: ${url}`);
  });
}

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-owner", owner);
  push.mockReset();
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("EtapaPublicacao", () => {
  it("sem conexão ativa orienta para Conexões e bloqueia Publicar com a razão visível", async () => {
    // SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([]);
    render(<EtapaPublicacao resumo={resumo} onPublicar={vi.fn()} />);

    expect(await screen.findByText(/nenhuma conexão ativa/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /conexões/i })).toHaveAttribute("href", "/conexoes");
    expect(screen.getByRole("button", { name: /publicar/i })).toBeDisabled();
  });

  it("bloqueia Publicar quando a dimensão da coleção diverge e mostra as duas dimensões", async () => {
    // SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant], { embeddings: 1536, colecao: 3072, compativel: false });
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} onPublicar={vi.fn()} />);

    await user.type(await screen.findByLabelText(/coleção/i), "produtos");

    expect(await screen.findByText(/3072/)).toBeInTheDocument();
    expect(screen.getByText(/1536/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /publicar/i })).toBeDisabled();
  });

  it("mostra Alert com Tentar novamente na falha e mantém o preenchimento", async () => {
    // SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant]);
    const onPublicar = vi.fn().mockRejectedValue(new Error("falha de rede"));
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} onPublicar={onPublicar} />);

    const colecao = await screen.findByLabelText(/coleção/i);
    await user.type(colecao, "produtos");
    await user.click(screen.getByRole("button", { name: /publicar/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
    expect(colecao).toHaveValue("produtos");
  });

  it("depois de publicar leva à página da Base e anuncia o resultado", async () => {
    // SPECSFY: SPEC-0026 US-003 FR-010 FR-014 AC-019
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant]);
    const onPublicar = vi.fn().mockResolvedValue({ base_id: "base-9", execution_id: "exec-9" });
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} onPublicar={onPublicar} />);

    await user.type(await screen.findByLabelText(/coleção/i), "produtos");
    await user.click(screen.getByRole("button", { name: /publicar/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/execucoes/base-9"));
    expect(onPublicar).toHaveBeenCalledWith({
      conexaoEmbeddingsId: "con-e",
      conexaoVectorStoreId: "con-q",
      colecao: "produtos",
    });
    expect(screen.getByRole("status")).toHaveTextContent(/publicação iniciada/i);
  });
});
