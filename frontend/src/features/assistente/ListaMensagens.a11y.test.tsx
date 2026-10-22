import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import { exigir } from "@/test/carregar";
import { mensagem } from "./_apoio";

type Modulo = typeof import("./ListaMensagens");

afterEach(cleanup);

describe("ListaMensagens — tecnologia assistiva", () => {
  it("test_carregando_e_resposta_sao_anunciados_em_regiao_viva", async () => {
    // SPECSFY: SPEC-0021 US-001 NFR-003 AC-026
    const { default: ListaMensagens } = await exigir<Modulo>("@/features/assistente/ListaMensagens");
    const pergunta = mensagem("pessoa", "Qual splitter usar?");
    const { container, rerender } = render(
      <ListaMensagens mensagens={[pergunta]} carregando erro={null} />,
    );

    const viva = container.querySelector('[aria-live="polite"]');
    expect(viva, "região aria-live polite").not.toBeNull();
    expect(viva!.textContent).toMatch(/aguardando|digitando|carregando|pensando/i);

    rerender(
      <ListaMensagens
        mensagens={[pergunta, mensagem("assistente", "Prefira dividir por cabeçalhos.")]}
        carregando={false}
        erro={null}
      />,
    );
    expect(container.querySelector('[aria-live="polite"]')!.textContent).toContain(
      "Prefira dividir por cabeçalhos.",
    );

    rerender(
      <ListaMensagens
        mensagens={[pergunta]}
        carregando={false}
        erro="Não foi possível obter a resposta agora."
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Não foi possível obter a resposta agora.");
  });

  it("anuncia a resposta de não encontrei pela região viva e sem violações do axe", async () => {
    // SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-003 AC-011
    const { default: ListaMensagens } = await exigir<Modulo>("@/features/assistente/ListaMensagens");
    const aviso = "Não encontrei isso nos documentos do seu projeto.";
    const { container } = render(
      <ListaMensagens
        mensagens={[
          mensagem("pessoa", "Qual a garantia do modelo X?"),
          mensagem("assistente", "A garantia é de 24 meses.", {
            fontes: [
              {
                tipo: "documento",
                rotulo: "manual.md — Manuais",
                colecao_id: "c1",
                documento: "manual.md",
                rota: "/workspaces/w1/colecoes/c1",
              },
            ],
          }),
          mensagem("pessoa", "Qual a política de viagens?"),
          mensagem("assistente", aviso),
        ]}
        carregando={false}
        erro={null}
      />,
    );

    const viva = container.querySelector('[role="log"][aria-live="polite"]');
    expect(viva, "região role=log com aria-live polite").not.toBeNull();
    expect(viva!.textContent).toContain(aviso);
    expect(viva!.textContent).toContain("manual.md — Manuais");
    expect(container.querySelectorAll('[aria-label="Fontes citadas"]')).toHaveLength(1);

    const axe = (await import("axe-core")).default;
    const resultado = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(resultado.violations.map((v) => v.id)).toEqual([]);
  });
});
