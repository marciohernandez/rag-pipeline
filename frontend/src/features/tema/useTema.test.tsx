import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";

import { exigir } from "@/test/carregar";
import { instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

type Preferencia = "claro" | "escuro" | "sistema";
type Modulo = {
  useTema: () => { preferencia: Preferencia; escolher: (preferencia: Preferencia) => void };
};

const html = () => document.documentElement;

beforeEach(() => {
  html().classList.remove("dark");
});

afterEach(() => {
  cleanup();
  limparAmbienteTema();
});

describe("useTema", () => {
  it("test_sistema_acompanha_o_computador_e_reage_a_mudanca", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-003 AC-003
    const computador = instalarMatchMedia(false);
    const { useTema } = await exigir<Modulo>("@/features/tema/useTema");

    const { result } = renderHook(() => useTema());
    expect(result.current.preferencia).toBe("sistema");
    expect(html()).not.toHaveClass("dark");

    act(() => computador.definirEscuro(true));
    expect(html()).toHaveClass("dark");

    act(() => computador.definirEscuro(false));
    expect(html()).not.toHaveClass("dark");
  });

  it("test_claro_e_escuro_fixados_ignoram_a_mudanca_do_computador", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-003 AC-003
    const computador = instalarMatchMedia(false);
    const { useTema } = await exigir<Modulo>("@/features/tema/useTema");

    const { result } = renderHook(() => useTema());
    act(() => result.current.escolher("claro"));
    act(() => computador.definirEscuro(true));
    expect(html()).not.toHaveClass("dark");

    act(() => result.current.escolher("escuro"));
    act(() => computador.definirEscuro(false));
    expect(html()).toHaveClass("dark");
    expect(localStorage.getItem("rag-pipeline-tema")).toBe("escuro");
  });

  it("test_valor_salvo_desconhecido_vale_sistema_sem_regravar", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-004 AC-003
    instalarMatchMedia(true);
    localStorage.setItem("rag-pipeline-tema", "azul");
    const { useTema } = await exigir<Modulo>("@/features/tema/useTema");

    const { result } = renderHook(() => useTema());
    expect(result.current.preferencia).toBe("sistema");
    expect(html()).toHaveClass("dark");
    expect(localStorage.getItem("rag-pipeline-tema")).toBe("azul");
  });

  it("test_armazenamento_indisponivel_aplica_na_sessao_sem_erro", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 FR-004 NFR-004 AC-005
    instalarMatchMedia(false);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("bloqueado", "SecurityError");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("bloqueado", "SecurityError");
    });
    const erros = vi.spyOn(console, "error").mockImplementation(() => {});
    const { useTema } = await exigir<Modulo>("@/features/tema/useTema");

    const { result, unmount } = renderHook(() => useTema());
    expect(() => act(() => result.current.escolher("escuro"))).not.toThrow();
    expect(html()).toHaveClass("dark");
    expect(result.current.preferencia).toBe("escuro");
    expect(erros).not.toHaveBeenCalled();

    unmount();
    html().classList.remove("dark");
    const recarregado = renderHook(() => useTema());
    expect(recarregado.result.current.preferencia).toBe("sistema");
    expect(html()).not.toHaveClass("dark");
  });

  it("test_sem_matchmedia_usa_o_tema_claro", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-003 FR-004 NFR-004 AC-005
    vi.stubGlobal("matchMedia", undefined);
    const { useTema } = await exigir<Modulo>("@/features/tema/useTema");

    const { result } = renderHook(() => useTema());
    expect(result.current.preferencia).toBe("sistema");
    expect(html()).not.toHaveClass("dark");
  });
});
