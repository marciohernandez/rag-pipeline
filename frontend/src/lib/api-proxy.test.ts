/**
 * Guard do proxy de mesma origem (SPEC-0013).
 *
 * Regressão: até 2026-09-07 o frontend nunca rodou contra o backend real. Sem
 * o rewrite, o navegador faria a chamada cross-origin e ela morreria duas
 * vezes — o backend não tem `CORSMiddleware` (o preflight `OPTIONS` exigido
 * pelo cabeçalho `Authorization` responde 405) e a CSP de `next.config.ts` não
 * declara `connect-src`, caindo em `default-src 'self'`.
 */

import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import nextConfig from "../../next.config";
import pacote from "../../package.json";
import { exigir } from "@/test/carregar";
import { apiFetch } from "./api-client";

type RegraDeRewrite = { source: string; destination: string };

async function regras(): Promise<RegraDeRewrite[]> {
  const resultado = await nextConfig.rewrites!();
  return (Array.isArray(resultado) ? resultado : resultado.beforeFiles) as RegraDeRewrite[];
}

describe("proxy /api do Next", () => {
  it("reencaminha /api/* para o backend, mantendo tudo em mesma origem", async () => {
    const regra = (await regras()).find((item) => item.source.startsWith("/api"));

    expect(regra, "nenhum rewrite de /api encontrado em next.config.ts").toBeDefined();
    expect(regra!.source).toBe("/api/:path*");
    expect(regra!.destination).toMatch(/^https?:\/\/.+\/api\/:path\*$/);
  });

  it("a CSP não declara connect-src, então cross-origin depende do proxy", async () => {
    const cabecalhos = await nextConfig.headers!();
    const csp = cabecalhos
      .flatMap((entrada) => entrada.headers)
      .find((cabecalho) => cabecalho.key === "Content-Security-Policy");

    expect(csp).toBeDefined();
    expect(csp!.value).toContain("default-src 'self'");
    expect(csp!.value).not.toContain("connect-src");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("o cliente HTTP chama a URL relativa, para cair no proxy", async () => {
    const fetchSimulado = vi.fn().mockResolvedValue(new Response("[]", { status: 200 }));
    vi.stubGlobal("fetch", fetchSimulado);

    await apiFetch("/api/v1/bases");

    // Sem prefixo absoluto: a requisição sai para a própria origem do Next,
    // que a reencaminha. Um `NEXT_PUBLIC_API_BASE_URL` preenchido apontaria o
    // navegador para outra origem e reintroduziria a dependência de CORS.
    expect(fetchSimulado).toHaveBeenCalledOnce();
    expect(fetchSimulado.mock.calls[0][0]).toBe("/api/v1/bases");
  });

  it("test_csp_continua_permitindo_script_em_linha_e_nada_muda_fora_do_frontend", async () => {
    // SPECSFY: SPEC-0024 FR-002 FR-005 NFR-004 AC-014
    const { default: ScriptTema } = await exigir<{ default: ComponentType }>("@/features/tema/ScriptTema");
    const cabecalhos = await nextConfig.headers!();
    const csp = cabecalhos
      .flatMap((entrada) => entrada.headers)
      .find((cabecalho) => cabecalho.key === "Content-Security-Policy")!.value;
    const scriptSrc = /script-src([^;]*);/.exec(csp)![1];

    expect(scriptSrc).toContain("'self'");
    expect(scriptSrc).toContain("'unsafe-inline'");
    expect(scriptSrc).not.toContain("nonce-");
    expect(csp).not.toContain("connect-src");
    // O script do tema é em linha e da própria origem: nada a carregar por rede.
    const marcacao = renderToStaticMarkup(createElement(ScriptTema));
    expect(marcacao).toContain("<script");
    expect(marcacao).not.toMatch(/<script[^>]*\ssrc=/);
  });

  it("test_tema_nao_adiciona_dependencia_de_tema_ao_pacote_do_frontend", async () => {
    // SPECSFY: SPEC-0024 FR-002 FR-005 NFR-004 AC-014
    await exigir<{ default: ComponentType }>("@/features/tema/ScriptTema");
    const dependencias = Object.keys({ ...pacote.dependencies, ...pacote.devDependencies });

    expect(dependencias.filter((nome) => /theme|dark-mode|color-scheme/i.test(nome))).toEqual([]);
  });

  it("test_script_do_tema_nao_exige_unsafe_eval_fora_do_desenvolvimento", async () => {
    // SPECSFY: SPEC-0024 FR-005 NFR-004 AC-014
    const { default: ScriptTema } = await exigir<{ default: ComponentType }>("@/features/tema/ScriptTema");
    const marcacao = renderToStaticMarkup(createElement(ScriptTema));

    expect(marcacao).not.toMatch(/\beval\(|new Function\(/);
  });
});
