import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
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
    for (const acao of [/editar/i, /redefinir senha/i, /desativar/i]) {
      expect(screen.getByRole("button", { name: acao })).toBeInTheDocument();
    }
    expect(screen.queryByRole("button", { name: /apagar|excluir/i })).not.toBeInTheDocument();
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
  });
});
