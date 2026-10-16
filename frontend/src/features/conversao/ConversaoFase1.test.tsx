import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { exigir } from "@/test/carregar";

type PropsAbas = { abas: string[]; onConfirmar: (abas: string[]) => void };
type PropsEnderecos = { onAdicionar: (url: string) => void };

afterEach(cleanup);

describe("Seleção de abas da planilha (SPEC-0036)", () => {
  it(
    // SPECSFY: SPEC-0036 US-003 FR-005 NFR-004 AC-015
    "desabilita Confirmar quando nenhuma aba está marcada e anuncia o motivo",
    async () => {
      const { default: SelecaoAbas } = await exigir<{ default: ComponentType<PropsAbas> }>(
        "@/features/conversao/SelecaoAbas",
      );
      const aoConfirmar = vi.fn();
      const usuario = userEvent.setup();
      render(<SelecaoAbas abas={["Preços", "Rascunho"]} onConfirmar={aoConfirmar} />);

      const caixas = screen.getAllByRole("checkbox");
      expect(caixas).toHaveLength(2);
      caixas.forEach((c) => expect(c).toBeChecked());

      await usuario.click(screen.getByRole("checkbox", { name: "Preços" }));
      await usuario.click(screen.getByRole("checkbox", { name: "Rascunho" }));

      expect(screen.getByRole("button", { name: /confirmar/i })).toBeDisabled();
      expect(screen.getByRole("alert")).toHaveTextContent(/ao menos uma aba/i);
      expect(aoConfirmar).not.toHaveBeenCalled();
    },
  );
});

describe("Entrada de endereços (SPEC-0036)", () => {
  it(
    // SPECSFY: SPEC-0036 NFR-004 US-001 FR-002 AC-029
    "opera por teclado e anuncia o erro de endereço interno ligado ao campo",
    async () => {
      const { default: EntradaEnderecos } = await exigir<{
        default: ComponentType<PropsEnderecos>;
      }>("@/features/conversao/EntradaEnderecos");
      const aoAdicionar = vi.fn();
      const usuario = userEvent.setup();
      render(<EntradaEnderecos onAdicionar={aoAdicionar} />);

      await usuario.tab();
      const campo = screen.getByRole("textbox", { name: /endereço/i });
      expect(campo).toHaveFocus();
      await usuario.keyboard("http://localhost:8000/admin");
      await usuario.tab();
      expect(screen.getByRole("button", { name: /adicionar/i })).toHaveFocus();
      await usuario.keyboard("{Enter}");

      const alerta = screen.getByRole("alert");
      expect(alerta).toHaveTextContent(/endereço/i);
      expect(campo).toHaveAccessibleDescription(alerta.textContent ?? "");
      expect(aoAdicionar).not.toHaveBeenCalled();
    },
  );
});
