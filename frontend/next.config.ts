import type { NextConfig } from "next";

// DEC-004 (SPEC-0013): CSP básica sem nonce — script-src limitado à própria
// origem, mitigação mínima de XSS para a primeira superfície web deste
// repositório, que guarda um token de sessão em sessionStorage.
const isDev = process.env.NODE_ENV === "development";

const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""};
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`;

// O navegador só fala com a origem do Next: `/api/*` é reencaminhado no
// servidor para o backend FastAPI. Isso mantém tudo em mesma origem, o que
// (a) dispensa CORS no backend — sem CORSMiddleware, o preflight `OPTIONS`
// exigido pelo cabeçalho `Authorization` responde 405 — e (b) satisfaz a CSP
// abaixo, que não declara `connect-src` e portanto cai em `default-src 'self'`.
// `NEXT_PUBLIC_API_BASE_URL` continua vazio por padrão (URL relativa).
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",

  // O CLI do TypeScript 5.9 pode encerrar sem liberar a saída de
  // `--showConfig` quando o Next o captura no Node 24. A API instalada evita
  // essa limitação sem suprimir a checagem de tipos do build.
  experimental: {
    useTypeScriptCli: false,
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: cspHeader.replace(/\n/g, ""),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
