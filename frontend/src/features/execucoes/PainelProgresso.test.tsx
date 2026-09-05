import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Componente ainda não existe (RED de T019/T020/T021/T022).
import PainelProgresso from "@/features/execucoes/PainelProgresso";

const execucao = (over: Record<string, unknown> = {}) => ({
  id: "exec-1",
  base_id: "base-1",
  situacao: "running",
  etapa: "indexando",
  previstos: 10,
  inseridos: 4,
  mantidos: 0,
  removidos: 0,
  erro: null,
  iniciado_em: "2026-09-05T12:00:00Z",
  concluido_em: null,
  ...over,
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("PainelProgresso", () => {
  it("mostra etapa, status e contagens previstos/inseridos/mantidos/removidos", () => {
    // SPECSFY: US-003 FR-005 FR-003 AC-008 (SPEC-0013)
    render(<PainelProgresso execucao={execucao({ situacao: "succeeded", etapa: "concluido", inseridos: 10 })} />);

    expect(screen.getByText(/concluido/i)).toBeInTheDocument();
    expect(screen.getByText(/succeeded/i)).toBeInTheDocument();
    expect(screen.getByText(/previstos/i)).toBeInTheDocument();
    expect(screen.getByText(/inseridos/i)).toBeInTheDocument();
    expect(screen.getByText(/mantidos/i)).toBeInTheDocument();
    expect(screen.getByText(/removidos/i)).toBeInTheDocument();
  });

  it("oferece Repetir e agenda nova execução quando a situação é failed", async () => {
    // SPECSFY: US-003 FR-006 FR-005 AC-009 (SPEC-0013)
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response('{"execution_id":"exec-2"}', { status: 202 }));
    const user = userEvent.setup();
    render(
      <PainelProgresso
        papel="owner"
        execucao={execucao({ situacao: "failed", etapa: "embeddings", erro: "provider indisponível" })}
      />,
    );

    await user.click(screen.getByRole("button", { name: /repetir/i }));

    expect(fetchSpy).toHaveBeenCalled();
    expect(String(fetchSpy.mock.calls[0]?.[0])).toMatch(/\/retry$/);
  });

  it("sinaliza execução ativa e não agenda nova quando já há pending/running", async () => {
    // SPECSFY: US-003 FR-006 AC-010 (SPEC-0013)
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 202 }),
    );
    render(<PainelProgresso papel="owner" execucao={execucao({ situacao: "running" })} />);

    expect(screen.getByText(/execução ativa|já existe uma execução/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repetir/i })).toBeNull();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("não oferece Repetir para execução succeeded", () => {
    // SPECSFY: US-003 FR-006 AC-021 (SPEC-0013)
    render(<PainelProgresso papel="owner" execucao={execucao({ situacao: "succeeded", etapa: "concluido" })} />);

    expect(screen.queryByRole("button", { name: /repetir/i })).toBeNull();
  });
});
