import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/font/google", () => ({
  Geist: () => ({ variable: "fonte-sans" }),
  Geist_Mono: () => ({ variable: "fonte-mono" }),
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}));

import RootLayout from "@/app/layout";
import LoginPage from "@/app/login/page";
import NovaSenhaPage from "@/app/nova-senha/page";
import { executarScript, extrairScript, instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

type Props = Parameters<typeof RootLayout>[0];

function paginaCompleta(pagina: React.ReactNode) {
  return renderToStaticMarkup(RootLayout({ children: pagina } as unknown as Props));
}

afterEach(limparAmbienteTema);

describe("telas de acesso", () => {
  it("test_login_e_nova_senha_seguem_o_tema_sem_controle", () => {
    // SPECSFY: SPEC-0024 US-002 FR-003 FR-006 AC-008
    for (const pagina of [<LoginPage key="login" />, <NovaSenhaPage key="nova-senha" />]) {
      document.documentElement.classList.remove("dark");
      instalarMatchMedia(true);
      const html = paginaCompleta(pagina);

      const codigo = extrairScript(html);
      expect(codigo, "a página não carrega o script de tema").not.toBeNull();
      executarScript(codigo as string);
      expect(document.documentElement).toHaveClass("dark");
      expect(html).not.toMatch(/menuitemradio|role="radio"|>Tema</);
      limparAmbienteTema();
    }
  });

  it("test_telas_de_acesso_no_computador_claro_ficam_no_tema_claro", () => {
    // SPECSFY: SPEC-0024 US-002 FR-003 FR-006 AC-008
    instalarMatchMedia(false);
    for (const pagina of [<LoginPage key="login" />, <NovaSenhaPage key="nova-senha" />]) {
      const codigo = extrairScript(paginaCompleta(pagina));
      expect(codigo, "a página não carrega o script de tema").not.toBeNull();
      executarScript(codigo as string);
      expect(document.documentElement).not.toHaveClass("dark");
    }
  });

  it("test_telas_de_acesso_respeitam_o_tema_salvo_mesmo_sem_sessao", () => {
    // SPECSFY: SPEC-0024 US-002 FR-003 FR-006 AC-008
    instalarMatchMedia(false);
    localStorage.setItem("rag-pipeline-tema", "escuro");
    sessionStorage.clear();

    const codigo = extrairScript(paginaCompleta(<LoginPage />));
    expect(codigo, "a página não carrega o script de tema").not.toBeNull();
    executarScript(codigo as string);
    expect(document.documentElement).toHaveClass("dark");
  });
});
