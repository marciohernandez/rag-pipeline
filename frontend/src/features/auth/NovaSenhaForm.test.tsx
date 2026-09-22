import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
}));

import { getToken, saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Modulo = { default: ComponentType };

beforeEach(() => {
  push.mockReset();
  replace.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-senha-pendente");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("NovaSenhaForm", () => {
  it("mostra a regra de 10 caracteres e o erro abaixo do campo com foco no primeiro erro", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-014 AC-006 AC-007 AC-026
    const { default: NovaSenhaForm } = await exigir<Modulo>("@/features/auth/NovaSenhaForm");
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const user = userEvent.setup();
    render(<NovaSenhaForm />);

    expect(screen.getByText(/10 caracteres/i)).toBeInTheDocument();
    const nova = screen.getByLabelText("Nova senha");
    const confirmacao = screen.getByLabelText(/confirmar nova senha/i);
    expect(nova).toHaveAttribute("autocomplete", "new-password");

    await user.type(nova, "curta");
    await user.type(confirmacao, "curta");
    await user.click(screen.getByRole("button", { name: /definir senha/i }));
    expect(nova).toHaveAttribute("aria-invalid", "true");
    expect(nova).toHaveFocus();
    expect(screen.getByText(/pelo menos 10 caracteres/i)).toBeInTheDocument();

    await user.clear(nova);
    await user.clear(confirmacao);
    await user.type(nova, "senha-longa-valida-1");
    await user.type(confirmacao, "outra-senha-longa-2");
    await user.click(screen.getByRole("button", { name: /definir senha/i }));
    expect(confirmacao).toHaveAttribute("aria-invalid", "true");
    expect(confirmacao).toHaveFocus();
    expect(screen.getByText(/não conferem/i)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("envia só a nova senha, mantém a sessão e segue aos Workspaces sem novo login", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-014 AC-006 AC-007
    const { default: NovaSenhaForm } = await exigir<Modulo>("@/features/auth/NovaSenhaForm");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const user = userEvent.setup();
    render(<NovaSenhaForm />);

    await user.type(screen.getByLabelText("Nova senha"), "senha-longa-valida-1");
    await user.type(screen.getByLabelText(/confirmar nova senha/i), "senha-longa-valida-1");
    await user.click(screen.getByRole("button", { name: /definir senha/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/workspaces"));
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/senha");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ nova_senha: "senha-longa-valida-1" });
    expect(getToken()).toBe("sessao-opaca-senha-pendente");
  });

  it("mostra o erro da política devolvido pelo servidor junto do campo, sem perder o que foi digitado", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-005 FR-014 AC-007 AC-026
    const { default: NovaSenhaForm } = await exigir<Modulo>("@/features/auth/NovaSenhaForm");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"A nova senha deve ser diferente da atual."}', {
        status: 422,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<NovaSenhaForm />);

    const nova = screen.getByLabelText("Nova senha");
    await user.type(nova, "senha-longa-valida-1");
    await user.type(screen.getByLabelText(/confirmar nova senha/i), "senha-longa-valida-1");
    await user.click(screen.getByRole("button", { name: /definir senha/i }));

    expect(await screen.findByText(/diferente da atual/i)).toBeInTheDocument();
    expect(nova).toHaveValue("senha-longa-valida-1");
    expect(push).not.toHaveBeenCalled();
  });
});

describe("Página Nova senha", () => {
  it("fica fora do shell: sem trilha nem navegação, apenas com a ação Sair", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-004 FR-014 AC-006 AC-026
    const { default: NovaSenhaPage } = await exigir<Modulo>("@/app/nova-senha/page");
    const user = userEvent.setup();
    render(<NovaSenhaPage />);

    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Workspaces" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /sair/i }));
    expect(getToken()).toBeNull();
    expect(replace).toHaveBeenCalledWith("/login");
  });
});
