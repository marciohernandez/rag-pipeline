/**
 * Guard do proxy de mesma origem (SPEC-0013).
 *
 * Regressão: até 2026-09-07 o frontend nunca rodou contra o backend real. Sem
 * o rewrite, o navegador faria a chamada cross-origin e ela morreria duas
 * vezes — o backend não tem `CORSMiddleware` (o preflight `OPTIONS` exigido
 * pelo cabeçalho `Authorization` responde 405) e a CSP de `next.config.ts` não
 * declara `connect-src`, caindo em `default-src 'self'`.
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import nextConfig from "../../next.config";
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
});
