import { afterEach, describe, expect, it } from "vitest";

import { exigir } from "@/test/carregar";
import { limparAmbienteTema } from "@/test/tema";

type Preferencia = "claro" | "escuro" | "sistema";
type Modulo = {
  CHAVE_TEMA: string;
  normalizarPreferencia: (valor: unknown) => Preferencia;
  resolverTema: (preferencia: Preferencia, computadorEscuro: boolean) => "claro" | "escuro";
};

afterEach(limparAmbienteTema);

describe("lib/tema", () => {
  it("test_sem_preferencia_ou_valor_invalido_resolve_para_sistema", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-004 AC-004
    const { CHAVE_TEMA, normalizarPreferencia, resolverTema } = await exigir<Modulo>("@/lib/tema");

    expect(CHAVE_TEMA).toBe("rag-pipeline-tema");
    for (const invalido of [null, undefined, "", "azul", "ESCURO", "dark", 3, {}]) {
      expect(normalizarPreferencia(invalido)).toBe("sistema");
    }
    for (const valido of ["claro", "escuro", "sistema"] as const) {
      expect(normalizarPreferencia(valido)).toBe(valido);
    }
    expect(resolverTema("sistema", true)).toBe("escuro");
    expect(resolverTema("sistema", false)).toBe("claro");
  });

  it("test_escolha_explicita_ignora_o_tema_do_computador", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-003 FR-004 AC-004
    const { resolverTema } = await exigir<Modulo>("@/lib/tema");

    expect(resolverTema("claro", true)).toBe("claro");
    expect(resolverTema("escuro", false)).toBe("escuro");
  });

  it("test_script_do_tema_usa_a_mesma_chave_e_cabe_em_1_kb", async () => {
    // SPECSFY: SPEC-0024 US-002 FR-005 NFR-001 AC-004
    const { CHAVE_TEMA, ...resto } = await exigir<Modulo & { scriptTema: () => string }>("@/lib/tema");

    const script = resto.scriptTema();
    expect(script).toContain(CHAVE_TEMA);
    expect(new TextEncoder().encode(script).length).toBeLessThan(1024);
  });
});
