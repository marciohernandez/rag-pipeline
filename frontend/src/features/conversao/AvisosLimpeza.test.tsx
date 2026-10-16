import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { exigir } from "@/test/carregar";

afterEach(cleanup);

type Props = { workspaceId: string; iaPermitida: boolean; dominioConfirmado: boolean };

async function montar(props: Props) {
  const { default: Avisos } = await exigir<{ default: ComponentType<Props> }>(
    "@/features/conversao/AvisosLimpeza",
  );
  render(<Avisos {...props} />);
}

it("explica que a limpeza seguirá só com regras fixas e leva ao Workspace", async () => {
  // SPECSFY: SPEC-0037 US-005 FR-008 NFR-004 AC-015
  await montar({ workspaceId: "w1", iaPermitida: false, dominioConfirmado: true });

  const aviso = screen.getByRole("status");
  expect(aviso).toHaveTextContent(/somente as regras fixas|só as regras fixas/i);
  expect(aviso).toHaveTextContent(/IA externa/i);
  const link = screen.getByRole("link", { name: /Domínio da empresa/i });
  expect(link).toHaveAttribute("href", expect.stringContaining("/workspaces/w1"));
});

it("com o domínio não confirmado avisa que a limpeza não começa", async () => {
  // SPECSFY: SPEC-0037 US-005 FR-008 NFR-004 AC-015
  await montar({ workspaceId: "w1", iaPermitida: true, dominioConfirmado: false });

  expect(screen.getByRole("status")).toHaveTextContent(/não começa|confirmar o domínio/i);
  expect(screen.getByRole("button", { name: "Confirmar domínio" })).toBeInTheDocument();
});

it("sem aviso quando tudo está configurado", async () => {
  // SPECSFY: SPEC-0037 US-005 FR-008 NFR-004 AC-015
  await montar({ workspaceId: "w1", iaPermitida: true, dominioConfirmado: true });

  expect(screen.queryByRole("status")).toBeNull();
});
