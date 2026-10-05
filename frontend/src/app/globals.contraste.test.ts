import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(join(__dirname, "globals.css"), "utf8");

type Cor = { r: number; g: number; b: number; alfa: number };

/** Lê os tokens de um bloco (`:root` ou `.dark`) em um mapa nome → valor. */
function tokens(seletor: string): Record<string, string> {
  const achado = new RegExp(`(?:^|\\n)${seletor}\\s*\\{([^}]*)\\}`).exec(css);
  expect(achado, `bloco ${seletor} não encontrado em globals.css`).not.toBeNull();
  const mapa: Record<string, string> = {};
  for (const [, nome, valor] of achado![1].matchAll(/--([\w-]+):\s*([^;]+);/g)) mapa[nome] = valor.trim();
  return mapa;
}

const codificar = (linear: number) =>
  linear <= 0.0031308 ? 12.92 * linear : 1.055 * Math.pow(linear, 1 / 2.4) - 0.055;
const decodificar = (canal: number) =>
  canal <= 0.04045 ? canal / 12.92 : Math.pow((canal + 0.055) / 1.055, 2.4);
const limitar = (valor: number) => Math.min(1, Math.max(0, valor));

/** oklch(L C h / alfa) → sRGB codificado (0–1) mais alfa. */
function lerOklch(valor: string): Cor {
  const achado = /^oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+)(%?))?\s*\)$/.exec(valor);
  expect(achado, `valor de cor não suportado: ${valor}`).not.toBeNull();
  const [, l, c, h, alfa, porcentagem] = achado!;
  const L = Number(l);
  const a = Number(c) * Math.cos((Number(h) * Math.PI) / 180);
  const b = Number(c) * Math.sin((Number(h) * Math.PI) / 180);
  const l_ = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3);
  const m_ = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3);
  const s_ = Math.pow(L - 0.0894841775 * a - 1.291485548 * b, 3);
  const linear = [
    4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
    -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
    -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
  ].map((canal) => codificar(limitar(canal)));
  const opacidade = alfa === undefined ? 1 : Number(alfa) / (porcentagem ? 100 : 1);
  return { r: linear[0], g: linear[1], b: linear[2], alfa: opacidade };
}

/** Composição sobre um fundo opaco, como o navegador faz em sRGB codificado. */
function sobre(frente: Cor, fundo: Cor): Cor {
  const misturar = (f: number, g: number) => f * frente.alfa + g * (1 - frente.alfa);
  return { r: misturar(frente.r, fundo.r), g: misturar(frente.g, fundo.g), b: misturar(frente.b, fundo.b), alfa: 1 };
}

function luminancia(cor: Cor): number {
  return 0.2126 * decodificar(cor.r) + 0.7152 * decodificar(cor.g) + 0.0722 * decodificar(cor.b);
}

function contraste(frente: Cor, fundo: Cor): number {
  const a = luminancia(sobre(frente, fundo));
  const b = luminancia(fundo);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

const PARES_DE_TEXTO: Array<[string, string]> = [
  ["foreground", "background"],
  ["card-foreground", "card"],
  ["popover-foreground", "popover"],
  ["primary-foreground", "primary"],
  ["secondary-foreground", "secondary"],
  ["muted-foreground", "muted"],
  ["muted-foreground", "background"],
  ["accent-foreground", "accent"],
  ["destructive", "background"],
  ["destructive", "card"],
  ["sidebar-foreground", "sidebar"],
  ["sidebar-primary-foreground", "sidebar-primary"],
  ["sidebar-accent-foreground", "sidebar-accent"],
];

const TEMAS = [
  { nome: "claro", seletor: ":root" },
  { nome: "escuro", seletor: "\\.dark" },
];

describe("contraste dos tokens", () => {
  it("test_pares_de_texto_dos_tokens_atendem_contraste_aa_nos_dois_temas", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-010
    const falhas: string[] = [];
    for (const { nome, seletor } of TEMAS) {
      const mapa = tokens(seletor);
      const fundoDaPagina = lerOklch(mapa.background);
      for (const [texto, fundo] of PARES_DE_TEXTO) {
        const razao = contraste(lerOklch(mapa[texto]), sobre(lerOklch(mapa[fundo]), fundoDaPagina));
        if (razao < 4.5) falhas.push(`${nome}: ${texto} sobre ${fundo} = ${razao.toFixed(2)}:1 (mínimo 4,5:1)`);
      }
    }

    expect(falhas, falhas.join("\n")).toEqual([]);
  });

  it("test_anel_de_foco_e_borda_de_campo_atendem_3_para_1_sobre_o_fundo_nos_dois_temas", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-010
    const falhas: string[] = [];
    for (const { nome, seletor } of TEMAS) {
      const mapa = tokens(seletor);
      const fundoDaPagina = lerOklch(mapa.background);
      for (const token of ["ring", "input"]) {
        const razao = contraste(lerOklch(mapa[token]), fundoDaPagina);
        if (razao < 3) falhas.push(`${nome}: ${token} sobre background = ${razao.toFixed(2)}:1 (mínimo 3:1)`);
      }
    }

    expect(falhas, falhas.join("\n")).toEqual([]);
  });

  it("test_calculo_de_contraste_reproduz_referencias_conhecidas", () => {
    // SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-010
    const branco = lerOklch("oklch(1 0 0)");
    const preto = lerOklch("oklch(0 0 0)");

    expect(contraste(preto, branco)).toBeCloseTo(21, 0);
    expect(contraste(branco, branco)).toBeCloseTo(1, 5);
    // Branco a 15% sobre preto compõe um cinza escuro, bem abaixo de 3:1.
    expect(contraste(lerOklch("oklch(1 0 0 / 15%)"), preto)).toBeLessThan(3);
    expect(Object.keys(tokens(":root"))).toEqual(expect.arrayContaining(["background", "ring", "input"]));
    expect(Object.keys(tokens("\\.dark"))).toEqual(expect.arrayContaining(["background", "ring", "input"]));
  });
});
