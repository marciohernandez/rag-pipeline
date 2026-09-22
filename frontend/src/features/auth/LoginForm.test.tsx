import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Importado depois dos mocks; o componente ainda não existe (RED de T008/T009).
import LoginForm from "@/features/auth/LoginForm";
import { getToken } from "@/lib/session";
import { exigir } from "@/test/carregar";

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LoginForm", () => {
  it("guarda o token em sessionStorage e leva aos Workspaces quando o backend aceita", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-001 (SPEC-0013)
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("[]", { status: 200, headers: { "content-type": "application/json" } }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(
      screen.getByLabelText(/token de demonstra/i),
      "token-demo-owner",
    );
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => expect(getToken()).toBe("token-demo-owner"));
    expect(push).toHaveBeenCalledWith("/workspaces");
  });

  it("rejeita token inválido com erro genérico, preserva o campo e não guarda sessão", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-002 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Token inválido"}', {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    const campo = screen.getByLabelText(/token de demonstra/i);
    await user.type(campo, "token-errado");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("alert").textContent ?? "").not.toMatch(/inválido/i);
    expect(campo).toHaveValue("token-errado");
    expect(getToken()).toBeNull();
    expect(push).not.toHaveBeenCalled();
  });
});

// --------------------------------------------------------------------------
// SPEC-0020 — login por e-mail e senha (fase RED).
// --------------------------------------------------------------------------

function respostaLogin(pendente: boolean) {
  return new Response(
    JSON.stringify({
      token: "sessao-opaca-nova",
      expira_em: "2026-09-22T10:00:00Z",
      pessoa: {
        id: "pessoa-1",
        nome: "Ana Souza",
        email: "ana@exemplo.com",
        papel: "owner",
        tenant_id: "tenant-1",
        project_id: "projeto-1",
        precisa_trocar_senha: pendente,
      },
    }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
}

describe("LoginForm por e-mail e senha", () => {
  it("envia e-mail e senha, guarda a sessão e leva aos Workspaces", async () => {
    // SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(respostaLogin(false));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "ana@exemplo.com");
    await user.type(screen.getByLabelText("Senha"), "senha-de-teste-123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => expect(getToken()).toBe("sessao-opaca-nova"));
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/login");
    expect(JSON.parse(String(init.body))).toEqual({
      email: "ana@exemplo.com",
      senha: "senha-de-teste-123",
    });
    expect(push).toHaveBeenCalledWith("/workspaces");
  });

  it("leva à tela Nova senha quando a senha ainda está pendente", async () => {
    // SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respostaLogin(true));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "ana@exemplo.com");
    await user.type(screen.getByLabelText("Senha"), "senha-inicial-123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/nova-senha"));
  });

  it("recusa com mensagem genérica, preserva o e-mail, limpa a senha e foca o primeiro campo", async () => {
    // SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Credenciais inválidas."}', {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    const email = screen.getByLabelText("E-mail");
    const senha = screen.getByLabelText("Senha");
    await user.type(email, "ana@exemplo.com");
    await user.type(senha, "senha-errada-123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(email).toHaveValue("ana@exemplo.com");
    expect(senha).toHaveValue("");
    expect(email).toHaveFocus();
    expect(getToken()).toBeNull();
    expect(push).not.toHaveBeenCalled();
  });

  it("mostra a mensagem própria de bloqueio temporário sem revelar o tempo restante", async () => {
    // SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Conta bloqueada temporariamente. Tente novamente mais tarde."}', {
        status: 429,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "ana@exemplo.com");
    await user.type(screen.getByLabelText("Senha"), "senha-de-teste-123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent ?? "").toMatch(/bloqueada temporariamente/i);
    expect(alerta.textContent ?? "").not.toMatch(/\d+ ?(minutos|segundos)/i);
  });

  it("orienta quem esqueceu a senha a pedir a redefinição a um owner ou admin", async () => {
    // SPECSFY: SPEC-0020 US-001 FR-001 FR-014 AC-023 AC-026
    render(<LoginForm />);

    expect(screen.getByText(/esqueceu a senha/i)).toBeInTheDocument();
    expect(screen.getByText(/owner ou admin/i)).toBeInTheDocument();
  });

  it("mostra o aviso de sessão terminada depois de um 401 em outra tela", async () => {
    // SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023
    const sessao = await exigir<{ avisarSessaoTerminada: () => void }>("@/lib/session");
    expect(typeof sessao.avisarSessaoTerminada).toBe("function");
    sessao.avisarSessaoTerminada();
    render(<LoginForm />);

    expect(screen.getByText("Sua sessão terminou. Entre novamente.")).toBeInTheDocument();
  });

  it("usa os campos acessíveis: rótulos visíveis e autocomplete de usuário e senha atual", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-014 FR-015 NFR-005 AC-026
    render(<LoginForm />);

    expect(screen.getByLabelText("E-mail")).toHaveAttribute("autocomplete", "username");
    expect(screen.getByLabelText("Senha")).toHaveAttribute("autocomplete", "current-password");
    expect(screen.getByLabelText("Senha")).toHaveAttribute("type", "password");
  });
});
