import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "pessoa-1" }),
  useRouter: () => ({ push, replace: vi.fn() }),
}));

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Modulo = { default: ComponentType };

const ana = {
  id: "pessoa-1",
  nome: "Ana Souza",
  email: "ana.souza.com.um.endereco.bem.longo@exemplo.com.br",
  papel: "owner",
  situacao: "ativa",
  precisa_trocar_senha: false,
  criada_em: "2026-09-20T10:00:00Z",
  criada_por: { id: "pessoa-0", nome: "Marcio", desativada: false },
};

function json(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function mockarApi(papel: "owner" | "member") {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) => {
    const url = String(entrada);
    if (url.includes("/api/v1/auth/me")) {
      return json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel, tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false });
    }
    if (url.endsWith("/api/v1/pessoas/pessoa-1")) return json(ana);
    if (url.endsWith("/api/v1/pessoas")) return json([ana]);
    return json({}, 404);
  });
}

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-pessoas");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Rota Pessoas", () => {
  it("owner vê o cabeçalho com Nova pessoa e a lista de pessoas do tenant", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 NFR-005 AC-011 AC-014 AC-025
    const { default: PessoasPage } = await exigir<Modulo>("@/app/(autenticado)/pessoas/page");
    mockarApi("owner");
    render(<PessoasPage />);

    expect(await screen.findByRole("heading", { name: "Pessoas" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /nova pessoa/i })).toBeInTheDocument();
    expect(await screen.findByRole("row", { name: /ana souza/i })).toBeInTheDocument();
  });

  it("só mostra a ação Nova pessoa depois de confirmar a permissão", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-010 FR-015 AC-014 AC-025
    const { default: PessoasPage } = await exigir<Modulo>("@/app/(autenticado)/pessoas/page");
    let concluirIdentidade!: (resposta: Response) => void;
    vi.spyOn(globalThis, "fetch")
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { concluirIdentidade = resolve; }))
      .mockResolvedValueOnce(json([]));
    render(<PessoasPage />);

    expect(screen.queryByRole("button", { name: /nova pessoa/i })).not.toBeInTheDocument();
    concluirIdentidade(json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel: "owner", tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false }));
    expect(await screen.findByRole("button", { name: /nova pessoa/i })).toBeInTheDocument();
  });

  it("oferece tentar novamente após erro sem manter uma grade enganosa", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-010 FR-015 NFR-005 AC-014 AC-025
    const { default: PessoasPage } = await exigir<Modulo>("@/app/(autenticado)/pessoas/page");
    let chamadasPessoas = 0;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) => {
      const url = String(entrada);
      if (url.includes("/api/v1/auth/me")) {
        return json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel: "owner", tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false });
      }
      if (url.endsWith("/api/v1/pessoas")) {
        chamadasPessoas += 1;
        return chamadasPessoas === 1 ? json({ detail: "Falha interna." }, 500) : json([ana]);
      }
      return json({}, 404);
    });
    const user = userEvent.setup();
    render(<PessoasPage />);

    expect(await screen.findByText(/não foi possível carregar as pessoas/i)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));

    expect(await screen.findByRole("row", { name: /ana souza/i })).toBeInTheDocument();
    expect(fetchSpy.mock.calls.filter(([url]) => String(url).endsWith("/api/v1/pessoas"))).toHaveLength(2);
  });

  it("member que abre a rota por endereço vê explicação curta, sem dados e sem chamar a API de pessoas", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 NFR-005 AC-014 AC-025
    const { default: PessoasPage } = await exigir<Modulo>("@/app/(autenticado)/pessoas/page");
    const fetchSpy = mockarApi("member");
    render(<PessoasPage />);

    expect(await screen.findByText(/permissão/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /workspaces/i })).toBeInTheDocument();
    expect(screen.queryByText("Ana Souza")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /nova pessoa/i })).not.toBeInTheDocument();
    const urls = fetchSpy.mock.calls.map(([u]) => String(u));
    expect(urls.some((u) => u.endsWith("/api/v1/pessoas"))).toBe(false);
  });
});

describe("Rota Pessoa (detalhe)", () => {
  it("mostra nome, situação, ações e os atributos em lista de detalhes com e-mail longo quebrando", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-011 AC-014 AC-025
    const { default: PessoaDetalhePage } = await exigir<Modulo>(
      "@/app/(autenticado)/pessoas/[id]/page",
    );
    mockarApi("owner");
    render(<PessoaDetalhePage />);

    expect(await screen.findByRole("heading", { name: "Ana Souza" })).toBeInTheDocument();
    expect(screen.getByText(/ana\.souza\.com\.um/i)).toBeInTheDocument();
    expect(screen.getByText("Marcio")).toBeInTheDocument();
    expect(screen.getByText("Owner")).toBeInTheDocument();
    for (const acao of [/editar/i, /redefinir senha/i, /desativar/i]) {
      expect(screen.getByRole("button", { name: acao })).toBeInTheDocument();
    }
    expect(screen.queryByRole("button", { name: /apagar|excluir/i })).not.toBeInTheDocument();
  });

  it("mostra skeleton sem dados ou ações enquanto valida a permissão e carrega o detalhe", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-011 AC-014 AC-025
    const { default: PessoaDetalhePage } = await exigir<Modulo>(
      "@/app/(autenticado)/pessoas/[id]/page",
    );
    let concluirIdentidade!: (resposta: Response) => void;
    vi.spyOn(globalThis, "fetch")
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { concluirIdentidade = resolve; }))
      .mockResolvedValueOnce(json(ana));
    render(<PessoaDetalhePage />);

    expect(screen.getByRole("status", { name: /carregando detalhes da pessoa/i })).toBeInTheDocument();
    expect(screen.queryByText(ana.email)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /editar|desativar|redefinir/i })).not.toBeInTheDocument();

    concluirIdentidade(json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel: "owner", tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false }));
    expect(await screen.findByRole("heading", { name: "Ana Souza" })).toBeInTheDocument();
  });

  it("recusa member por endereço sem buscar nem revelar a pessoa", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 NFR-005 AC-014 AC-025
    const { default: PessoaDetalhePage } = await exigir<Modulo>(
      "@/app/(autenticado)/pessoas/[id]/page",
    );
    const fetchSpy = mockarApi("member");
    render(<PessoaDetalhePage />);

    expect(await screen.findByText(/não tem permissão/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voltar aos workspaces/i })).toHaveAttribute(
      "href",
      "/workspaces",
    );
    expect(screen.queryByText(ana.nome)).not.toBeInTheDocument();
    expect(screen.queryByText(ana.email)).not.toBeInTheDocument();
    expect(fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/pessoas/pessoa-1"))).toBe(false);
  });

  it("identifica a autoria desativada sem depender apenas de estilo", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-011 AC-025
    const { default: PessoaDetalhePage } = await exigir<Modulo>(
      "@/app/(autenticado)/pessoas/[id]/page",
    );
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me")
        ? json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel: "admin", tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false })
        : json({ ...ana, criada_por: { ...ana.criada_por, desativada: true } }),
    );
    render(<PessoaDetalhePage />);

    expect(await screen.findByText("Marcio (desativada)")).toBeInTheDocument();
  });

  it("mostra a mensagem de não encontrada quando a pessoa é de outro tenant", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 AC-014 AC-025
    const { default: PessoaDetalhePage } = await exigir<Modulo>(
      "@/app/(autenticado)/pessoas/[id]/page",
    );
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/auth/me")
        ? json({ id: "eu", nome: "Eu", email: "eu@exemplo.com", papel: "owner", tenant_id: "tenant-2", project_id: "projeto-2", precisa_trocar_senha: false })
        : json({ detail: "Pessoa não encontrada." }, 404),
    );
    render(<PessoaDetalhePage />);

    await waitFor(() => expect(screen.getByText(/não encontrada/i)).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /voltar para pessoas/i })).toHaveAttribute(
      "href",
      "/pessoas",
    );
  });
});
