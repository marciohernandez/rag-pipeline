import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Pessoa {
  id: string;
  nome: string;
  email: string;
  papel: string;
}
interface Props {
  open: boolean;
  pessoa?: Pessoa;
  podeAtribuirOwner?: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onSaved?: (pessoa: Pessoa) => void;
}
type Modulo = { default: ComponentType<Props> };

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-owner");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("PessoaFormSheet", () => {
  it("cria a pessoa em painel lateral com nome, e-mail, papel e senha inicial", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 AC-011 AC-012 AC-013 AC-025
    const { default: PessoaFormSheet } = await exigir<Modulo>("@/features/pessoas/PessoaFormSheet");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"id":"pessoa-9","nome":"Carla","email":"carla@exemplo.com","papel":"member"}', {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(<PessoaFormSheet open onSaved={onSaved} podeAtribuirOwner />);

    expect(screen.getByRole("dialog", { name: /nova pessoa/i })).toBeInTheDocument();
    expect(screen.getByText(/canal seguro/i)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Nome"), "Carla");
    await user.type(screen.getByLabelText("E-mail"), "carla@exemplo.com");
    await user.selectOptions(screen.getByLabelText("Papel"), "member");
    await user.type(screen.getByLabelText("Senha inicial"), "senha-inicial-123");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/pessoas");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({
      nome: "Carla",
      email: "carla@exemplo.com",
      papel: "member",
      senha_inicial: "senha-inicial-123",
    });
  });

  it("oferece a opção owner só para quem pode atribuí-la", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 AC-011 AC-013 AC-025
    const { default: PessoaFormSheet } = await exigir<Modulo>("@/features/pessoas/PessoaFormSheet");
    const { rerender } = render(<PessoaFormSheet open podeAtribuirOwner={false} />);
    const opcoes = () => screen.getByLabelText("Papel").querySelectorAll("option");

    expect([...opcoes()].map((o) => o.value)).not.toContain("owner");
    rerender(<PessoaFormSheet open podeAtribuirOwner />);
    expect([...opcoes()].map((o) => o.value)).toContain("owner");
  });

  it("preserva os campos e foca o e-mail quando o servidor recusa por e-mail duplicado", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 AC-011 AC-012 AC-025
    const { default: PessoaFormSheet } = await exigir<Modulo>("@/features/pessoas/PessoaFormSheet");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Este e-mail já está em uso. Use outro e-mail."}', {
        status: 409,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<PessoaFormSheet open podeAtribuirOwner />);

    await user.type(screen.getByLabelText("Nome"), "Carla");
    const email = screen.getByLabelText("E-mail");
    await user.type(email, "carla@exemplo.com");
    await user.type(screen.getByLabelText("Senha inicial"), "senha-inicial-123");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await screen.findByText(/já está em uso/i)).toBeInTheDocument();
    expect(email).toHaveAttribute("aria-invalid", "true");
    expect(email).toHaveFocus();
    expect(screen.getByLabelText("Nome")).toHaveValue("Carla");
    expect(email).toHaveValue("carla@exemplo.com");
    expect(screen.getByLabelText("Senha inicial")).toHaveValue("senha-inicial-123");
  });

  it("edita nome, e-mail e papel da mesma pessoa por PATCH, sem pedir senha", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 AC-011 AC-025
    const { default: PessoaFormSheet } = await exigir<Modulo>("@/features/pessoas/PessoaFormSheet");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"id":"pessoa-1","nome":"Ana Maria","email":"ana@exemplo.com","papel":"admin"}', {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(
      <PessoaFormSheet
        open
        podeAtribuirOwner
        pessoa={{ id: "pessoa-1", nome: "Ana", email: "ana@exemplo.com", papel: "member" }}
      />,
    );

    expect(screen.queryByLabelText("Senha inicial")).not.toBeInTheDocument();
    await user.clear(screen.getByLabelText("Nome"));
    await user.type(screen.getByLabelText("Nome"), "Ana Maria");
    await user.selectOptions(screen.getByLabelText("Papel"), "admin");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/pessoas/pessoa-1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).toMatchObject({ nome: "Ana Maria", papel: "admin" });
  });
});
