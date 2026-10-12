import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import EtapaArquivos from "@/features/ingestao/EtapaArquivos";

const md = (nome: string, tamanho = 10) => new File(["x".repeat(tamanho)], nome, { type: "text/markdown" });
const props = () => ({ arquivos: [] as File[], usarPreparada: false, onAdicionar: vi.fn(), onRemover: vi.fn(), onPreparada: vi.fn() });

afterEach(cleanup);

describe("EtapaArquivos", () => {
  it("adiciona arquivos .md válidos e lista os selecionados com remoção", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-013 FR-014 NFR-004 AC-015 AC-016
    const p = props();
    const user = userEvent.setup();
    const { rerender } = render(<EtapaArquivos {...p} />);

    await user.upload(screen.getByLabelText(/arquivos markdown/i), [md("a.md"), md("b.md")]);
    expect(p.onAdicionar).toHaveBeenCalledTimes(1);
    expect(p.onAdicionar.mock.calls[0][0]).toHaveLength(2);

    rerender(<EtapaArquivos {...p} arquivos={[md("a.md")]} />);
    await user.click(screen.getByRole("button", { name: /remover a\.md/i }));
    expect(p.onRemover).toHaveBeenCalledWith("a.md");
  });

  it("recusa extensão inválida e arquivo acima de 5 MB sem adicionar nada", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-013 FR-014 NFR-004 AC-015 AC-016
    const p = props();
    const user = userEvent.setup({ applyAccept: false });
    render(<EtapaArquivos {...p} />);

    await user.upload(screen.getByLabelText(/arquivos markdown/i), [new File(["x"], "nota.txt")]);
    expect(await screen.findByText(/extensão inválida/i)).toBeInTheDocument();
    await user.upload(screen.getByLabelText(/arquivos markdown/i), [md("grande.md", 5 * 1024 * 1024 + 1)]);
    expect(await screen.findByText(/excede o limite de 5 MB/i)).toBeInTheDocument();
    expect(p.onAdicionar).not.toHaveBeenCalled();
  });

  it("com a base preparada some o envio de arquivos", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-013 FR-014 NFR-004 AC-015 AC-016
    const p = props();
    const user = userEvent.setup();
    const { rerender } = render(<EtapaArquivos {...p} />);

    await user.click(screen.getByRole("checkbox", { name: /usar base preparada/i }));
    expect(p.onPreparada).toHaveBeenCalledWith(true);
    rerender(<EtapaArquivos {...p} usarPreparada />);
    expect(screen.queryByLabelText(/arquivos markdown/i)).not.toBeInTheDocument();
    expect(screen.getByText(/base preparada de demonstração/i)).toBeInTheDocument();
  });
});
