import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";

afterEach(cleanup);

function classesDoFundo(slot: string): string[] {
  const fundo = document.querySelector(`[data-slot="${slot}"]`);
  expect(fundo, `fundo ${slot} não foi renderizado`).not.toBeNull();
  return (fundo as Element).className.split(/\s+/);
}

describe("fundos de Dialog e Sheet", () => {
  it("test_backdrops_de_dialog_e_sheet_usam_opacidade_minima_no_escuro", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-011
    render(
      <Dialog open>
        <DialogContent>
          <DialogTitle>Título</DialogTitle>
          <DialogDescription>Descrição</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    expect(classesDoFundo("dialog-overlay")).toContain("dark:bg-black/50");
    cleanup();

    render(
      <Sheet open>
        <SheetContent>
          <SheetTitle>Título</SheetTitle>
          <SheetDescription>Descrição</SheetDescription>
        </SheetContent>
      </Sheet>,
    );
    expect(classesDoFundo("sheet-overlay")).toContain("dark:bg-black/50");
  });

  it("test_tema_claro_mantem_o_fundo_com_10_por_cento", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-011
    render(
      <Dialog open>
        <DialogContent>
          <DialogTitle>Título</DialogTitle>
          <DialogDescription>Descrição</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    expect(classesDoFundo("dialog-overlay")).toContain("bg-black/10");
    cleanup();

    render(
      <Sheet open>
        <SheetContent>
          <SheetTitle>Título</SheetTitle>
          <SheetDescription>Descrição</SheetDescription>
        </SheetContent>
      </Sheet>,
    );
    expect(classesDoFundo("sheet-overlay")).toContain("bg-black/10");
  });

  it("test_conteudo_do_dialogo_e_do_painel_continua_nos_tokens_do_tema", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-011
    render(
      <Dialog open>
        <DialogContent>
          <DialogTitle>Título</DialogTitle>
          <DialogDescription>Descrição</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    const dialogo = document.querySelector('[data-slot="dialog-content"]') as Element;
    expect(dialogo.className).toContain("bg-popover");
    expect(dialogo.className).toContain("text-popover-foreground");
    expect(classesDoFundo("dialog-overlay")).toContain("dark:bg-black/50");
  });
});
