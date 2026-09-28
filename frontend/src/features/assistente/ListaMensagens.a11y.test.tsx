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
});
