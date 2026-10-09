import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Valores {
  novaColecao?: string;
  conexaoEmbeddingsId?: string;
  conexaoVectorStoreId?: string;
  destino?: { batch_size: number };
}
interface Props {
  resumo: { arquivos: number; chunks: number };
  workspaceId: string;
  onPublicar: (valores: Valores) => Promise<{ envio_id: string; colecao_id: string }>;
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

function simular(conexoes: unknown[]) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.includes("/colecoes")) return json([]);
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
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    expect(await screen.findByText(/nenhuma conexão ativa/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /conexões/i })).toHaveAttribute("href", "/conexoes");
    expect(screen.getByRole("button", { name: /publicar/i })).toBeDisabled();
  });

  it("mostra Alert com Tentar novamente na falha e mantém o preenchimento", async () => {
    // SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant]);
    const onPublicar = vi.fn().mockRejectedValue(new Error("falha de rede"));
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={onPublicar} />);

    await user.selectOptions(await screen.findByLabelText(/conexão de embeddings/i), "con-e");
    await user.selectOptions(screen.getByLabelText(/conexão do qdrant/i), "con-q");
    const colecao = await screen.findByLabelText(/nome da coleção/i);
    await user.type(colecao, "produtos");
    await user.click(screen.getByRole("button", { name: /publicar/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
    expect(colecao).toHaveValue("produtos");
  });

  it("depois de publicar leva ao envio e anuncia o resultado", async () => {
    // SPECSFY: SPEC-0026 US-003 FR-010 FR-014 AC-019
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant]);
    const onPublicar = vi.fn().mockResolvedValue({ envio_id: "env-9", colecao_id: "col-9" });
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={onPublicar} />);

    await user.type(await screen.findByLabelText(/nome da coleção/i), "produtos");
    await user.click(screen.getByRole("button", { name: /publicar/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/envios/env-9"));
    // SPEC-0029 acrescentou o destino escolhido na Publicação; SPEC-0030 tirou o modo de sincronização.
    expect(onPublicar).toHaveBeenCalledWith({
      conexaoEmbeddingsId: "con-e",
      conexaoVectorStoreId: "con-q",
      novaColecao: "produtos",
      destino: { batch_size: 50 },
    });
    expect(screen.getByText(/publicação iniciada/i)).toHaveAttribute("role", "status");
  });
});

describe("EtapaPublicacao — destino e conexão no fluxo (SPEC-0029)", () => {
  const novaConexao = {
    id: "con-nova", nome: "OpenAI teste", tipo: "embeddings_openai", situacao: "ativa",
    configuracao: { modelo: "text-embedding-3-small", dimensoes: 1536 },
  };

  function simularCadastro(teste: { sucesso: boolean; mensagem: string }) {
    let cadastrada = false;
    const espiao = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/colecoes")) return json([]);
      if (url.endsWith("/api/v1/conexoes") && init?.method === "POST") {
        cadastrada = true;
        return json({ ...novaConexao, teste }, 201);
      }
      if (url.includes("/api/v1/conexoes")) return json(cadastrada ? [novaConexao, qdrant] : [qdrant]);
      throw new Error(`URL inesperada: ${url}`);
    });
    return espiao;
  }

  async function preencherNovaConexao(user: ReturnType<typeof userEvent.setup>) {
    const painel = await screen.findByRole("dialog", { name: /nova conexão/i });
    await user.type(within(painel).getByLabelText("Nome"), "OpenAI teste");
    await user.clear(within(painel).getByLabelText("Modelo"));
    await user.type(within(painel).getByLabelText("Modelo"), "text-embedding-3-small");
    await user.clear(within(painel).getByLabelText("Dimensões"));
    await user.type(within(painel).getByLabelText("Dimensões"), "1536");
    await user.type(within(painel).getByLabelText("Chave"), "sk-teste");
    await user.click(within(painel).getByRole("button", { name: /salvar/i }));
    return painel;
  }

  it("mostra o padrão do lote e não oferece modo de sincronização", async () => {
    // SPECSFY: SPEC-0029 US-003 FR-006 NFR-003 AC-013
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([embeddings, qdrant]);
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    await user.click(await screen.findByRole("button", { name: /avançado/i }));
    expect(screen.getByLabelText(/tamanho do lote de embeddings/i)).toHaveValue(50);
    expect(screen.queryByLabelText(/modo de sincronização/i)).toBeNull();
    expect(screen.queryByText(/mirror|append/i)).toBeNull();
  });

  it("cadastra conexão no painel sem sair da Publicação", async () => {
    // SPECSFY: SPEC-0029 US-005 FR-010 NFR-003 AC-022
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simularCadastro({ sucesso: true, mensagem: "Conexão testada com sucesso." });
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    await user.click(await screen.findByRole("button", { name: /cadastrar conexão/i }));
    await preencherNovaConexao(user);

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(await screen.findByLabelText(/conexão de embeddings/i)).toHaveValue("con-nova");
    expect(screen.getByText("Conexão testada com sucesso.")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("cancelar ou falhar no painel preserva o fluxo", async () => {
    // SPECSFY: SPEC-0029 US-005 FR-009 FR-010 AC-023
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    const espiao = simularCadastro({ sucesso: false, mensagem: "O servidor exige uma chave de API." });
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    await user.click(await screen.findByRole("button", { name: /cadastrar conexão/i }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: /cancelar/i }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(espiao.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);

    await user.click(screen.getByRole("button", { name: /cadastrar conexão/i }));
    const painel = await preencherNovaConexao(user);
    expect(await within(painel).findByText(/conexão salva, mas o teste falhou: o servidor exige uma chave de api/i)).toBeInTheDocument();
    expect(within(painel).getByRole("button", { name: /editar/i })).toBeInTheDocument();
    await user.click(within(within(painel).getByRole("alert")).getByRole("button", { name: /fechar/i }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.getByRole("option", { name: /openai teste \(teste falhou\)/i })).toBeInTheDocument();
  });

  it("reaproveita o formulário de conexões no painel", async () => {
    // SPECSFY: SPEC-0029 US-005 FR-009 FR-010 AC-026
    const { default: EtapaPublicacao } = await exigir<Modulo>("@/features/ingestao/EtapaPublicacao");
    simular([qdrant]);
    const user = userEvent.setup();
    render(<EtapaPublicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    await user.click(await screen.findByRole("button", { name: /cadastrar conexão/i }));
    const painel = await screen.findByRole("dialog", { name: /nova conexão/i });

    for (const rotulo of ["Nome", "Tipo", "Modelo", "Dimensões", "URL base (opcional)", "Chave"]) {
      expect(within(painel).getByLabelText(rotulo)).toBeInTheDocument();
    }
  });
});

describe("EtapaPublicacao — coleções (SPEC-0030)", () => {
  it("pré-seleciona a coleção e trava as conexões na Publicação", async () => {
    // SPECSFY: SPEC-0030 US-001 FR-002 FR-003 FR-006 FR-007 AC-002
    interface PropsColecao {
      resumo: { arquivos: number; chunks: number };
      workspaceId: string;
      colecaoInicial?: string;
      onPublicar: (valores: Record<string, unknown>) => Promise<{ envio_id: string; colecao_id: string }>;
    }
    const { default: Publicacao } = await exigir<{ default: ComponentType<PropsColecao> }>(
      "@/features/ingestao/EtapaPublicacao",
    );
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/workspaces/w1/colecoes"))
        return json([{ id: "c1", nome: "manuais", documentos: 1, chunks: 4, ultimo_envio_em: null }]);
      if (url.endsWith("/api/v1/colecoes/c1"))
        return json({
          id: "c1", nome: "manuais", dimensao: 1536,
          conexao_embeddings: { id: "con-e", nome: "OpenAI principal" },
          conexao_vector_store: { id: "con-q", nome: "Qdrant produção" },
        });
      if (url.includes("/api/v1/ingestao/dimensao")) return json({ embeddings: 1536, colecao: 1536, compativel: true });
      if (url.includes("/api/v1/conexoes")) return json([embeddings, qdrant]);
      throw new Error(`URL inesperada: ${url}`);
    });
    const onPublicar = vi.fn().mockResolvedValue({ envio_id: "e1", colecao_id: "c1" });
    const user = userEvent.setup();
    render(<Publicacao resumo={resumo} workspaceId="w1" colecaoInicial="c1" onPublicar={onPublicar} />);

    const grupo = await screen.findByRole("radiogroup", { name: /coleção/i });
    expect(within(grupo).getByRole("radio", { name: "Coleção existente" })).toBeChecked();
    expect(within(grupo).getByRole("radio", { name: "Nova coleção" })).not.toBeChecked();
    expect(await screen.findByText("OpenAI principal")).toBeInTheDocument();
    expect(screen.getByText("Qdrant produção")).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: /conexão/i })).toBeNull();
    expect(screen.queryByText(/modo de sincronização|sync_mode|mirror|append/i)).toBeNull();

    await user.click(screen.getByRole("button", { name: /publicar/i }));

    expect(onPublicar).toHaveBeenCalledWith(expect.objectContaining({ colecaoId: "c1" }));
  });

  it("mostra o nome que a coleção terá no Qdrant ao digitar", async () => {
    // SPECSFY: SPEC-0030 US-001 FR-001 FR-002 NFR-003 AC-023
    const { default: Publicacao } = await exigir<{ default: ComponentType<Props> }>(
      "@/features/ingestao/EtapaPublicacao",
    );
    simular([embeddings, qdrant]);
    const user = userEvent.setup();
    render(<Publicacao resumo={resumo} workspaceId="w1" onPublicar={vi.fn()} />);

    const campo = await screen.findByLabelText(/nome da coleção/i);
    await user.type(campo, "Manuais Técnicos 2026");

    expect(screen.getByText("Nome no Qdrant: Manuais-Tecnicos-2026")).toBeInTheDocument();
    expect(screen.getByText(/não muda depois/i)).toBeInTheDocument();

    await user.clear(campo);
    await user.type(campo, "!!!");
    expect(screen.getByText(/precisa ter ao menos uma letra ou número/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /publicar/i })).toBeDisabled();
  });
});
