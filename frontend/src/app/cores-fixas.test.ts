import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

import { describe, expect, it } from "vitest";

const RAIZ_SRC = join(__dirname, "..");

/** Exceções do AC-017: fundos de Dialog e Sheet e a página-modelo da rota raiz. */
const EXCECOES = new Set([
  "components/ui/dialog.tsx",
  "components/ui/sheet.tsx",
  "app/page.tsx",
]);

const PALETA =
  "white|black|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose";
const UTILITARIOS =
  "bg|text|border|ring|fill|stroke|from|to|via|outline|divide|shadow|decoration|accent|caret|placeholder";
const COR_FIXA = [
  /#[0-9a-fA-F]{3,8}\b/,
  /\b(?:rgb|rgba|hsl|hsla|oklch|oklab|lab|lch)\(/,
  new RegExp(`(?:^|[\\s"'\`:])(?:${UTILITARIOS})-(?:${PALETA})(?:-\\d{2,3})?(?:/\\d+)?(?=[\\s"'\`]|$)`),
];

function fontes(pasta: string): string[] {
  return readdirSync(pasta).flatMap((nome) => {
    const caminho = join(pasta, nome);
    if (statSync(caminho).isDirectory()) return nome === "test" ? [] : fontes(caminho);
    const ehFonte = /\.(ts|tsx)$/.test(nome) && !/\.test\.(ts|tsx)$/.test(nome);
    return ehFonte ? [caminho] : [];
  });
}

describe("cores fixas", () => {
  it("test_fontes_do_frontend_nao_usam_cores_fixas_fora_dos_tokens", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-017
    const achados: string[] = [];
    for (const arquivo of fontes(RAIZ_SRC)) {
      const id = relative(RAIZ_SRC, arquivo).replaceAll("\\", "/");
      if (EXCECOES.has(id)) continue;
      readFileSync(arquivo, "utf8")
        .split("\n")
        .forEach((linha, indice) => {
          if (COR_FIXA.some((padrao) => padrao.test(linha))) achados.push(`${id}:${indice + 1}: ${linha.trim()}`);
        });
    }

    expect(achados, `cores fixas fora dos tokens:\n${achados.join("\n")}`).toEqual([]);
  });

  it("test_excecoes_de_dialog_e_sheet_usam_a_variante_dark_no_fundo", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-017
    for (const id of ["components/ui/dialog.tsx", "components/ui/sheet.tsx"]) {
      const fonte = readFileSync(join(RAIZ_SRC, id), "utf8");
      expect(fonte, `${id} ainda não declara dark:bg-black/50`).toContain("dark:bg-black/50");
      expect(fonte).toContain("bg-black/10");
    }
  });

  it("test_detector_reconhece_cores_fixas_e_ignora_tokens_do_tema", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-017
    const proibidas = ['className="bg-white"', "text-red-500", 'style={{ color: "#fff" }}', "border-gray-200/50", "fill-[rgb(0,0,0)]"];
    const permitidas = [
      'className="bg-background text-foreground"',
      "border-border bg-card text-muted-foreground",
      "bg-primary/90 text-primary-foreground",
      "ring-ring/50 text-destructive",
    ];

    for (const linha of proibidas) expect(COR_FIXA.some((p) => p.test(linha)), linha).toBe(true);
    for (const linha of permitidas) expect(COR_FIXA.some((p) => p.test(linha)), linha).toBe(false);
  });
});
