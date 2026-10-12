import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: push }) }));

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import LoginForm from "@/features/auth/LoginForm";
import DataGridWorkspaces from "@/features/workspaces/DataGridWorkspaces";
import DataGridColecoes from "@/features/colecoes/DataGridColecoes";
import DataGridPessoas from "@/features/pessoas/DataGridPessoas";
import ListaConversas from "@/features/assistente/ListaConversas";
import ListaMensagens from "@/features/assistente/ListaMensagens";
import { useAssistente } from "@/features/assistente/useAssistente";
import DetalheEnvio from "@/features/envios/DetalheEnvio";

const resolvers: Array<(response: Response) => void> = [];
function adiarResposta() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => { resolve = done; });
  resolvers.push(resolve);
  vi.spyOn(globalThis, "fetch").mockReturnValue(promise);
  return resolve;
}

beforeEach(() => { push.mockReset(); sessionStorage.clear(); });
afterEach(async () => {
  await act(async () => { resolvers.splice(0).forEach((resolve) => resolve(new Response("{}"))); });
  cleanup();
  vi.restoreAllMocks();
});

describe("SPEC-0025 feedback local de processamento", () => {
  it("sinaliza só o botão ocupado e mantém a ação independente utilizável", async () => {
    // SPECSFY: SPEC-0025 US-001 FR-001 FR-002 NFR-001 AC-001
    const independente = vi.fn();
    const { container } = render(<><Button loading>Salvando…</Button><Button onClick={independente}>Outra ação</Button></>);
    const ocupado = screen.getByRole("button", { name: "Salvando…" });
    expect(ocupado.querySelector('[data-slot="spinner"]')).not.toBeNull();
    expect(ocupado).toBeDisabled();
    expect(ocupado).toHaveAttribute("aria-busy", "true");
    expect(container.querySelector('[data-slot="spinner"]')).toHaveAttribute("aria-hidden", "true");
    await userEvent.setup().click(screen.getByRole("button", { name: "Outra ação" }));
    expect(independente).toHaveBeenCalledOnce();
  });

  it("mostra espera de login até a falha e permite nova tentativa", async () => {
    // SPECSFY: SPEC-0025 US-001 FR-001 FR-002 AC-002
    const resolver = adiarResposta();
    const user = userEvent.setup();
    render(<LoginForm />);
    await user.type(screen.getByLabelText("E-mail"), "ana@example.test");
    await user.type(screen.getByLabelText("Senha"), "senha-de-teste-123");
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    const ocupado = screen.getByRole("button", { name: "Entrando…" });
    expect(ocupado.querySelector('[data-slot="spinner"]')).not.toBeNull();
    expect(ocupado).toHaveAttribute("aria-busy", "true");
    await act(async () => resolver(new Response('{"detail":"Indisponível"}', { status: 500 })));
    await waitFor(() => expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument());
    expect(screen.getByLabelText("E-mail")).toHaveValue("ana@example.test");
    expect(document.querySelector('[data-slot="spinner"]')).toBeNull();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it.each(["Workspaces", "Coleções", "Pessoas", "Conversas", "Mensagens"])("mostra círculo local na região de %s", (regiao) => {
    // SPECSFY: SPEC-0025 US-001 FR-001 NFR-001 AC-003
    const noop = vi.fn();
    const componentes = {
      Workspaces: <DataGridWorkspaces workspaces={[]} carregando />,
      "Coleções": <DataGridColecoes workspaceId="workspace-1" colecoes={[]} carregando />,
      Pessoas: <DataGridPessoas pessoas={[]} carregando />,
      Conversas: <ListaConversas conversas={[]} carregando erro={null} onAbrir={noop} onApagar={noop} onTentarNovamente={noop} />,
      Mensagens: <ListaMensagens mensagens={[]} carregando erro={null} />,
    };
    const { container } = render(componentes[regiao as keyof typeof componentes]);
    expect(container.querySelector('[data-slot="spinner"]')).not.toBeNull();
    expect(container.querySelector('[data-slot="spinner"]')).toHaveAttribute("aria-hidden", "true");
    expect(container.textContent).toMatch(/carregando|aguardando/i);
  });

  it("expõe espera de leitura de conversa e a encerra na resposta", async () => {
    // SPECSFY: SPEC-0025 US-001 FR-001 NFR-001 AC-003
    const resolver = adiarResposta();
    const { result } = renderHook(() => useAssistente());
    let operacao!: Promise<boolean>;
    act(() => { operacao = result.current.abrirConversa("conversa-1"); });
    expect(result.current.carregandoMensagens).toBe(true);
    await act(async () => {
      resolver(new Response('{"id":"conversa-1","titulo":"Teste","mensagens":[]}'));
      await operacao;
    });
    expect(result.current.carregandoMensagens).toBe(false);
    expect(result.current.conversaId).toBe("conversa-1");
  });

  it.each(["queued", "running"])("mantém círculo em %s e remove em ambos os estados terminais", (situacao) => {
    // SPECSFY: SPEC-0025 US-001 FR-001 FR-002 AC-004
    const execucao = { id: "env-1", colecao: { id: "colecao-1", nome: "manuais", workspace_id: "workspace-1" }, arquivos: ["a.md"], processamento: {}, criado_por: null, situacao, etapa: "indexando", previstos: 10, inseridos: 4, mantidos: 0, removidos: 0, erro: null, iniciado_em: "2026-10-05T12:00:00Z", concluido_em: null };
    const { container, rerender } = render(<DetalheEnvio envio={execucao} papel="owner" />);
    expect(container.querySelector('[data-slot="spinner"]')).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(/envio em andamento/i);
    for (const final of ["succeeded", "failed"]) {
      rerender(<DetalheEnvio envio={{ ...execucao, situacao: final }} papel="owner" />);
      expect(container.querySelector('[data-slot="spinner"]')).toBeNull();
      expect(screen.getByText("Previstos")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument();
    }
  });

  it("encerra o indicador após login bem sucedido sem bloquear outra ação", async () => {
    // SPECSFY: SPEC-0025 US-001 FR-001 FR-002 AC-005
    const resolver = adiarResposta();
    const independente = vi.fn();
    const user = userEvent.setup();
    render(<><LoginForm /><Button onClick={independente}>Ajuda</Button></>);
    await user.type(screen.getByLabelText("E-mail"), "ana@example.test");
    await user.type(screen.getByLabelText("Senha"), "senha-de-teste-123");
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(screen.getByRole("button", { name: "Entrando…" }).querySelector('[data-slot="spinner"]')).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "Ajuda" }));
    expect(independente).toHaveBeenCalledOnce();
    await act(async () => resolver(new Response(JSON.stringify({ token: "token-opaco", expira_em: "2026-10-06T12:00:00Z", pessoa: { id: "p1", nome: "Ana", email: "ana@example.test", papel: "owner", tenant_id: "t1", project_id: "p1", precisa_trocar_senha: false } }))));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/workspaces"));
    expect(document.querySelector('[data-slot="spinner"]')).toBeNull();
    expect(screen.getByRole("button", { name: "Entrar" })).not.toHaveAttribute("aria-busy", "true");
  });

  it("usa português, cor herdada e movimento reduzido sem foco no ícone", () => {
    // SPECSFY: SPEC-0025 US-001 FR-001 NFR-001 AC-006
    render(<Spinner />);
    const indicador = screen.getByRole("status", { name: "Carregando" });
    expect(indicador).toHaveClass("motion-reduce:animate-none");
    expect(indicador).not.toHaveAttribute("tabindex");
    expect(indicador).toHaveAttribute("stroke", "currentColor");
    expect(indicador).not.toHaveAttribute("aria-label", "Loading");
  });
});
